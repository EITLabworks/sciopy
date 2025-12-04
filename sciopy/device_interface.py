"""
Project ：sciopy
Directory: sciopy/sciopy
File : device_interface.py
Author ：Patricia Fuchs
Date ：26.11.2025 14:04
"""

try:
    import serial
except ImportError:
    print("Could not import module: serial")

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #


class DeviceInterface:
    def __init__(self):
        self.sProtocol = "None"

    def send_data(self, data):
        pass

    def read_data(self):
        return None


import serial


class USB_FS_Device(DeviceInterface):
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 9000):
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


class USB_HS_Device(DeviceInterface):
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 9000):
        super().__init__()
