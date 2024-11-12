try:
    import serial
except ImportError:
    print("Could not import module: serial")

from dataclasses import dataclass


@dataclass
class EisMeasurementSetup:
    pass


class ISX_3:
    def __init__(self, n_el) -> None:
        # number of electrodes used
        self.n_el = n_el

    def connect_device_FS(self, port: str, baudrate: int = 9600, timeout: int = 1):
        """
        Connect to full speed
        """
        if hasattr(self, "serial_protocol"):
            print(
                "Serial connection 'self.serial_protocol' already defined as {self.serial_protocol}."
            )
        else:
            self.serial_protocol = "FS"
        self.device = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )
        print("Connection to", self.device.name, "is established.")

    def SetOptions(self):
        # 0x97
        pass

    def GetOptions(self):
        # 0x98
        pass

    def ResetSystem(self):
        # 0xA1
        pass

    def SetFE_Settings(self):
        # 0xB0
        pass

    def GetFE_Settings(self):
        # 0xB1
        pass

    def SetExtensionPortChannel(self):
        # 0xB2
        pass

    def GetExtensionPortChannel(self):
        # 0xB3
        pass

    def GetExtensionPortModule(self):
        # 0xB5
        pass

    def GetSetup(self):
        # 0xB6
        pass

    def SetSetup(self):
        # 0xB7
        pass

    def StartMeasure(self):
        # 0xB8
        pass

    def SetSyncTime(self):
        # 0xB9
        pass

    def GetSyncTime(self):
        # 0xBA
        pass

    def GetDeviceID(self):
        # 0xD1
        pass

    def GetFPGAfirmwareID(self):
        # 0xD2
        pass

    def GetExtensionPortChannel(self):
        # 0xD3
        pass


# 0xBD - Set Ethernet Configuration
# 0xBE - Get Ethernet Configuration
# 0xCF - TCP connection watchdog
# 0xD0 - Get ARM firmware ID
