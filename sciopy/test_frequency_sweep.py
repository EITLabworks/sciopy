from unittest.mock import Mock

import numpy as np
import pytest

from sciopy.com_util import clTbt_sp, clTbt_u16
from sciopy.EIT_16_32_64_128 import EIT_16_32_64_128
from sciopy.sciopy_dataclasses import EITFrame, EitMeasurementSetup
from sciopy.usb_message_parser import MessageParser, get_data_as_matrix


def test_update_excitation_frequencies_builds_valid_sweep_command():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    device.update_ExcitationFrequencies(f_min=1_000.0, f_max=100_000.0, f_count=5, f_scale="log")

    expected = bytearray(
        [0xB0, 12, 4]
        + clTbt_sp(1_000.0)
        + clTbt_sp(100_000.0)
        + clTbt_u16(5)
        + [0x01, 0xB0]
    )
    device.write_command_string.assert_called_once_with(expected)


def test_update_excitation_frequency_stays_backward_compatible():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    device.update_ExcitationFrequency(50_000)

    expected = bytearray(
        [0xB0, 12, 4] + clTbt_sp(50_000) + clTbt_sp(50_000) + [0, 1] + [0x00, 0xB0]
    )
    device.write_command_string.assert_called_once_with(expected)


def test_update_excitation_frequencies_rejects_invalid_sweep():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    with pytest.raises(ValueError):
        device.update_ExcitationFrequencies(f_min=1_000.0, f_max=1_000.0, f_count=3)

    with pytest.raises(ValueError):
        device.update_ExcitationFrequencies(f_min=1_000.0, f_scale="bogus")


def test_set_measurement_setup_uses_excitation_frequencies_sweep(monkeypatch):
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.write_command_string = Mock()
    device.send_message = Mock()

    setup = EitMeasurementSetup(
        burst_count=1,
        n_el=16,
        exc_freq=1_000.0,
        framerate=10,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
        exc_freq_max=10_000.0,
        n_freq=3,
        freq_scale="lin",
    )
    device.SetMeasurementSetup(setup)

    expected = bytearray(
        [0xB0, 12, 4]
        + clTbt_sp(1_000.0)
        + clTbt_sp(10_000.0)
        + clTbt_u16(3)
        + [0x00, 0xB0]
    )
    assert expected in [call.args[0] for call in device.write_command_string.call_args_list]


def test_start_stop_measurement_can_configure_sweep_inline():
    device = EIT_16_32_64_128(16)
    device.setup = EitMeasurementSetup(
        burst_count=1,
        n_el=16,
        exc_freq=1_000.0,
        framerate=10,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
    )
    device.cMessageParser = Mock()
    device.cMessageParser.read_usb_till_timeout.return_value = []
    device.write_command_string = Mock()
    device.send_message = Mock()

    device.StartStopMeasurement(f_min=1_000.0, f_max=10_000.0, f_count=4, f_scale="log")

    expected = bytearray(
        [0xB0, 12, 4]
        + clTbt_sp(1_000.0)
        + clTbt_sp(10_000.0)
        + clTbt_u16(4)
        + [0x01, 0xB0]
    )
    device.write_command_string.assert_called_once_with(expected)
    assert device.setup.n_freq == 4


def test_message_parser_sizes_frame_for_frequency_sweep():
    setup = EitMeasurementSetup(
        burst_count=1,
        n_el=16,
        exc_freq=1_000.0,
        framerate=10,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
        exc_freq_max=10_000.0,
        n_freq=3,
        freq_scale="lin",
    )
    parser = MessageParser(device=None, eitsetup=setup, devicetype="FS")

    assert parser.iNumFreqSettings == 3
    assert len(parser.CurrentFrame.ppcData) == (
        parser.iMaxChannelGroups * 16 * parser.iNumExcitationSettings * 3
    )
    np.testing.assert_allclose(parser.CurrentFrame.frequency_stgs, [1_000.0, 5_500.0, 10_000.0])


def test_message_parser_defaults_to_single_frequency():
    setup = EitMeasurementSetup(
        burst_count=1,
        n_el=16,
        exc_freq=1_000.0,
        framerate=10,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
    )
    parser = MessageParser(device=None, eitsetup=setup, devicetype="FS")

    assert parser.iNumFreqSettings == 1
    np.testing.assert_allclose(parser.CurrentFrame.frequency_stgs, [1_000.0])


def test_get_data_as_matrix_keeps_old_shape_for_single_frequency():
    n_exc, n_el = 16, 16
    frame = EITFrame(
        n_el=16,
        excitation_stgs=np.zeros((n_exc, 2), dtype=int),
        frequency_stgs=np.array([1_000.0]),
        timestamp1=0,
        timestamp2=0,
        timestamp_pc=0,
        ppcData=np.arange(n_exc * n_el, dtype=complex),
    )

    matrix = get_data_as_matrix([frame])

    assert matrix.shape == (1, n_exc, n_el)


def test_get_data_as_matrix_adds_frequency_axis_for_sweep():
    n_exc, n_freq, n_el = 16, 3, 16
    frame = EITFrame(
        n_el=16,
        excitation_stgs=np.zeros((n_exc, 2), dtype=int),
        frequency_stgs=np.array([1_000.0, 5_500.0, 10_000.0]),
        timestamp1=0,
        timestamp2=0,
        timestamp_pc=0,
        ppcData=np.arange(n_exc * n_freq * n_el, dtype=complex),
    )

    matrix = get_data_as_matrix([frame])

    assert matrix.shape == (1, n_exc, n_freq, n_el)
    # excitation outer, frequency middle, channel inner (see EITFrame docstring)
    assert matrix[0, 0, 0, 0] == 0
    assert matrix[0, 0, 1, 0] == n_el
    assert matrix[0, 1, 0, 0] == n_freq * n_el
