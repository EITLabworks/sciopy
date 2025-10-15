try:
    import serial
except ImportError:
    print("Could not import module: serial")

from dataclasses import dataclass

from sciopy.sciopy_dataclasses import EisMeasurementSetup

error_msg_dict = {
    "0x01": "init setup failed",
    "0x02": "add frequency block failed",
    "0x03": "set parasitic parameters failed",
    "0x04": "set acceleration settings failed",
    "0x05": "set sync time failed",
    "0x06": "set channel settings failed",
    "0x07": "set calibration data failed",
    "0x08": "set timestamp failed",
    "0x09": "start measurement failed",
    "0x22": "set amplitude failed",
}

frame_status_dict = {
    "0x01": "Frame-Not-Acknowledge: Incorrect syntax",
    "0x02": "Timeout: Communication-timeout (less data than expected)",
    "0x04": "Wake-Up Message: System boot ready",
    "0x81": "Not-Acknowledge: Command has not been executed",
    "0x82": "Not-Acknowledge: Command could not be recognized",
    "0x83": "Command-Acknowledge: Command has been executed successfully",
    "0x84": "System-Ready Message: System is operational and ready to receive data",
}


class ISX_3:
    def __init__(self, n_el) -> None:
        # number of electrodes used
        self.n_el = n_el

    def connect_device_USB2(self, port: str, baudrate: int = 9600, timeout: int = 1):
        """
        Connect to USB 2.0 Type B
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
        self.print_msg = True
        self.write_command_string(bytearray([0xA1, 0x00, 0xA1]))
        self.print_msg = False

    def SetFE_Settings(self, PP, CH, RA):
        """
        Configures the frontend measurement settings for the device.

        PP : int
            Measurement mode (see above for options).
        CH : int
            Measurement channel (see above for options).
        RA : int
            Range setting (see above for options).

        Frontend configuration:
        - PP (Measurement mode):
            - 0x02: 4 point configuration
        - CH (Measurement channel):
            - 0x01: BNC Port (ISX-3mini: Port 1)
            - 0x02: ExtensionPort
            - 0x03: ExtensionPort2 (ISX-3mini: Port 2, ISX-3v2: optional, InternalMux)
        - RA (Range Settings):
            - 0x01: 100 Ohm
            - 0x02: 10 kOhm
            - 0x04: 1 MOhm
        """
        self.print_msg = True
        self.write_command_string(bytearray([0xB0, PP, CH, RA, 0xB0]))
        self.print_msg = False

    def GetFE_Settings(self):
        """
        Retrieves the frontend measurement settings from the device.

        Returns:
            dict: Dictionary containing PP (Measurement mode), CH (Measurement channel), RA (Range setting).
        """
        self.print_msg = True
        # TBD: write_command_string needs to return response
        self.write_command_string(bytearray([0xB1, 0x00, 0xB1]))
        response = self.read_response()
        self.print_msg = False

        if (
            response
            and len(response) >= 6
            and response[0] == 0xB1
            and response[-1] == 0xB1
        ):
            self.PP = response[2]
            self.CH = response[3]
            self.RA = response[4]
            print("Frontend Settings:")
            print(f"Measurement Mode (PP): {self.PP}")
            print(f"Measurement Channel (CH): {self.CH}")
            print(f"Range Setting (RA): {self.RA}")
        else:
            print("Failed to get FE settings or invalid response.")
            return None

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

    def Action(self):
        self.print_msg = True
        self.write_command_string(bytearray([0xD2, 0x00, 0xD2]))
        self.print_msg = False


# - 0x90 - Save Settings
# - 0x97 - Set Options
# - 0x98 - Get Options
# - 0x99 - Set IOPort Configuration
# - 0x9A - Get IOPort Configuration
# - 0x9B - Set NTC Parameter 1
# - 0x9D - Set NTC Parameter 2
# - 0x9C - Get NTC Parameter 1
# - 0x9E - Get NTC Parameter 2
# - 0xA1 - Reset System
# - 0xB0 - Set FE Settings
# - 0xB1 - Get FE Settings
# - 0xB2 - Set ExtensionPort Channel
# - 0xB3 - Get ExtPort Channel
# - 0xB5 - Get ExtPort Module
# - 0xB6 - Set Setup
# - 0xB7 - Get Setup
# - 0xB8 - Start Measure
# - 0xB9 - Set Sync Time
# - 0xBA - Get Sync Time
# - 0xBD - Set Ethernet Configuration
# - 0xBE - Get Ethernet Configur
# - 0xD0 - Get ARM firmware ID
