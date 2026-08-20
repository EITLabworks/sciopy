"""Module for interfacing with the Sciospec EIT devices via serial communication"""

import serial

from .com_util import (
    clTbt_dp,
    clTbt_sp,
    clTbt_u16,
)

import numpy as np
from pyftdi.ftdi import Ftdi

from .sciopy_dataclasses import EitMeasurementSetup
from .usb_message_parser import (
    MessageParser,
    make_eitframes_hex,
    get_data_as_matrix,
    make_results_folder,
)


class EIT_16_32_64_128:
    """
    A class for interfacing with the Sciospec EIT 16/32/64/128 devices.
    """

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
        self.cMessageParser = None
        self.setup = None

    def init_channel_group(self):
        """
        Initializes and returns a list representing the channel group based on the number of electrodes.
        Returns:
            list: A list of channel group indices, where each index corresponds to a channel.
                  The number of channels is determined by dividing `self.n_el` by 16.
        Raises:
            ValueError: If `self.n_el` is not one of the allowed values (16, 32, 48, 64, or 128).
        Notes:
            - Allowed values for `self.n_el` are 16, 32, 48, 64, and 128.
            - The returned list contains consecutive integers starting from 1 up to `self.n_el // 16`.
        """

        if self.n_el in [16, 32, 48, 64, 128]:
            return [ch + 1 for ch in range(self.n_el // 16)]
        else:
            raise ValueError(
                f"Unallowed value: {self.n_el}. Please set 16, 32, 48, 64 or 128 electrode mode."
            )

    def connect_device_HS(self, url: str = "ftdi://ftdi:232h/1", baudrate: int = 9000):
        """
        Establishes a high-speed serial connection to an FTDI device.

        This method initializes the FTDI device using the specified URL and baudrate,
        configures the device for synchronous FIFO mode, and sets up the serial protocol.
        If a serial connection is already defined, it notifies the user.

        Args:
            url (str): The FTDI device URL. Defaults to "ftdi://ftdi:232h/1".
            baudrate (int): The baud rate for the serial connection. Defaults to 9000.

        Side Effects:
            Sets the `self.serial_protocol` attribute to "HS" if not already defined.
            Initializes and configures the FTDI device, assigning it to `self.device`.

        Raises:
            Any exceptions raised by the FTDI library during device initialization or configuration.
        """
        if hasattr(self, "serial_protocol"):
            print(
                f"Replacing existing {self.serial_protocol} serial connection with HS."
            )
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
        self.cMessageParser = MessageParser(self.device, devicetype="HS")

    def connect_device_FS(self, port: str, baudrate: int = 9600, timeout: int = 1):
        """
        Establishes a serial connection to a device using the FS protocol.

        Parameters:
            port (str): The serial port to connect to (e.g., 'COM3' or '/dev/ttyUSB0').
            baudrate (int, optional): The baud rate for the serial connection. Defaults to 9600.
            timeout (int, optional): The timeout value for the serial connection in seconds. Defaults to 1.

        Notes:
            - If a serial connection is already defined in 'self.serial_protocol', a message is printed.
            - Sets 'self.serial_protocol' to "FS" if not already defined.
            - Initializes 'self.device' as a serial.Serial object with specified parameters.
            - Prints a confirmation message upon successful connection.
        """
        if hasattr(self, "serial_protocol"):
            print(
                f"Replacing existing {self.serial_protocol} serial connection with FS."
            )
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
        self.cMessageParser = MessageParser(self.device, devicetype="FS")

    def disconnect_device(self):
        """
        Disconnects the currently connected device by closing its connection.

        This method should be called to safely terminate communication with the device.
        """
        self.device.close()

    def send_message(self, message):
        """
        Sends bytes using the protocol selected by ``connect_device_HS`` or
        ``connect_device_FS``.
        """
        if self.serial_protocol == "HS":
            self.device.write_data(message)
        elif self.serial_protocol == "FS":
            self.device.write(message)
        else:
            raise ValueError(f"Unsupported serial protocol: {self.serial_protocol!r}")

    def read_message(self):
        """
        Reads one buffer using the connected parser's HS or FS transport.
        """
        if self.cMessageParser is None:
            raise RuntimeError("No device connected.")
        return self.cMessageParser.device_read()

    def SystemMessageCallback(self):
        """
        Reads and handles pending messages from the connected device.

        The message parser is configured for the selected serial protocol when
        the device is connected, so both HS and FS connections use the same
        parsing entry point here.

        Returns:
            list: Measurement frames collected by the message parser. For a
            system-message-only buffer this list is empty.
        """
        if self.cMessageParser is None:
            raise RuntimeError("No device connected.")
        self.cMessageParser.bPrintMessages = self.print_msg
        return self.cMessageParser.read_usb_till_timeout(
            bSaveData=False,
            bDeleteDataFrame=True,
            # A callback can run directly after connecting, before a
            # measurement setup (and therefore an EIT frame) exists.
            bStartReset=False,
        )

    def write_command_string(self, command):
        """
        Sends a command string to the device using the appropriate serial protocol.

        Depending on the value of `self.serial_protocol`, the command is sent using either
        high-speed ("HS") or full-speed ("FS") protocol. After sending the command, the
        system message callback is triggered.

        Args:
            command (str): The command string to be sent to the device.

        Raises:
            AttributeError: If `self.device` does not have the required method for the selected protocol.
        """
        if self.cMessageParser is None:
            raise RuntimeError("No device connected.")
        self.cMessageParser.bPrintMessages = self.print_msg
        self.cMessageParser.set_pending_command(command)
        self.send_message(command)
        self.cMessageParser.read_usb_till_timeout(
            bSaveData=False,
            bDeleteDataFrame=True,
            # Command responses do not require an EIT measurement frame and
            # commands such as GetDeviceInfo can run before a setup exists.
            bStartReset=False,
        )

    # --- sciospec device commands

    def SoftwareReset(self):
        """
        Performs a software reset of the device.

        This method sends a specific command sequence to the device to initiate a software reset.
        """
        self.print_msg = True
        self.write_command_string(bytearray([0xA1, 0x00, 0xA1]))
        self.print_msg = False

    def update_BurstCount(self, burst_count):
        """
        Updates the burst count setting and sends the corresponding command to the device.

        Args:
            burst_count (int): The new burst count value to set.

        Side Effects:
            - Sets `self.setup.burst_count` to the provided value.
            - Sends a command to the device using `write_command_string`.
            - Temporarily sets `self.print_msg` to True during the operation.
        self.print_msg = True

        """
        self.setup.burst_count = burst_count
        self.print_msg = True
        self.write_command_string(
            bytearray([0xB0, 0x03, 0x02, 0x00, self.setup.burst_count, 0xB0])
        )
        self.print_msg = False

    def update_FrameRate(self, framerate):
        """
        Updates the frame rate setting for the device and sends the corresponding command.

        Args:
            framerate (int): The desired frame rate to set.

        Side Effects:
            - Sets `self.setup.framerate` to the provided value.
            - Sends a command to the device to update the frame rate.
            - Temporarily sets `self.print_msg` to True during the operation.

        Note:
            The command sent is constructed using the `clTbt_sp` function and numpy's `concatenate`.
        """
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

    def update_ExcitationFrequencies(
        self,
        f_min: float,
        f_max: float = None,
        f_count: int = 1,
        f_scale: str = "lin",
    ):
        """
        Configures a single excitation frequency or a full frequency sweep.

        Sends the "Excitation Frequencies" option (0x04) of the "Set
        Measurement Setup" command (0xB0), as specified by the Sciospec
        System Message Protocol for the EIT-16/32/64/128 device family:

            [CT] 0x0C 0x04 [f_min] [f_max] [f_count] [f_scale] [CT]

            f_min, f_max : IEEE-754 single precision float, big-endian
                           (4 bytes each). Minimum / maximum excitation
                           frequency in Hz (100 Hz to 1 MHz).
            f_count      : unsigned 16-bit integer, big-endian (2 bytes).
                           Number of frequency points measured between
                           f_min and f_max (inclusive). f_count=1 selects a
                           single-frequency measurement at f_min.
            f_scale      : 1 byte. 0x00 = linear, 0x01 = logarithmic
                           distribution of the frequency points between
                           f_min and f_max.

        Parameters
        ----------
        f_min : float
            Start (or only) excitation frequency in Hz.
        f_max : float, optional
            Stop excitation frequency in Hz. Defaults to `f_min`, i.e. a
            single-frequency measurement.
        f_count : int, optional
            Number of frequency points in the sweep. Defaults to 1.
        f_scale : str, optional
            ``"lin"`` for a linear sweep or ``"log"`` for a logarithmic
            sweep. Defaults to ``"lin"``. Ignored when `f_count` is 1.

        Side Effects
        ------------
        - Updates `self.setup` (exc_freq, exc_freq_max, n_freq, freq_scale)
          and re-syncs the message parser's frame layout, when a
          measurement setup is present, so subsequently received frames are
          parsed with the right number of frequency points.
        - Sends the configuration command to the connected device.
        """
        scale_options = {"lin": 0x00, "log": 0x01}
        if f_scale not in scale_options:
            raise ValueError(f"Unknown f_scale {f_scale!r}; expected 'lin' or 'log'.")
        if f_count < 1:
            raise ValueError("f_count must be >= 1.")
        if f_max is None:
            f_max = f_min
        if f_count > 1 and f_max <= f_min:
            raise ValueError("f_max must be greater than f_min when f_count > 1.")

        if self.setup is not None:
            self.setup.exc_freq = f_min
            self.setup.exc_freq_max = f_max
            self.setup.n_freq = f_count
            self.setup.freq_scale = f_scale
            if self.cMessageParser is not None:
                # Re-sync the parser's frame layout (iNumFreqSettings etc.)
                # with the new sweep configuration.
                self.cMessageParser.set_measurement_setup(self.setup)

        # Set frequencies:
        # [CT] 0C 04 [fmin] [fmax] [fcount] [fscale] [CT]
        self.print_msg = True
        self.write_command_string(
            bytearray(
                list(
                    np.concatenate(
                        [
                            [176, 12, 4],
                            clTbt_sp(f_min),
                            clTbt_sp(f_max),
                            clTbt_u16(f_count),
                            [scale_options[f_scale]],
                            [176],
                        ]
                    )
                )
            )
        )
        self.print_msg = False

    def update_ExcitationFrequency(self, exc_freq):
        """
        Sets a single excitation frequency (no sweep).

        Kept for backward compatibility; equivalent to
        ``update_ExcitationFrequencies(f_min=exc_freq, f_count=1)``.

        Parameters
        ----------
        exc_freq : int or float
            frequency to be set from 100 Hz to 1 MHz
        """
        self.update_ExcitationFrequencies(f_min=exc_freq, f_count=1)

    def SetMeasurementSetup(self, setup: EitMeasurementSetup):
        """
        Configures the ScioSpec device measurement setup according to the provided EitMeasurementSetup dataclass.

        This method sets various device parameters including burst count, excitation amplitude, ADC range, gain,
        single-ended mode, excitation switch type, framerate, excitation frequencies, and electrode injection configuration.
        It also enables output configuration options such as excitation setting, frequency stack row, and timestamp.

        Parameters
        ----------
        setup : EitMeasurementSetup
            The measurement setup configuration containing parameters such as burst count, amplitude, ADC range, gain,
            framerate, excitation frequency, number of electrodes, and injection skip.

        Raises
        ------
        AssertionError
            If the number of electrodes in the setup does not match the device initialization.

        Notes
        -----
        - Amplitude is limited to a maximum of 10mA.
        - ADC range and gain are set according to predefined device commands.
        - Electrode injection configuration is set for all electrodes based on the provided setup.
        - Output configuration is enabled for excitation, frequency stack, and timestamp.
        """

        if not isinstance(setup, EitMeasurementSetup):
            raise TypeError("setup must be an EitMeasurementSetup instance.")
        if setup.n_el != self.n_el:
            raise ValueError(
                "Number of electrodes in setup configuration must match "
                "EIT_16_32_64_128 initialization."
            )

        self.setup = setup
        self.cMessageParser.set_measurement_setup(self.setup)
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

        # Single ended mode as standard setup, if else configured, skip patterns are possible:
        self.update_measurement_mode(setup.mea_mode, boundary=setup.mea_mode_boundary)
        # self.write_command_string(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))

        # Excitation switch type:
        self.write_command_string(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))

        # Set framerate:
        self.write_command_string(
            bytearray(
                list(np.concatenate([[176, 5, 3], clTbt_sp(setup.framerate), [176]]))
            )
        )
        # Set excitation frequencies (single frequency, or a full sweep when
        # setup.n_freq > 1):
        self.update_ExcitationFrequencies(
            f_min=setup.exc_freq,
            f_max=setup.exc_freq_max if setup.exc_freq_max is not None else setup.exc_freq,
            f_count=setup.n_freq,
            f_scale=setup.freq_scale,
        )

        # Set injection config
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
        """
        Resets the measurement setup by sending a specific command to the device.

        This method sets the `print_msg` flag to True, sends a reset command via
        `write_command_string`, and then sets `print_msg` back to False.

        The command sent is a bytearray: [0xB0, 0x01, 0x01, 0xB0].

        Returns:
            None
        """
        self.print_msg = True
        self.write_command_string(bytearray([0xB0, 0x01, 0x01, 0xB0]))
        self.print_msg = False

    def update_measurement_mode(
        self, meamode: str = "singleended", boundary: str = "internal"
    ):
        """
        Updates the measurement mode and its channel-group boundary behavior.

        Args:
            meamode: One of ``singleended``, ``skip0``, ``skip2`` or ``skip4``.
            boundary: ``internal`` for each channel group or ``external`` for
                all connected channels.
        """
        mode_options = {
            "singleended": 0x01,
            "skip0": 0x02,
            "skip2": 0x03,
            "skip4": 0x04,
        }
        if meamode not in mode_options:
            raise ValueError(
                f"Unknown measurement mode {meamode!r}; expected one of "
                f"{', '.join(mode_options)}."
            )
        boundary_options = {"internal": 0x01, "external": 0x02}
        if boundary not in boundary_options:
            raise ValueError(
                f"Unknown boundary {boundary!r}; expected 'internal' or 'external'."
            )

        self.print_msg = True
        self.write_command_string(
            bytearray(
                [
                    0xB0,
                    0x03,
                    0x08,
                    mode_options[meamode],
                    boundary_options[boundary],
                    0xB0,
                ]
            )
        )
        self.print_msg = False

    def GetMeasurementSetup(self, setup_of: int):
        """
        Requests one measurement setup value from the device.

        Args:
            setup_of: Setup identifier, for example 0x02 for burst count,
                0x03 for frame rate or 0x04 for excitation frequencies.
        """
        if not isinstance(setup_of, int) or not 0 <= setup_of <= 0xFF:
            raise ValueError("setup_of must be a byte-sized integer.")
        self.print_msg = True
        self.write_command_string(bytearray([0xB1, 0x01, setup_of, 0xB1]))
        self.print_msg = False

    def StartStopMeasurement(
        self,
        timeout: int = 0,
        return_as="pot_mat",
        bSaveData: bool = False,
        bDeleteData: bool = False,
        sSavePath: str = "C/",
        bResultsFolder=False,
        f_min: float = None,
        f_max: float = None,
        f_count: int = None,
        f_scale: str = "lin",
    ):
        """
        Starts and stops a measurement process using the configured serial protocol (HS or FS).
        Sends appropriate commands to the device to initiate and terminate measurement.
        If a timeout is specified, data is measrued for timeout seconds (burst_count==0). Else, a burst count needs to
        be specified, and all measured data is received.
        Processes the received data by removing hexadecimal values, reshaping messages into bursts,
        and splitting bursts into frames. Stores the processed data in NPZ format at sSavepath

        Args:
            timeout (int): Specifies the timeout in seconds.
            return_as (str, optional): Specifies the format of the returned data.
                - "hex": Returns the processed data as a list of hexadecimal values.
                - "pot_mat": Returns the processed data as a matrix using `get_data_as_matrix()`.
                Default is "pot_mat".
                - else: data is only stored
            bSaveData (bool): Specifies if the measured data is saved in NPZ format
            bDeleteData (bool): Specifies if the measured data is deleted out of memory after each EITframe, with
                bSaveData=True, measured data is saved and then removed from RAM
            sSavePath (str): Specifies the sPath where the measured data is saved.
            bResultsFolder (bool): Specifies if additionally a folder in sSavePath is created to store the data in
            f_min (float, optional): When given, (re)configures the device's excitation
                frequency/sweep via `update_ExcitationFrequencies` before starting the
                measurement. Omit to measure with whatever sweep is already configured
                (e.g. via `SetMeasurementSetup`).
            f_max (float, optional): Stop frequency of the sweep in Hz. Defaults to
                `f_min` (single-frequency measurement) when `f_min` is given but
                `f_max` is not.
            f_count (int, optional): Number of frequency points in the sweep. Defaults
                to `self.setup.n_freq` (or 1) when `f_min` is given but `f_count` is not.
            f_scale (str, optional): "lin" or "log" distribution of the sweep's
                frequency points. Defaults to "lin".

        Returns:
            list or matrix: The measurement data in the format specified by `return_as`.
            When a frequency sweep (`f_count` / `setup.n_freq` > 1) is active and
            `return_as="pot_mat"`, the returned matrix has shape
            (n_frames, n_excitations, n_freq, n_el); otherwise it keeps the previous
            (n_frames, n_excitations, n_el) shape.
        """

        if self.cMessageParser is None:
            raise RuntimeError("No device connected.")
        if self.setup is None:
            raise RuntimeError("SetMeasurementSetup must be called before measuring.")
        if return_as not in {"hex", "pot_mat", "eitframe"}:
            raise ValueError("return_as must be 'hex', 'pot_mat' or 'eitframe'.")

        if f_min is not None:
            # (Re-)configure a single frequency or a full sweep right before
            # the measurement starts.
            self.update_ExcitationFrequencies(
                f_min=f_min,
                f_max=f_max,
                f_count=f_count if f_count is not None else (self.setup.n_freq or 1),
                f_scale=f_scale,
            )

        # Start measurement
        self.cMessageParser.clear_out_data()
        sCurrentPath = make_results_folder(
            bResultsFolder, bSaveData, sSavePath
        )  # No new path is created  if bResultsFolder=False

        self.send_message(bytearray([0xB4, 0x01, 0x01, 0xB4]))
        self.cMessageParser.bPrintMessages = False
        if timeout != 0:
            self.cMessageParser.read_usb_for_seconds(
                timeout,
                bSaveData=bSaveData,
                bDeleteDataFrame=bDeleteData,
                sSavePath=sCurrentPath,
            )
        else:
            if self.setup.burst_count == 0:
                print("Burst count for this setup needs to be >=1")
                return
            self.cMessageParser.read_usb_till_timeout(
                bSaveData=bSaveData,
                bDeleteDataFrame=bDeleteData,
                sSavePath=sCurrentPath,
            )

        # Stop measurement
        self.send_message(bytearray([0xB4, 0x01, 0x00, 0xB4]))
        # All data is returned if wanted
        data = self.cMessageParser.read_usb_till_timeout(
            bSaveData=bSaveData,
            bDeleteDataFrame=bDeleteData,
            sSavePath=sCurrentPath,
            bStartReset=False,
        )

        self.cMessageParser.clear_out_data()
        if bDeleteData:
            return
        if return_as == "hex":
            return make_eitframes_hex(data)
        elif return_as == "pot_mat":
            return get_data_as_matrix(data)
        elif return_as == "eitframe":
            return data

    def get_data_as_matrix(self, data=None):
        """
        Converts parsed EIT frames into a complex-valued NumPy matrix.

        Args:
            data: Optional list of EIT frames. If omitted, the frames currently
                held by the message parser are used.
        """
        if data is None:
            if self.cMessageParser is None:
                raise RuntimeError("No device connected.")
            data = self.cMessageParser.ppcData
        return get_data_as_matrix(data)

    def SetOutputConfiguration(self):
        print("TBD")

    def GetOutputConfiguration(self):
        self.print_msg = True
        # |-- Excitation setting | [CT] 02 01 [enable/disable] [CT]
        print("Excitation setting: [enable/disable]")
        self.write_command_string(bytearray([0xB3, 0x01, 0x01, 0xB3]))
        # |-- Current row in the frequency stack | [CT] 02 02 [enable/disable] [CT]
        print("Current row in the frequency stack: [enable/disable]")
        self.write_command_string(bytearray([0xB3, 0x01, 0x02, 0xB3]))
        # |-- Timestamp | [CT] 02 03 [enable/disable] [CT]
        print("Timestamp: [enable/disable]")
        self.write_command_string(bytearray([0xB3, 0x01, 0x03, 0xB3]))
        self.print_msg = False

    def GetDeviceInfo(self):
        """
        Retrieves device information by sending a specific command to the device.

        This method sets the print_msg flag to True, sends the device info command
        using `write_command_string`, and then resets the print_msg flag to False.

        Returns:
            None
        """
        self.print_msg = True
        self.write_command_string(bytearray([0xD1, 0x00, 0xD1]))
        self.print_msg = False

    def GetFirmwareIDs(self):
        """
        Sends a command to retrieve firmware IDs from the device.

        This method sets the print_msg flag to True, sends a specific command
        to the device to request firmware identification, and then resets the
        print_msg flag to False.

        Returns:
            None
        """
        self.print_msg = True
        self.write_command_string(bytearray([0xD2, 0x00, 0xD2]))
        self.print_msg = False

    def PowerPlugDetect(self):
        """
        Detects the presence of a power plug by sending a specific command to the device.

        This method sets the print_msg flag to True, sends a command to check for power plug detection,
        and then resets the print_msg flag to False.

        Command sent:
            - [0xCC, 0x01, 0x81, 0xCC]: Power plug detection command.

        Note:
            The method does not return any value. It is assumed that the result of the detection
            is handled elsewhere in the class or by a callback.

        Side Effects:
            Modifies the self.print_msg attribute.
        """
        self.print_msg = True
        self.write_command_string(bytearray([0xCC, 0x01, 0x81, 0xCC]))
        self.print_msg = False

        # 0xB5 - Get temperature
        # 0xC6 - Set Battery Control
        # 0xC7 - Get Battery Control
        # 0xC8 - Set LED Control
        # 0xC9 - Get LED Control
        # 0xCB - FrontIOs
