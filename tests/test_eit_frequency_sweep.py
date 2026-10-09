import struct
from unittest.mock import Mock, call

import pytest

from sciopy.EIT_16_32_64_128 import (
    EIT_16_32_64_128,
)
from sciopy.sciopy_dataclasses import (
    EitFrequencyBlock,
    EitMeasurementSetup,
)


def build_frequency_command(
    f_min,
    f_max,
    f_count,
    f_type,
):
    command = bytearray([0xB0, 0x0C, 0x04])
    command.extend(struct.pack(">f", f_min))
    command.extend(struct.pack(">f", f_max))
    command.extend(
        f_count.to_bytes(
            2,
            byteorder="big",
            signed=False,
        )
    )
    command.extend([f_type, 0xB0])
    return command


def test_scalar_frequency_remains_supported():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    device.update_ExcitationFrequency(100000)

    expected = build_frequency_command(
        100000,
        100000,
        1,
        0,
    )

    device.write_command_string.assert_called_once_with(expected)


def test_linear_and_logarithmic_blocks():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=10,
            f_type="lin",
        ),
        EitFrequencyBlock(
            f_min=10000,
            f_max=100000,
            f_count=20,
            f_type="log",
        ),
    ]

    device.update_ExcitationFrequency(blocks)

    expected_linear = build_frequency_command(
        1000,
        10000,
        10,
        0,
    )
    expected_logarithmic = build_frequency_command(
        10000,
        100000,
        20,
        1,
    )

    assert device.write_command_string.call_count == 2
    device.write_command_string.assert_has_calls(
        [
            call(expected_linear),
            call(expected_logarithmic),
        ]
    )


def test_invalid_frequency_type_is_rejected():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=10,
            f_type="invalid",
        )
    ]

    with pytest.raises(
        ValueError,
        match="f_type",
    ):
        device.update_ExcitationFrequency(blocks)

    device.write_command_string.assert_not_called()


def test_frequency_count_must_fit_wire_format():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=64,
            f_type="lin",
        ),
        EitFrequencyBlock(
            f_min=10000,
            f_max=100000,
            f_count=65536,
            f_type="log",
        ),
    ]

    with pytest.raises(
        ValueError,
        match="unsigned 16-bit",
    ):
        device.update_ExcitationFrequency(blocks)

    device.write_command_string.assert_not_called()


def test_set_measurement_setup_forwards_frequency_blocks():
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.write_command_string = Mock()
    device.update_measurement_mode = Mock()
    device.update_ExcitationFrequency = Mock()

    blocks = [
        EitFrequencyBlock(
            f_min=1000,
            f_max=10000,
            f_count=10,
            f_type="lin",
        ),
        EitFrequencyBlock(
            f_min=10000,
            f_max=100000,
            f_count=20,
            f_type="log",
        ),
    ]

    setup = EitMeasurementSetup(
        burst_count=2,
        n_el=16,
        exc_freq=blocks,
        framerate=2,
        amplitude=0.001,
        inj_skip=0,
        gain=1,
        adc_range=1,
    )

    device.SetMeasurementSetup(setup)

    device.update_ExcitationFrequency.assert_called_once_with(blocks)


@pytest.mark.parametrize("skips", [[], [True], [-1], [15], [0, 0]])
def test_invalid_injection_skips_send_no_commands(skips):
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.write_command_string = Mock()
    setup = EitMeasurementSetup(1, 16, 1000, 2, 0.001, skips, 1, 1)
    with pytest.raises((ValueError, TypeError)):
        device.SetMeasurementSetup(setup)
    device.write_command_string.assert_not_called()
    device.cMessageParser.set_measurement_setup.assert_not_called()


def test_multiple_skip_patterns_send_all_injection_pairs():
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.write_command_string = Mock()
    setup = EitMeasurementSetup(1, 16, 1000, 2, 0.001, [0, 2], 1, 1)
    device.SetMeasurementSetup(setup)
    pairs = [
        list(item.args[0])
        for item in device.write_command_string.call_args_list
        if item.args[0][:3] == bytearray([0xB0, 3, 6])
    ]
    expected = [
        [0xB0, 3, 6, out, ((out + skip) % 16) + 1, 0xB0]
        for skip in (0, 2)
        for out in range(1, 17)
    ]
    assert pairs == expected


def test_direct_block_update_synchronizes_parser():
    from sciopy.usb_message_parser import MessageParser

    device = EIT_16_32_64_128(16)
    device.setup = EitMeasurementSetup(1, 16, 1000, 2, 0.001, 0, 1, 1)
    device.cMessageParser = MessageParser(None, device.setup)
    device.write_command_string = Mock()
    device.update_ExcitationFrequency([EitFrequencyBlock(1000, 10000, 3)])
    assert device.cMessageParser.iNumFreqSettings == 3
    assert len(device.cMessageParser.CurrentFrame.ppcData) == 16 * 3 * 16


@pytest.mark.parametrize("value", [float("nan"), float("inf"), 0, -1, True])
def test_invalid_frequency_endpoints_send_no_commands(value):
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()
    with pytest.raises((ValueError, TypeError)):
        device.update_ExcitationFrequency(value)
    device.write_command_string.assert_not_called()


def test_mixed_legacy_and_block_configuration_rejected_before_writes():
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.write_command_string = Mock()
    setup = EitMeasurementSetup(
        1, 16, [EitFrequencyBlock(1000, 2000, 2)], 2, 0.001, 0, 1, 1, n_freq=2
    )
    with pytest.raises(ValueError, match="legacy"):
        device.SetMeasurementSetup(setup)
    device.write_command_string.assert_not_called()
