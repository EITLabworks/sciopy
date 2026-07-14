from unittest.mock import Mock

from sciopy.EIT_16_32_64_128 import EIT_16_32_64_128


def test_system_message_callback_uses_configured_message_parser():
    device = EIT_16_32_64_128(16)
    device.print_msg = True
    device.cMessageParser = Mock()
    device.cMessageParser.read_usb_till_timeout.return_value = []

    result = device.SystemMessageCallback()

    assert result == []
    assert device.cMessageParser.bPrintMessages is True
    device.cMessageParser.read_usb_till_timeout.assert_called_once_with(
        bSaveData=False,
        bDeleteDataFrame=True,
        bStartReset=False,
    )


def test_get_device_info_does_not_require_measurement_setup():
    device = EIT_16_32_64_128(16)
    device.serial_protocol = "HS"
    device.device = Mock()
    device.cMessageParser = Mock()

    device.GetDeviceInfo()

    device.device.write_data.assert_called_once_with(bytearray([0xD1, 0x00, 0xD1]))
    device.cMessageParser.read_usb_till_timeout.assert_called_once_with(
        bSaveData=False,
        bDeleteDataFrame=True,
        bStartReset=False,
    )


def test_read_message_uses_parser_transport_without_recursion():
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()
    device.cMessageParser.device_read.return_value = bytearray([0x18, 0x01, 0x83, 0x18])

    assert device.read_message() == bytearray([0x18, 0x01, 0x83, 0x18])
    device.cMessageParser.device_read.assert_called_once_with()


def test_update_measurement_mode_builds_valid_command():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    device.update_measurement_mode("skip4", "external")

    device.write_command_string.assert_called_once_with(
        bytearray([0xB0, 0x03, 0x08, 0x04, 0x02, 0xB0])
    )


def test_get_measurement_setup_builds_valid_command():
    device = EIT_16_32_64_128(16)
    device.write_command_string = Mock()

    device.GetMeasurementSetup(0x02)

    device.write_command_string.assert_called_once_with(
        bytearray([0xB1, 0x01, 0x02, 0xB1])
    )


def test_measurement_requires_setup_before_parser_reset():
    device = EIT_16_32_64_128(16)
    device.cMessageParser = Mock()

    try:
        device.StartStopMeasurement()
    except RuntimeError as error:
        assert str(error) == "SetMeasurementSetup must be called before measuring."
    else:
        raise AssertionError("StartStopMeasurement accepted a missing setup")
