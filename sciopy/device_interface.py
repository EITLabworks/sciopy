"""
Project ：sciopy
Directory: sciopy/sciopy
File : device_interface.py
Author ：Patricia Fuchs
Date ：26.11.2025 14:04
"""

import serial

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #


class DeviceInterface:
    def __init__(self):
        self.sProtocol = "None"

    def send_data(self, data):
        raise NotImplementedError

    def read_data(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class USB_FS_Device(DeviceInterface):
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1):
        super().__init__()
        self.sProtocol = "FS"
        self.device = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )
        self.name = self.device.name

    def send_data(self, data):
        self.device.write(data)

    def read_data(self):
        return self.device.read()

    def close(self):
        self.device.close()


class USB_HS_Device(DeviceInterface):
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 9000):
        super().__init__()
        raise NotImplementedError(
            "USB_HS_Device is not implemented; use EIT_16_32_64_128.connect_device_HS()."
        )
