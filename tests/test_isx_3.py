from unittest.mock import Mock
import struct

import numpy as np

from sciopy.ISX_3 import ISXMeasurement, ISX_3
from sciopy.sciopy_dataclasses import EisMeasurementSetup


def command_device():
    device = ISX_3()
    device.send_command = Mock(return_value=[])
    return device


def test_frame_builder_uses_sciospec_framing():
    assert ISX_3.build_frame(0xB0, [0x02, 0x01, 0x00, 0x01]) == bytearray(
        [0xB0, 0x04, 0x02, 0x01, 0x00, 0x01, 0xB0]
    )


def test_stream_parser_handles_partial_and_multiple_frames():
    device = ISX_3()
    first = bytes([0x18, 0x01, 0x83, 0x18])
    second = bytes([0xBA, 0x04, 0x00, 0x00, 0x03, 0xE8, 0xBA])

    assert device.parse_received_bytes(first[:2]) == []
    assert device.parse_received_bytes(first[2:] + second) == [
        list(first),
        list(second),
    ]


def test_set_and_get_frontend_settings_follow_manual():
    device = command_device()

    device.SetFE_Settings("4-point", "bnc", "auto", "1v")
    device.GetFE_Settings()

    assert device.send_command.call_args_list == [
        ((0xB0, [0x02, 0x01, 0x00, 0x01]),),
        ((0xB1,),),
    ]
    assert device.decode_frame([0xB1, 0x04, 0x02, 0x01, 0x04, 0x02, 0xB1]) == {
        "measurement_mode": 0x02,
        "measurement_channel": 0x01,
        "current_range": 0x04,
        "voltage_range": 0x02,
    }


def test_options_update_measurement_layout_state():
    device = command_device()

    device.SetOptions("timestamp_us", True)
    device.SetOptions("current_range", True)

    assert device.timestamp_mode == "us"
    assert device.current_range_output is True
    assert device.send_command.call_args_list == [
        ((0x97, [0x02, 0x01]),),
        ((0x97, [0x04, 0x01]),),
    ]


def test_add_frequency_point_encodes_float_and_extended_options():
    device = command_device()

    device.AddFrequencyPoint(
        32_000,
        1.0,
        0.25,
        point_delay=1000,
        phase_sync=True,
        excitation_type="voltage",
    )

    payload = device.send_command.call_args.args[1]
    assert device.send_command.call_args.args[0] == 0xB6
    assert payload[0] == 0x02
    assert struct.unpack(">fff", payload[1:13]) == (32_000.0, 1.0, 0.25)
    assert payload[13:] == bytearray(
        [0x01, 0x00, 0x00, 0x03, 0xE8, 0x02, 0, 0, 0, 1, 0x03, 0, 0, 0, 1]
    )


def test_add_frequency_list_encodes_documented_setup():
    device = command_device()

    device.AddFrequencyList(1_000, 10_000, 10, "log", 1.0, 0.25)

    tag, payload = device.send_command.call_args.args
    assert tag == 0xB6
    assert payload[0] == 0x03
    assert struct.unpack(">fff", payload[1:13]) == (1_000.0, 10_000.0, 10.0)
    assert payload[13] == 0x01
    assert struct.unpack(">ff", payload[14:22]) == (1.0, 0.25)


def test_eis_dataclass_configures_setup():
    device = command_device()
    setup = EisMeasurementSetup(
        start=100,
        stop=100_000,
        step=20,
        stepmode="log",
        avg=1,
        amplitude=0.1,
        precision=1,
        measurement_time=0,
    )

    device.SetMeasurementSetup(setup)

    assert device.setup is setup
    assert device.send_command.call_args_list[0] == ((0xB6, [0x01]),)
    assert device.send_command.call_args_list[1].args[0] == 0xB6


def test_measurement_without_optional_fields_is_decoded():
    device = ISX_3()
    payload = [0x00, 0x02, *struct.pack(">ff", 123.5, -4.25)]

    result = device.decode_frame([0xB8, len(payload), *payload, 0xB8])

    assert result == ISXMeasurement(frequency_id=2, impedance=123.5 - 4.25j)


def test_measurement_with_microsecond_timestamp_and_range_is_decoded():
    device = ISX_3()
    device.timestamp_mode = "us"
    device.current_range_output = True
    payload = [0x00, 0x03, 0, 0, 0, 1, 2, 0x04, *struct.pack(">ff", 10, 2)]

    result = device.decode_frame([0xB8, len(payload), *payload, 0xB8])

    assert result == ISXMeasurement(
        frequency_id=3,
        impedance=10 + 2j,
        timestamp=258,
        timestamp_unit="us",
        current_range=0x04,
    )


def test_setup_response_decoders():
    device = ISX_3()
    frequencies = struct.pack(">ff", 100.0, 1_000.0)

    assert device.decode_frame([0xB7, 0x03, 0x01, 0x00, 0x10, 0xB7]) == {
        "frequency_count": 16
    }
    result = device.decode_frame([0xB7, 0x09, 0x04, *frequencies, 0xB7])
    assert np.allclose(result["frequencies_hz"], [100, 1_000])


def test_frequency_point_response_decodes_extended_options():
    device = ISX_3()
    data = [
        0x02,
        *struct.pack(">fff", 32_000, 1.0, 0.25),
        0x01,
        0,
        0,
        3,
        0xE8,
        0x03,
        0,
        0,
        0,
        1,
    ]

    result = device.decode_frame([0xB7, len(data), *data, 0xB7])

    assert result == {
        "frequency_hz": 32_000.0,
        "precision": 1.0,
        "amplitude": 0.25,
        "point_delay_us": 1_000,
        "excitation_type": 1,
    }


def test_compensation_record_encodes_three_complex_values():
    device = command_device()

    device.SetCompensationData(2, 3, 1 + 2j, 3 + 4j, 5 + 6j)

    tag, payload = device.send_command.call_args.args
    assert tag == 0xB6
    assert payload[:5] == bytearray([0x17, 0x02, 0x02, 0x00, 0x03])
    assert struct.unpack(">ffffff", payload[5:]) == (1, 2, 3, 4, 5, 6)


def test_sync_ethernet_and_watchdog_commands():
    device = command_device()

    device.SetSyncTime(1_000)
    device.SetEthernetConfiguration(ip_address="192.168.1.25")
    device.SetEthernetConfiguration(dhcp=True)
    device.GetEthernetConfiguration("mac_address")
    device.SetTCPWatchdog(60)

    assert device.send_command.call_args_list == [
        ((0xB9, bytes([0, 0, 3, 0xE8])),),
        ((0xBD, [0x01, 192, 168, 1, 25]),),
        ((0xBD, [0x03, 1]),),
        ((0xBE, [0x02]),),
        ((0xCF, [0x00, 0, 0, 0, 60]),),
    ]


def test_firmware_and_device_information_are_decoded():
    device = ISX_3()

    arm = device.decode_frame([0xD0, 0x06, 1, 2, 0, 3, 0, 4, 0xD0])
    identity = device.decode_frame([0xD1, 0x07, 1, 0, 7, 0x12, 0x34, 14, 9, 0xD1])

    assert arm == {"developer_information": "0102", "revision": 3, "build": 4}
    assert identity == {
        "information_version": 1,
        "device_identifier": 7,
        "serial_number": 0x1234,
        "delivery_year": 2024,
        "delivery_month": 9,
        "developer_information": "",
    }


def test_invalid_protocol_values_are_rejected():
    device = command_device()

    for action in (
        lambda: device.SetFE_Settings("invalid", "bnc", "auto"),
        lambda: device.SetSyncTime(180_000_001),
        lambda: device.SetTCPWatchdog(0),
        lambda: device.SetDCBiasValue(1.1),
    ):
        try:
            action()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid protocol value was accepted")
