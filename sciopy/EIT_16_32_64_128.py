try:
    import serial
except ImportError:
    print("Could not import module: serial")

from usb_hs_handling import connect_COM_port_usb_hs

from sciopy_dataclasses import EitMeasurementSetup


class EIT_16_32_64_128:
    def __init__(self, n_el) -> None:
        # number of electrodes used
        self.n_el = n_el
        self.channel_group = self.init_channel_group()

    def init_channel_group(self):
        if self.n_el in [16, 32, 48, 64]:
            return [ch + 1 for ch in range(self.n_el // 16)]
        else:
            raise ValueError(
                f"Unallowed value: {self.n_el}. Please set 16, 32, 48 or 64 electrode mode."
            )

    def connect_device_HS(self):
        """
        Connect to high speed
        """
        if hasattr(self, "serial_protocol"):
            print(
                "Serial connection 'self.serial_protocol' already defined as {self.serial_protocol}."
            )
        else:
            self.serial_protocol = "HS"
        self.device = connect_COM_port_usb_hs()

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

    def write_setup(self, setup: EitMeasurementSetup):
        self.setup = setup
        if self.serial_protocol == "HS":
            pass
        elif self.serial_protocol == "FS":
            pass

    def software_reset(self):
        pass

    def set_measurement_setup(self):
        pass

    def get_measurement_setup(self):
        pass

    def start_stop_measurement(self):
        pass

    def set_output_configuration(self):
        pass

    def get_output_configuration(self):
        pass

    def get_device_info(self):
        pass

    def get_firmware_IDs(self):
        pass


# 0xB5 - Get temperature
# 0xC6 - Set Battery Control
# 0xC7 - Get Battery Control
# 0xC8 - Set LED Control
# 0xC9 - Get LED Control
# 0xCB - FrontIOs
# 0xCC - Power Plug Detect
