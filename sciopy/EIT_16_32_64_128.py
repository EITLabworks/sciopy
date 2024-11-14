try:
    import serial
except ImportError:
    print("Could not import module: serial")


from .com_util import (
    clTbt_dp,
    clTbt_sp,
    del_hex_in_list,
    reshape_full_message_in_bursts,
    split_bursts_in_frames,
)

import numpy as np
from pyftdi.ftdi import Ftdi


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

from .sciopy_dataclasses import EitMeasurementSetup


class EIT_16_32_64_128:
    def __init__(self, n_el: int) -> None:
        """
        __init__

        Parameters
        ----------
        n_el : int
            number of electrodes used for measurement.
        """
        self.n_el = n_el

        self.channel_group = self.init_channel_group()
        self.print_msg = True
        self.ret_hex_int = None

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

    def SystemMessageCallback_usb_fs(self):
        """
        !Only used if a full-speed connection is established!

        Reads the message buffer of a serial connection. Also prints out the general system message.
        """
        timeout_count = 0
        received = []
        received_hex = []
        data_count = 0

        while True:
            buffer = self.device.read()
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

        if self.ret_hex_int is None:
            return
        elif self.ret_hex_int == "hex":
            return received_hex
        elif self.ret_hex_int == "int":
            return received
        elif self.ret_hex_int == "both":
            return received, received_hex

    def SystemMessageCallback_usb_hs(self):
        """
        !Only used if a high-speed connection is established!

        Reads the message buffer of a serial connection. Also prints out the general system message.
        """

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

        if self.ret_hex_int is None:
            return
        elif self.ret_hex_int == "hex":
            return received_hex
        elif self.ret_hex_int == "int":
            return received
        elif self.ret_hex_int == "both":
            return received, received_hex

    def SystemMessageCallback(self):
        """
        SystemMessageCallback
        """
        if self.serial_protocol == "HS":
            self.SystemMessageCallback_usb_hs()
        elif self.serial_protocol == "FS":
            self.SystemMessageCallback_usb_fs()

    def write_command_string(self, command):
        """
        Function for writing a command 'bytearray(...)' to the serial port
        """
        if self.serial_protocol == "HS":
            self.device.write_data(command)
        elif self.serial_protocol == "FS":
            self.device.write(command)
        self.SystemMessageCallback()

    # --- sciospec device commands

    def SoftwareReset(self):
        self.print_msg = True
        self.write_command_string(bytearray([0xA1, 0x00, 0xA1]))
        self.print_msg = False

    def update_BurstCount(self, burst_count):
        self.print_msg = True
        self.setup.burst_count = burst_count
        self.write_command_string(
            bytearray([0xB0, 0x03, 0x02, 0x00, self.setup.burst_count, 0xB0])
        )
        self.print_msg = False

    def update_FrameRate(self, framerate):
        self.print_msg = True
        self.setup.framerate = framerate
        self.write_command_string(
            bytearray(
                list(
                    np.concatenate([[176, 5, 3], clTbt_sp(self.setup.framerate), [176]])
                )
            )
        )
        self.print_msg = False

    def SetMeasurementSetup(self, setup: EitMeasurementSetup):
        """
        set_measurement_config sets the ScioSpec device configuration depending on the EitMeasurementSetup configuration dataclass.
        """

        self.setup = setup
        self.print_msg = False
        self.ResetMeasurementSetup()

        # set burst count | for 3: ["B0 03 02 00 03 B0"]
        self.write_command_string(
            bytearray([0xB0, 0x03, 0x02, 0x00, setup.burst_count, 0xB0])
        )

        # set excitation alternating current amplitude double precision
        # A_min = 100nA
        # A_max = 10mA
        if setup.amplitude > 0.01:
            print(
                f"Amplitude {setup.amplitude}A is out of available range.\nSet amplitude to 10mA."
            )
            setup.amplitude = 0.01
        self.write_command_string(
            bytearray(
                list(np.concatenate([[176, 9, 5], clTbt_dp(setup.amplitude), [176]]))
            )
        )
        # ADC range settings: [+/-1, +/-5, +/-10]
        # ADC range = +/-1  : B0 02 0D 01 B0
        # ADC range = +/-5  : B0 02 0D 02 B0
        # ADC range = +/-10 : B0 02 0D 03 B0
        if setup.adc_range == 1:
            self.write_command_string(bytearray([0xB0, 0x02, 0x0D, 0x01, 0xB0]))
        elif setup.adc_range == 5:
            self.write_command_string(bytearray([0xB0, 0x02, 0x0D, 0x02, 0xB0]))
        elif setup.adc_range == 10:
            self.write_command_string(bytearray([0xB0, 0x02, 0x0D, 0x03, 0xB0]))
        # Gain settings:
        # Gain = 1     : B0 03 09 01 00 B0
        # Gain = 10    : B0 03 09 01 01 B0
        # Gain = 100   : B0 03 09 01 02 B0
        # Gain = 1_000 : B0 03 09 01 03 B0
        if setup.gain == 1:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x00, 0xB0]))
        elif setup.gain == 10:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x01, 0xB0]))
        elif setup.gain == 100:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x02, 0xB0]))
        elif setup.gain == 1_000:
            self.write_command_string(bytearray([0xB0, 0x03, 0x09, 0x01, 0x03, 0xB0]))

        # Single ended mode:
        self.write_command_string(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))

        # Excitation switch type:
        self.write_command_string(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))

        # Set framerate:
        self.write_command_string(
            bytearray(
                list(np.concatenate([[176, 5, 3], clTbt_sp(setup.framerate), [176]]))
            )
        )
        # Set frequencies:
        # [CT] 0C 04 [fmin] [fmax] [fcount] [ftype] [CT]
        f_min = clTbt_sp(setup.exc_freq)
        f_max = clTbt_sp(setup.exc_freq)
        f_count = [0, 1]
        f_type = [0]  # linear/log
        # bytearray
        self.write_command_string(
            bytearray(
                list(
                    np.concatenate([[176, 12, 4], f_min, f_max, f_count, f_type, [176]])
                )
            )
        )

        # Set injection config
        assert setup.n_el == self.n_el, print(
            "Number of electrodes in setup configuration must match Eit_16_32_64_128() initialization."
        )
        el_inj = np.arange(1, setup.n_el + 1)
        el_gnd = np.roll(el_inj, -(setup.inj_skip + 1))
        for v_el, g_el in zip(el_inj, el_gnd):
            self.write_command_string(bytearray([0xB0, 0x03, 0x06, v_el, g_el, 0xB0]))

        self.print_msg = True
        # Set output configuration - enable all
        # |-- Excitation setting | [CT] 02 01 [enable/disable] [CT]
        self.write_command_string(bytearray([0xB2, 0x02, 0x01, 0x01, 0xB2]))
        # |-- Current row in the frequency stack | [CT] 02 02 [enable/disable] [CT]
        self.write_command_string(bytearray([0xB2, 0x02, 0x02, 0x01, 0xB2]))
        # |-- Timestamp | [CT] 02 03 [enable/disable] [CT]
        self.write_command_string(bytearray([0xB2, 0x02, 0x03, 0x01, 0xB2]))
        self.print_msg = False

    def SaveSettings(self):
        print("TBD (to be checked)")
        self.print_msg = True
        self.write_command_string(bytearray([0x90, 0x00, 0x90]))
        self.print_msg = False

    def ResetMeasurementSetup(self):
        self.print_msg = True
        self.write_command_string(bytearray([0xB0, 0x01, 0x01, 0xB0]))
        self.print_msg = False

    def GetMeasurementSetup(self, setup_of: str):
        """
        GetMeasurementSetup

        Burst Count                                    2 -> 0x02
        Frame Rate                                     3 -> 0x03
        Excitation Frequencies                         4 -> 0x04
        Excitation Amplitude                           5 -> 0x05
        Excitation Sequence                            6 -> 0x06
        Single-Ended or Differential Measure Mode      7 -> 0x08
        Gain Settings                                  8 -> 0x09
        Excitation Switch Type                         9 -> 0x0C
        """

        print("TBD (to be checked)")
        self.print_msg = True
        self.write_command_string(bytearray([0xB1, 0x01, setup_of, 0xB1]))
        print("TBD: Translation")
        self.print_msg = False

    def StartStopMeasurement(self, return_as="pot_mat"):
        if self.serial_protocol == "HS":
            self.device.write_data(bytearray([0xB4, 0x01, 0x01, 0xB4]))
            self.ret_hex_int = "hex"
            self.print_msg = False

            data = self.SystemMessageCallback_usb_hs()

            self.device.write_data(bytearray([0xB4, 0x01, 0x00, 0xB4]))
            self.ret_hex_int = None
            self.SystemMessageCallback()

        elif self.serial_protocol == "FS":
            self.device.write(bytearray([0xB4, 0x01, 0x01, 0xB4]))
            self.ret_hex_int = "hex"
            self.print_msg = False

            data = self.SystemMessageCallback_usb_fs()

            self.device.write(bytearray([0xB4, 0x01, 0x00, 0xB4]))
            self.ret_hex_int = None
            self.SystemMessageCallback()

        data = del_hex_in_list(data)
        data = reshape_full_message_in_bursts(data, self.setup)
        data = split_bursts_in_frames(data, self.setup.burst_count, self.channel_group)
        self.data = data

        if return_as == "hex":
            return data
        elif return_as == "pot_mat":
            return self.get_data_as_matrix()

    def get_data_as_matrix(self):
        pot_matrix = np.empty(
            (self.setup.burst_count, self.n_el, self.n_el), dtype=complex
        )

        for b_c, burst in enumerate(self.data):
            row = -1
            for frame in burst:
                curr_grp = frame.channel_group
                if curr_grp == 1:
                    row += 1
                el_signs = list()
                for ch in range(16):
                    el_signs.append(frame.__dict__[f"ch_{ch+1}"])

                el_signs = np.array(el_signs)
                start_idx = (curr_grp - 1) * 16
                stop_idx = curr_grp * 16
                pot_matrix[b_c, row, start_idx:stop_idx] = el_signs
        self.data = pot_matrix
        return pot_matrix

    def SetOutputConfiguration(self):
        print("TBD")

    def GetOutputConfiguration(self):
        self.print_msg = True
        # |-- Excitation setting | [CT] 02 01 [enable/disable] [CT]
        print("Excitation setting: [enable/disable]")
        self.write_command_string(bytearray([0xB3, 0x01, 0x01, 0xB2]))
        # |-- Current row in the frequency stack | [CT] 02 02 [enable/disable] [CT]
        print("Current row in the frequency stack: [enable/disable]")
        self.write_command_string(bytearray([0xB3, 0x01, 0x02, 0xB2]))
        # |-- Timestamp | [CT] 02 03 [enable/disable] [CT]
        print("Timestamp: [enable/disable]")
        self.write_command_string(bytearray([0xB3, 0x01, 0x03, 0xB2]))
        self.print_msg = False

    def GetDeviceInfo(self):
        self.print_msg = True
        self.write_command_string(bytearray([0xD1, 0x00, 0xD1]))
        self.print_msg = False

    def GetFirmwareIDs(self):
        self.print_msg = True
        self.write_command_string(bytearray([0xD2, 0x00, 0xD2]))
        self.print_msg = False

    def PowerPlugDetect(self):
        self.print_msg = True
        self.write_command_string(bytearray([0xCC, 0x01, 0x81, 0xCC]))
        self.print_msg = False

        # 0xB5 - Get temperature
        # 0xC6 - Set Battery Control
        # 0xC7 - Get Battery Control
        # 0xC8 - Set LED Control
        # 0xC9 - Get LED Control
        # 0xCB - FrontIOs
