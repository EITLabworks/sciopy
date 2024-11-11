try:
    import serial
except ImportError:
    print("Could not import module: serial")

import struct
from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np
from pyftdi.ftdi import Ftdi


@dataclass
class EitMeasurementSetup:
    burst_count: int
    total_meas_num: int
    n_el: int
    channel_group: list
    exc_freq: Union[int, float]
    framerate: Union[int, float]
    amplitude: Union[int, float]
    inj_skip: Union[int, list]
    gain: int
    adc_range: int
    notes: str
    configured: bool


class EIT_16_32_64_128:
    def __init__(self, n_el) -> None:
        # number of electrodes used
        self.n_el = n_el
        self.channel_group = self.init_channel_group()
        self.print_msg = True

    def init_channel_group(self):
        if self.n_el in [16, 32, 48, 64]:
            return [ch + 1 for ch in range(self.n_el // 16)]
        else:
            raise ValueError(
                f"Unallowed value: {self.n_el}. Please set 16, 32, 48 or 64 electrode mode."
            )

    def connect_device_HS(self, url: str = "ftdi://ftdi:232h/1", baudrate: int = 9000):
        """
        Connect to high speed
        """
        if hasattr(self, "serial_protocol"):
            print(
                "Serial connection 'self.serial_protocol' already defined as {self.serial_protocol}."
            )
        else:
            self.serial_protocol = "HS"

        serial = Ftdi().create_from_url(url=url)
        serial.purge_buffers()
        serial.set_bitmode(0x00, Ftdi.BitMode.RESET)
        serial.set_bitmode(0x40, Ftdi.BitMode.SYNCFF)
        serial.PARITY_NONE
        serial.SET_BITS_HIGH
        serial.STOP_BIT_1
        serial.set_baudrate(baudrate)
        self.device = serial

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

    # communication
    def SystemMessageCallback_usb_hs(self):
        """
        Reads the message buffer of a serial connection. Also prints out the general system message.
        """
        msg_dict = {
            "0x01": "No message inside the message buffer",
            "0x02": "Timeout: Communication-timeout (less data than expected)",
            "0x04": "Wake-Up Message: System boot ready",
            "0x11": "TCP-Socket: Valid TCP client-socket connection",
            "0x81": "Not-Acknowledge: Command has not been executed",
            "0x82": "Not-Acknowledge: Command could not be recognized",
            "0x83": "Command-Acknowledge: Command has been executed successfully",
            "0x84": "System-Ready Message: System is operational and ready to receive data",
            "0x92": "Data holdup: Measurement data could not be sent via the master interface",
        }
        ret_hex_int = None

        timeout_count = 0
        received = []
        received_hex = []
        data_count = 0

        while True:
            buffer = self.device.read_data_bytes(size=1024, attempt=150)
            if buffer:
                received.extend(buffer)
                data_count += len(buffer)
                timeout_count = 0
                continue
            timeout_count += 1
            if timeout_count >= 1:
                # Break if we haven't received any data
                break

            received = "".join(str(received))  # If you need all the data
        received_hex = [hex(receive) for receive in received]
        try:
            msg_idx = received_hex.index("0x18")
            if self.print_msg:
                print(msg_dict[received_hex[msg_idx + 2]])
        except BaseException:
            if self.print_msg:
                print(msg_dict["0x01"])
                # self.print_msg = False
        if self.print_msg:
            print("message buffer:\n", received_hex)
            print("message length:\t", data_count)

        if ret_hex_int is None:
            return
        elif ret_hex_int == "hex":
            return received_hex
        elif ret_hex_int == "int":
            return received
        elif ret_hex_int == "both":
            return received, received_hex

    def SystemMessageCallback(self):
        if self.serial_protocol == "HS":
            self.SystemMessageCallback_usb_hs()
        elif self.serial_protocol == "FS":
            pass  # TBD

    def write_command_string(self, command):
        """
        Function for writing a command 'bytearray(...)' to the serial port
        """
        if self.serial_protocol == "HS":
            self.device.write_data(command)
        elif self.serial_protocol == "FS":
            self.device.write(command)
        self.SystemMessageCallback()

    # ---

    def SoftwareReset(self):
        command = bytearray([0xA1, 0x00, 0xA1])
        self.write_command_string(command)

    def SetMeasurementSetup(self, ssms: EitMeasurementSetup):
        """
        set_measurement_config sets the ScioSpec device configuration depending on the ssms configuration dataclass.
        """

        def clTbt_sp(val: Union[int, float]) -> list:
            """
            clTbt_sp converts an integer or float value to a list of single precision bytes.
            """
            return [int(bt) for bt in struct.pack(">f", val)]

        def clTbt_dp(val: float) -> list:
            """
            clTbt_dp converts an integer or float value to a list of double precision bytes.
            """
            return [int(ele) for ele in struct.pack(">d", val)]

        self.print_msg = False
        # Set measurement setup:
        self.write_command_string(bytearray([0xB0, 0x01, 0x01, 0xB0]))
        # Set burst count: "B0 03 02 00 03 B0" = 3
        self.write_command_string(
            bytearray([0xB0, 0x03, 0x02, 0x00, ssms.burst_count, 0xB0])
        )
        # Excitation amplitude double precision
        # A_min = 100nA
        # A_max = 10mA
        if ssms.amplitude > 0.01:
            print(
                f"Amplitude {ssms.amplitude}A is out of available range.\nSet amplitude to 10mA."
            )
            ssms.amplitude = 0.01
        self.write_command_string(
            bytearray(
                list(np.concatenate([[176, 9, 5], clTbt_dp(ssms.amplitude), [176]]))
            )
        )
        # ADC range settings: [+/-1, +/-5, +/-10]
        # ADC range = +/-1  : B0 02 0D 01 B0
        # ADC range = +/-5  : B0 02 0D 02 B0
        # ADC range = +/-10 : B0 02 0D 03 B0
        if ssms.adc_range == 1:
            self.write_command_string(bytearray([0xB0, 0x02, 0x0D, 0x01, 0xB0]))
        elif ssms.adc_range == 5:
            self.write_command_string(bytearray([0xB0, 0x02, 0x0D, 0x02, 0xB0]))
        elif ssms.adc_range == 10:
            self.write_command_string(bytearray([0xB0, 0x02, 0x0D, 0x03, 0xB0]))
        # Gain settings:
        # Gain = 1     : B0 03 09 01 00 B0
        # Gain = 10    : B0 03 09 01 01 B0
        # Gain = 100   : B0 03 09 01 02 B0
        # Gain = 1_000 : B0 03 09 01 03 B0
        if ssms.gain == 1:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x00, 0xB0]))
        elif ssms.gain == 10:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x01, 0xB0]))
        elif ssms.gain == 100:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x02, 0xB0]))
        elif ssms.gain == 1_000:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x03, 0xB0]))
        # Single ended mode:
        self.write_command_string(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
        # Excitation switch type:
        self.write_command_string(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))
        # Set framerate:
        self.write_command_string(
            bytearray(
                list(np.concatenate([[176, 5, 3], clTbt_sp(ssms.framerate), [176]]))
            )
        )
        # Set frequencies:
        # [CT] 0C 04 [fmin] [fmax] [fcount] [ftype] [CT]
        f_min = clTbt_sp(ssms.exc_freq)
        f_max = clTbt_sp(ssms.exc_freq)
        f_count = [0, 1]
        f_type = [0]
        # bytearray
        self.write_command_string(
            bytearray(
                list(
                    np.concatenate([[176, 12, 4], f_min, f_max, f_count, f_type, [176]])
                )
            )
        )

        # Set injection config
        el_inj = np.arange(1, ssms.n_el + 1)
        el_gnd = np.roll(el_inj, -(ssms.inj_skip + 1))

        for v_el, g_el in zip(el_inj, el_gnd):
            self.write_command_string(bytearray([0xB0, 0x03, 0x06, v_el, g_el, 0xB0]))
        self.print_msg = True
        # Get measurement setup
        self.write_command_string(bytearray([0xB1, 0x01, 0x03, 0xB1]))
        # Set output configuration
        self.write_command_string(bytearray([0xB2, 0x02, 0x01, 0x01, 0xB2]))
        self.write_command_string(bytearray([0xB2, 0x02, 0x03, 0x01, 0xB2]))
        self.write_command_string(bytearray([0xB2, 0x02, 0x02, 0x01, 0xB2]))

    def ResetMeasurementSetup(self):
        command = bytearray([0xB0, 0x01, 0x01, 0xB0])
        self.write_command_string(command)

    def GetMeasurementSetup(self):
        command = bytearray([])
        self.write_command_string(command)

    def StartStopMeasurement(self):

        print("Starting measurement.")
        # start measurement
        command = bytearray([0xB4, 0x01, 0x01, 0xB4])
        self.write_command_string(command)

        measurement_data_hex = SystemMessageCallback(
            self.device, prnt_msg=False, ret_hex_int="hex"
        )

        # stop measurement
        print("Stopping measurement.")
        command = bytearray([0xB4, 0x01, 0x00, 0xB4])
        self.write_command_string(command)

        self.measurement_data_hex = measurement_data_hex
        return measurement_data_hex

    def SetOutputConfiguration(self):
        command = bytearray([])
        self.write_command_string(command)

    def GetOutputConfiguration(self):
        command = bytearray([])
        self.write_command_string(command)

    def GetDeviceInfo(self):
        command = bytearray([0xD1, 0x00, 0xD1])
        self.write_command_string(command)
        self.SystemMessageCallback()

    def GetFirmwareIDs(self):
        command = bytearray([0xD2, 0x00, 0xD2])
        self.write_command_string(command)
        self.SystemMessageCallback()


# 0xB5 - Get temperature
# 0xC6 - Set Battery Control
# 0xC7 - Get Battery Control
# 0xC8 - Set LED Control
# 0xC9 - Get LED Control
# 0xCB - FrontIOs
# 0xCC - Power Plug Detect
