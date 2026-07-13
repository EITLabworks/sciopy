"""Serial interface for Sciospec ISX-3 and ISX-3mini devices."""

from dataclasses import asdict, dataclass
import ipaddress
import struct
import time
from typing import Iterable, Optional

import serial

from .sciopy_dataclasses import EisMeasurementSetup


SYSTEM_MESSAGES = {
    0x01: "Frame-Not-Acknowledge: Incorrect syntax",
    0x02: "Timeout: Communication-timeout (less data than expected)",
    0x04: "Wake-Up Message: System boot ready",
    0x11: "TCP-Socket: Valid TCP client-socket connection",
    0x81: "Not-Acknowledge: Command has not been executed",
    0x82: "Not-Acknowledge: Command could not be recognized",
    0x83: "Command-Acknowledge: Command has been executed successfully",
    0x84: "System-Ready Message: System is operational and ready to receive data",
    0x90: "Overcurrent detected",
    0x91: "Overvoltage detected",
}

COMMANDS = {
    0x18: "Acknowledge / General System Message",
    0x90: "Save Settings",
    0x97: "Set Options",
    0x98: "Get Options",
    0xA1: "Reset System",
    0xB0: "Set FE Settings",
    0xB1: "Get FE Settings",
    0xB2: "Set ExtensionPort Channel",
    0xB3: "Get ExtensionPort Channel",
    0xB5: "Get ExtensionPort Module",
    0xB6: "Set Setup",
    0xB7: "Get Setup",
    0xB8: "Start/Stop Measure",
    0xB9: "Set Sync Time",
    0xBA: "Get Sync Time",
    0xBD: "Set Ethernet Configuration",
    0xBE: "Get Ethernet Configuration",
    0xCF: "TCP Connection Watchdog",
    0xD0: "Get ARM Firmware ID",
    0xD1: "Get Device ID",
    0xD2: "Get FPGA Firmware ID",
}

OPTION_CODES = {"timestamp_ms": 0x01, "timestamp_us": 0x02, "current_range": 0x04}
MEASUREMENT_MODES = {"2-point": 0x01, "4-point": 0x02, "3-point": 0x03}
MEASUREMENT_CHANNELS = {"bnc": 0x01, "extension": 0x02, "extension2": 0x03}
CURRENT_RANGES = {"auto": 0x00, "10ma": 0x01, "100ua": 0x02, "1ua": 0x04, "10na": 0x06}
VOLTAGE_RANGES = {"auto": 0x00, "1v": 0x01, "90mv": 0x02}
EXCITATION_TYPES = {"voltage": 0x01, "current": 0x02}
SCALES = {"linear": 0x00, "logarithmic": 0x01, "lin": 0x00, "log": 0x01}

EXTENSION_MODULES = {
    0x00: "No module",
    0x01: "MEArack",
    0x02: "MuxModule32",
    0x03: "ECIS Adapter",
    0x05: "ExtensionPortAdapter",
    0x06: "SlideChipAdapter",
    0x07: "Mux32any2any",
    0x08: "DaQEisMux",
    0x09: "Mux32any2any2202",
}
INTERNAL_MODULES = {
    0x00: "No module",
    0x01: "MuxModule16x4",
    0x02: "MuxModule32x2",
    0x07: "Mux32any2any",
    0x09: "Mux32any2any2202",
}


@dataclass(frozen=True)
class ISXMeasurement:
    """One decoded impedance value returned by command ``0xB8``.

    Attributes
    ----------
    frequency_id : int
        Zero-based identifier of the configured frequency point.
    impedance : complex
        Measured complex impedance in ohms.
    timestamp : int, optional
        Device timestamp when timestamp output is enabled.
    timestamp_unit : {"ms", "us"}, optional
        Unit used by ``timestamp``.
    current_range : int, optional
        Current-range code used for this point when range output is enabled.
    """

    frequency_id: int
    impedance: complex
    timestamp: Optional[int] = None
    timestamp_unit: Optional[str] = None
    current_range: Optional[int] = None


def _float_bytes(value: float) -> bytes:
    """Encode a number as a four-byte, big-endian IEEE-754 float."""
    return struct.pack(">f", float(value))


def _uint_bytes(value: int, length: int) -> bytes:
    """Encode a non-negative integer using exactly ``length`` bytes.

    Raises
    ------
    ValueError
        If ``value`` is not an integer or does not fit in the requested size.
    """
    if not isinstance(value, int) or not 0 <= value < 1 << (8 * length):
        raise ValueError(f"value must fit in {length} unsigned bytes")
    return value.to_bytes(length, "big")


def _choice(value, choices, name):
    """Resolve a case-insensitive symbolic protocol choice or numeric code."""
    if isinstance(value, str):
        try:
            return choices[value.lower()]
        except KeyError as error:
            raise ValueError(
                f"Unknown {name} {value!r}; choose from {tuple(choices)}"
            ) from error
    if isinstance(value, int) and value in choices.values():
        return value
    raise ValueError(f"Invalid {name}: {value!r}")


class ISX_3:
    """Interface for the documented Sciospec ISX-3 communication protocol.

    The class owns the serial transport, buffers partial protocol frames,
    decodes command responses, and stores measurements received from the
    device. Constructing an instance does not open a serial connection.
    """

    def __init__(self) -> None:
        """Initialize an unconnected ISX-3 interface with default output options."""
        self.print_msg = True
        self.device = None
        self.serial_protocol = None
        self._receive_buffer = bytearray()
        self._pending_command = None
        self.timestamp_mode = None
        self.current_range_output = False
        self.responses = []
        self.measurements = []
        self.setup = None

    def connect_device_FS(self, port: str, baudrate: int = 9600, timeout: float = 1):
        """Connect through the USB full-speed virtual serial interface.

        Parameters
        ----------
        port : str
            Serial device name, for example ``"COM3"`` or ``"/dev/ttyUSB0"``.
        baudrate : int, default=9600
            Serial baud rate.
        timeout : float, default=1
            Read timeout in seconds. It also terminates response collection.

        Returns
        -------
        ISX_3
            This instance, allowing fluent connection setup.
        """
        self.device = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )
        self.serial_protocol = "FS"
        self._receive_buffer.clear()
        if self.print_msg:
            print(f"Connection to {self.device.name} is established.")
        return self

    connect_device_USB2 = connect_device_FS

    def disconnect_device(self):
        """Close the active serial connection; do nothing when disconnected."""
        if self.device is None:
            return
        self.device.close()
        self.device = None
        self.serial_protocol = None

    disconnect_device_USB2 = disconnect_device

    def _require_connection(self):
        """Raise ``RuntimeError`` unless a serial device is connected."""
        if self.device is None:
            raise RuntimeError("No ISX-3 device connected.")

    @staticmethod
    def build_frame(command_tag: int, data: Iterable[int] = ()) -> bytearray:
        """Construct a Sciospec frame from a command tag and payload.

        The returned layout is ``[tag, payload length, payload..., tag]``.

        Raises
        ------
        ValueError
            If the tag is not a byte or the payload exceeds 255 bytes.
        """
        payload = bytes(data)
        if not 0 <= command_tag <= 0xFF:
            raise ValueError("command_tag must be a byte")
        if len(payload) > 0xFF:
            raise ValueError("command payload cannot exceed 255 bytes")
        return bytearray([command_tag, len(payload), *payload, command_tag])

    def parse_received_bytes(self, data) -> list[list[int]]:
        """Decode complete Sciospec frames from an arbitrary serial chunk.

        Incomplete trailing data remains buffered for the next call. Multiple
        frames contained in one USB read are returned separately.

        Raises
        ------
        ValueError
            If a complete frame has different start and end tags.
        """
        if data:
            self._receive_buffer.extend(data)
        frames = []
        while len(self._receive_buffer) >= 2:
            frame_length = self._receive_buffer[1] + 3
            if len(self._receive_buffer) < frame_length:
                break
            frame = list(self._receive_buffer[:frame_length])
            del self._receive_buffer[:frame_length]
            if frame[0] != frame[-1]:
                raise ValueError(
                    f"Invalid ISX-3 frame: start 0x{frame[0]:02X} != end 0x{frame[-1]:02X}"
                )
            frames.append(frame)
        return frames

    def send_message(self, message):
        """Write an already framed command to the connected serial device."""
        self._require_connection()
        return self.device.write(message)

    def read_message(self, size: int = 4096):
        """Read up to ``size`` bytes from the connected serial device."""
        self._require_connection()
        return self.device.read(size)

    def SystemMessageCallback(self, timeout: Optional[float] = None):
        """Read frames until timeout and return decoded responses.

        Parameters
        ----------
        timeout : float, optional
            Maximum collection time in seconds. If omitted, collection ends
            when the configured serial read returns no data.

        Returns
        -------
        list
            Decoded dictionaries and :class:`ISXMeasurement` objects in their
            receive order.
        """
        self._require_connection()
        deadline = None if timeout is None else time.monotonic() + timeout
        decoded = []
        while deadline is None or time.monotonic() < deadline:
            chunk = self.read_message()
            if not chunk:
                break
            for frame in self.parse_received_bytes(chunk):
                value = self.decode_frame(frame)
                decoded.append(value)
                self.responses.append(value)
                if isinstance(value, ISXMeasurement):
                    self.measurements.append(value)
                if not isinstance(value, ISXMeasurement):
                    description = self.describe_frame(frame, value)
                    if self.print_msg:
                        print(description)
        return decoded

    def write_command_string(self, command, timeout: Optional[float] = None):
        """Send a complete command frame and collect its response frames."""
        self._pending_command = list(command)
        self.send_message(command)
        return self.SystemMessageCallback(timeout=timeout)

    def send_command(self, command_tag: int, data: Iterable[int] = (), timeout=None):
        """Build, send, and read a documented Sciospec command frame.

        This is the low-level extension point for commands not yet represented
        by a convenience method.
        """
        return self.write_command_string(self.build_frame(command_tag, data), timeout)

    def describe_frame(self, frame, decoded=None):
        """Create a human-readable command or acknowledgement description."""
        tag = frame[0]
        name = COMMANDS.get(tag, "Unknown Command")
        if tag == 0x18:
            status = SYSTEM_MESSAGES.get(frame[2], f"Unknown status 0x{frame[2]:02X}")
            if self._pending_command is not None:
                command_tag = self._pending_command[0]
                command = COMMANDS.get(command_tag, f"Command 0x{command_tag:02X}")
                self._pending_command = None
                return f"{command} -> {status}"
            return status
        if decoded is not None:
            return f"{name} (0x{tag:02X}): {decoded}"
        return f"{name} (0x{tag:02X})"

    def decode_frame(self, frame):
        """Decode one validated protocol frame into a typed or dictionary value."""
        tag, payload = frame[0], bytes(frame[2:-1])
        if tag == 0x18:
            return {
                "command": tag,
                "status": payload[0],
                "message": SYSTEM_MESSAGES.get(payload[0]),
            }
        if tag == 0xB8:
            return self._decode_measurement(payload)
        if tag == 0xB1 and len(payload) >= 4:
            return {
                "measurement_mode": payload[0],
                "measurement_channel": payload[1],
                "current_range": payload[2],
                "voltage_range": payload[3],
            }
        if tag == 0xB3 and len(payload) == 4:
            return dict(
                zip(("counter", "reference", "working_sense", "working"), payload)
            )
        if tag == 0xB5:
            return self._decode_modules(payload)
        if tag == 0x98:
            return self._decode_option(payload)
        if tag == 0xB7:
            return self._decode_setup(payload)
        if tag == 0xBA and len(payload) == 4:
            return {"sync_time_us": int.from_bytes(payload, "big")}
        if tag == 0xBE:
            return self._decode_ethernet(payload)
        if tag in {0xD0, 0xD2}:
            developer_length = 2 if tag == 0xD0 else 5
            return {
                "developer_information": payload[:developer_length].hex(),
                "revision": int.from_bytes(
                    payload[developer_length : developer_length + 2], "big"
                ),
                "build": int.from_bytes(
                    payload[developer_length + 2 : developer_length + 4], "big"
                ),
            }
        if tag == 0xD1 and len(payload) >= 7:
            return {
                "information_version": payload[0],
                "device_identifier": int.from_bytes(payload[1:3], "big"),
                "serial_number": int.from_bytes(payload[3:5], "big"),
                "delivery_year": 2010 + payload[5],
                "delivery_month": payload[6],
                "developer_information": payload[7:].hex(),
            }
        return {"command": tag, "name": COMMANDS.get(tag), "data": list(payload)}

    def _decode_measurement(self, payload):
        """Decode a ``0xB8`` payload using the configured output options."""
        if len(payload) < 10:
            raise ValueError("Incomplete ISX-3 measurement frame")
        index = 2
        timestamp = None
        timestamp_unit = None
        if self.timestamp_mode == "ms":
            timestamp = int.from_bytes(payload[index : index + 4], "big")
            timestamp_unit, index = "ms", index + 4
        elif self.timestamp_mode == "us":
            timestamp = int.from_bytes(payload[index : index + 5], "big")
            timestamp_unit, index = "us", index + 5
        current_range = None
        if self.current_range_output:
            current_range, index = payload[index], index + 1
        if len(payload) - index != 8:
            raise ValueError(
                "Measurement layout does not match configured output options"
            )
        real, imaginary = struct.unpack(">ff", payload[index : index + 8])
        return ISXMeasurement(
            frequency_id=int.from_bytes(payload[:2], "big"),
            impedance=complex(real, imaginary),
            timestamp=timestamp,
            timestamp_unit=timestamp_unit,
            current_range=current_range,
        )

    @staticmethod
    def _decode_modules(payload):
        """Decode external and internal multiplexer module identifiers."""
        if len(payload) < 2:
            raise ValueError("Incomplete ExtensionPort module response")
        result = {"extension_module": EXTENSION_MODULES.get(payload[0], payload[0])}
        index = 1
        if payload[0] == 0x09:
            if len(payload) < 4:
                raise ValueError("Incomplete external module channel count")
            result["extension_channel_count"] = int.from_bytes(
                payload[index : index + 2], "big"
            )
            index += 2
        if index >= len(payload):
            raise ValueError("Missing internal module identifier")
        result["internal_module"] = INTERNAL_MODULES.get(payload[index], payload[index])
        index += 1
        if payload[index - 1] == 0x09 and len(payload) >= index + 2:
            result["internal_channel_count"] = int.from_bytes(
                payload[index : index + 2], "big"
            )
        return result

    @staticmethod
    def _decode_option(payload):
        """Decode a Get Options (``0x98``) response payload."""
        if not payload:
            return {}
        option, data = payload[0], payload[1:]
        if option == 0x03 and len(data) == 8:
            minimum, maximum = struct.unpack(">ff", data)
            return {
                "option": "frequency_range",
                "minimum_hz": minimum,
                "maximum_hz": maximum,
            }
        return {"option": option, "value": data[0] if len(data) == 1 else list(data)}

    @staticmethod
    def _decode_setup(payload):
        """Decode a Get Setup (``0xB7``) response payload."""
        if not payload:
            return {}
        option, data = payload[0], payload[1:]
        if option == 0x01 and len(data) == 2:
            return {"frequency_count": int.from_bytes(data, "big")}
        if option == 0x04 and len(data) % 4 == 0:
            return {
                "frequencies_hz": [
                    struct.unpack(">f", data[i : i + 4])[0]
                    for i in range(0, len(data), 4)
                ]
            }
        if option == 0x02 and len(data) >= 12:
            result = {
                "frequency_hz": struct.unpack(">f", data[0:4])[0],
                "precision": struct.unpack(">f", data[4:8])[0],
                "amplitude": struct.unpack(">f", data[8:12])[0],
            }
            index = 12
            while index < len(data):
                extended_option = data[index]
                if index + 5 > len(data):
                    raise ValueError("Incomplete extended frequency option")
                value = int.from_bytes(data[index + 1 : index + 5], "big")
                names = {
                    0x01: "point_delay_us",
                    0x02: "phase_sync",
                    0x03: "excitation_type",
                }
                result[
                    names.get(extended_option, f"option_0x{extended_option:02x}")
                ] = value
                index += 5
            return result
        if option == 0x33 and len(data) == 4:
            return {"dc_bias_v": struct.unpack(">f", data)[0]}
        return {"option": option, "data": list(data)}

    @staticmethod
    def _decode_ethernet(payload):
        """Decode IP address, MAC address, or DHCP response data."""
        if not payload:
            return {}
        option, data = payload[0], payload[1:]
        if option == 0x01 and len(data) == 4:
            return {"ip_address": str(ipaddress.IPv4Address(data))}
        if option == 0x02 and len(data) == 6:
            return {"mac_address": ":".join(f"{value:02X}" for value in data)}
        if option == 0x03 and len(data) == 1:
            return {"dhcp": bool(data[0])}
        return {"option": option, "data": list(data)}

    # General and option commands -------------------------------------------------
    def SaveSettings(self):
        """Persist supported settings in device flash using command ``0x90``."""
        return self.send_command(0x90)

    def ResetSystem(self):
        """Restart the complete device using command ``0xA1``."""
        return self.send_command(0xA1)

    SoftwareReset = ResetSystem

    def SetOptions(self, option, enabled=True):
        """Enable or disable a measurement-output option.

        Parameters
        ----------
        option : {"timestamp_ms", "timestamp_us", "current_range"} or int
            Symbolic option name or documented option byte.
        enabled : bool, default=True
            Desired option state. Enabling one timestamp mode replaces the
            previously tracked timestamp mode.

        Returns
        -------
        list
            Decoded device responses, normally followed by an ACK.
        """
        option_code = _choice(option, OPTION_CODES, "option")
        if option_code == 0x01 and enabled:
            self.timestamp_mode = "ms"
        elif option_code == 0x02 and enabled:
            self.timestamp_mode = "us"
        elif option_code in {0x01, 0x02} and not enabled:
            self.timestamp_mode = None
        elif option_code == 0x04:
            self.current_range_output = bool(enabled)
        return self.send_command(0x97, [option_code, int(bool(enabled))])

    def GetOptions(self, option):
        """Read a timestamp, current-range, or available-frequency option."""
        return self.send_command(
            0x98, [_choice(option, OPTION_CODES | {"frequency_range": 0x03}, "option")]
        )

    # Frontend and extension-port commands ---------------------------------------
    def SetFE_Settings(
        self, measurement_mode, measurement_channel, current_range, voltage_range="1v"
    ):
        """Append one frontend configuration to the device stack.

        Parameters accept either documented numeric codes or symbolic names
        from ``MEASUREMENT_MODES``, ``MEASUREMENT_CHANNELS``,
        ``CURRENT_RANGES``, and ``VOLTAGE_RANGES``.
        """
        data = [
            _choice(measurement_mode, MEASUREMENT_MODES, "measurement mode"),
            _choice(measurement_channel, MEASUREMENT_CHANNELS, "measurement channel"),
            _choice(current_range, CURRENT_RANGES, "current range"),
            _choice(voltage_range, VOLTAGE_RANGES, "voltage range"),
        ]
        return self.send_command(0xB0, data)

    def ClearFE_Settings(self):
        """Clear the frontend configuration stack using the manual's FF frame."""
        return self.send_command(0xB0, [0xFF, 0xFF, 0xFF])

    def GetFE_Settings(self):
        """Read the currently selected frontend configuration (command ``0xB1``)."""
        return self.send_command(0xB1)

    def SetExtensionPortChannel(self, counter, reference, working_sense, working):
        """Configure C, R, WS, and W selections on the extension port."""
        return self.send_command(0xB2, [counter, reference, working_sense, working])

    def GetExtensionPortChannel(self):
        """Read the current C, R, WS, and W extension-port selections."""
        return self.send_command(0xB3)

    def GetExtensionPortModule(self):
        """Identify connected external and internal extension modules."""
        return self.send_command(0xB5)

    # Setup commands --------------------------------------------------------------
    def InitSetup(self):
        """Reset the active setup and initialize an empty frequency stack."""
        return self.send_command(0xB6, [0x01])

    @staticmethod
    def _extended_options(point_delay=None, phase_sync=None, excitation_type=None):
        """Encode optional delay, phase-sync, and excitation-type fields."""
        data = bytearray()
        if point_delay is not None:
            data.extend([0x01, *_uint_bytes(point_delay, 4)])
        if phase_sync is not None:
            data.extend([0x02, *_uint_bytes(int(bool(phase_sync)), 4)])
        if excitation_type is not None:
            data.extend(
                [
                    0x03,
                    *_uint_bytes(
                        _choice(excitation_type, EXCITATION_TYPES, "excitation type"), 4
                    ),
                ]
            )
        return data

    def AddFrequencyPoint(
        self,
        frequency,
        precision,
        amplitude,
        *,
        point_delay=None,
        phase_sync=None,
        excitation_type=None,
    ):
        """Append one frequency point to the active setup.

        Parameters
        ----------
        frequency : float
            Excitation frequency in hertz. Zero selects DC resistance.
        precision : float
            Device precision factor.
        amplitude : float
            Peak excitation amplitude in volts or amperes.
        point_delay : int, optional
            Delay before the next point in microseconds.
        phase_sync : bool, optional
            Whether to switch phase-synchronously to the next point.
        excitation_type : {"voltage", "current"}, optional
            Unit and excitation mode used by ``amplitude``.
        """
        data = bytearray([0x02])
        data.extend(
            _float_bytes(frequency) + _float_bytes(precision) + _float_bytes(amplitude)
        )
        data.extend(self._extended_options(point_delay, phase_sync, excitation_type))
        return self.send_command(0xB6, data)

    def AddFrequencyList(
        self,
        start,
        stop,
        count,
        scale,
        precision,
        amplitude,
        *,
        point_delay=None,
        phase_sync=None,
        excitation_type=None,
    ):
        """Append a linearly or logarithmically spaced frequency block.

        ``start`` and ``stop`` are in hertz, ``count`` is the number of points,
        and ``amplitude`` is the peak voltage or current. The optional extended
        fields have the same meaning as in :meth:`AddFrequencyPoint`.
        """
        data = bytearray([0x03])
        data.extend(_float_bytes(start) + _float_bytes(stop) + _float_bytes(count))
        data.append(_choice(scale, SCALES, "frequency scale"))
        data.extend(_float_bytes(precision) + _float_bytes(amplitude))
        data.extend(self._extended_options(point_delay, phase_sync, excitation_type))
        return self.send_command(0xB6, data)

    def SetAmplitude(self, amplitude, excitation_type="voltage", row=None):
        """Set excitation amplitude for all points or one frequency row.

        Parameters
        ----------
        amplitude : float
            Peak amplitude in volts or amperes.
        excitation_type : {"voltage", "current"}, default="voltage"
            Excitation source type.
        row : int, optional
            Two-byte row index. If omitted, all rows are updated.
        """
        data = bytearray([0x05])
        if row is not None:
            data.extend(_uint_bytes(row, 2))
        data.append(_choice(excitation_type, EXCITATION_TYPES, "excitation type"))
        data.extend(_float_bytes(amplitude))
        return self.send_command(0xB6, data)

    def StartCompensation(self):
        """Start the interactive open/short/load compensation procedure."""
        return self.send_command(0xB6, [0x10])

    def AcknowledgeCompensation(self, accept=True):
        """Continue or abort a pending compensation-interaction request."""
        return self.send_command(0xB6, [0x11 if accept else 0x12])

    def SetCompensationLoad(self, value, load_type="resistance"):
        """Set the known compensation load in ohms or farads."""
        types = {"resistance": 0x01, "capacitor": 0x02}
        return self.send_command(
            0xB6, [0x16, _choice(load_type, types, "load type"), *_float_bytes(value)]
        )

    def ResetCompensationData(self):
        """Delete compensation data associated with the active setup."""
        return self.send_command(0xB6, [0x17, 0x01])

    def SetCompensationData(
        self,
        channel,
        row,
        open_value,
        short_value,
        load_value,
    ):
        """Upload one open/short/load compensation record.

        ``open_value``, ``short_value``, and ``load_value`` are complex values
        whose real and imaginary parts are encoded as big-endian floats.
        """
        data = bytearray([0x17, 0x02, *_uint_bytes(channel, 1), *_uint_bytes(row, 2)])
        for value in (open_value, short_value, load_value):
            value = complex(value)
            data.extend(_float_bytes(value.real))
            data.extend(_float_bytes(value.imag))
        return self.send_command(0xB6, data)

    def LoadSetup(self, slot):
        """Load setup and compensation data from flash slot 1 through 255."""
        return self.send_command(0xB6, [0x20, *_uint_bytes(slot, 1)])

    def SaveSetup(self, slot):
        """Save the active setup and compensation data to a flash slot."""
        return self.send_command(0xB7, [0x20, *_uint_bytes(slot, 1)])

    def SetDCBias(self, enabled):
        """Activate or deactivate DC-bias regulation on the configured channel."""
        return self.send_command(0xB6, [0x30, int(bool(enabled))])

    def AbortDCBias(self):
        """Abort the current DC-bias regulation process."""
        return self.send_command(0xB6, [0x32])

    def SetDCBiasValue(self, voltage):
        """Set the requested DC bias in the inclusive range -1 V to +1 V."""
        if not -1 <= voltage <= 1:
            raise ValueError("DC bias voltage must be between -1 V and +1 V")
        return self.send_command(0xB6, [0x33, *_float_bytes(voltage)])

    def GetSetup(self, option, data=()):
        """Read one setup property through command ``0xB7``.

        Parameters
        ----------
        option : {"frequency_count", "frequency_point", "frequency_list", "dc_bias"}
            Setup property to request.
        data : iterable of int, optional
            Additional command data, such as a two-byte frequency row.
        """
        return self.send_command(
            0xB7,
            [
                _choice(
                    option,
                    {
                        "frequency_count": 0x01,
                        "frequency_point": 0x02,
                        "frequency_list": 0x04,
                        "dc_bias": 0x33,
                    },
                    "setup option",
                ),
                *data,
            ],
        )

    def GetFrequencyCount(self):
        """Read the total number of configured frequency points."""
        return self.GetSetup("frequency_count")

    def GetFrequencyPoint(self, row):
        """Read frequency, precision, amplitude, and options for one row."""
        return self.GetSetup("frequency_point", _uint_bytes(row, 2))

    def GetFrequencyList(self):
        """Read all configured frequencies, including split response frames."""
        return self.GetSetup("frequency_list")

    def GetDCBias(self):
        """Read the configured DC-bias value in volts."""
        return self.GetSetup("dc_bias")

    def SetMeasurementSetup(self, setup: EisMeasurementSetup):
        """Initialize and populate a setup from :class:`EisMeasurementSetup`.

        The dataclass's start, stop, step, step mode, precision, and amplitude
        fields are translated into one frequency-list command. ``avg`` and
        ``measurement_time`` are consumed later by :meth:`StartStopMeasurement`.

        Raises
        ------
        TypeError
            If ``setup`` is not an :class:`EisMeasurementSetup` instance.
        """
        if not isinstance(setup, EisMeasurementSetup):
            raise TypeError("setup must be an EisMeasurementSetup instance")
        self.setup = setup
        responses = []
        responses.extend(self.InitSetup())
        responses.extend(
            self.AddFrequencyList(
                setup.start,
                setup.stop,
                setup.step,
                setup.stepmode,
                setup.precision,
                setup.amplitude,
            )
        )
        return responses

    # Measurement ----------------------------------------------------------------
    def StartMeasure(self, repeat=1, timeout=None):
        """Start a measurement and collect impedance frames.

        Parameters
        ----------
        repeat : int, default=1
            Number of spectra per channel configuration. Zero starts a
            continuous measurement that must be stopped explicitly.
        timeout : float, optional
            Maximum collection time in seconds.

        Returns
        -------
        list[ISXMeasurement]
            Measurements received before the read or explicit timeout.
        """
        self.measurements = []
        self.send_message(self.build_frame(0xB8, [0x01, *_uint_bytes(repeat, 2)]))
        self._pending_command = list(
            self.build_frame(0xB8, [0x01, *_uint_bytes(repeat, 2)])
        )
        self.SystemMessageCallback(timeout=timeout)
        return list(self.measurements)

    def StopMeasure(self):
        """Stop a running continuous measurement using command ``0xB8``."""
        return self.send_command(0xB8, [0x00])

    def StartStopMeasurement(self, repeat=None, timeout=None, return_as="measurement"):
        """Measure spectra and return records or complex impedance values.

        If ``repeat`` or ``timeout`` is omitted, values from the configured
        :class:`EisMeasurementSetup` are used. A continuous run (``repeat=0``)
        is stopped after collection.

        Parameters
        ----------
        return_as : {"measurement", "complex"}, default="measurement"
            Return full :class:`ISXMeasurement` records or only impedances.
        """
        if repeat is None:
            repeat = 1 if self.setup is None else int(self.setup.avg)
        if timeout is None and self.setup is not None and self.setup.measurement_time:
            timeout = float(self.setup.measurement_time)
        data = self.StartMeasure(repeat=repeat, timeout=timeout)
        if repeat == 0:
            self.StopMeasure()
        if return_as == "measurement":
            return data
        if return_as == "complex":
            return [measurement.impedance for measurement in data]
        raise ValueError("return_as must be 'measurement' or 'complex'")

    # Synchronization, network, and identification -------------------------------
    def SetSyncTime(self, microseconds):
        """Set inter-spectrum synchronization time from 0 to 180,000,000 µs."""
        if not 0 <= microseconds <= 180_000_000:
            raise ValueError("sync time must be between 0 and 180,000,000 µs")
        return self.send_command(0xB9, _uint_bytes(microseconds, 4))

    def GetSyncTime(self):
        """Read the currently configured synchronization time in microseconds."""
        return self.send_command(0xBA)

    def SetEthernetConfiguration(self, *, ip_address=None, dhcp=None):
        """Set either the static IPv4 address or DHCP state.

        Exactly one keyword must be provided. Saving and applying network
        configuration may additionally require ``SaveSettings`` and a reboot.
        """
        if (ip_address is None) == (dhcp is None):
            raise ValueError("provide exactly one of ip_address or dhcp")
        if ip_address is not None:
            return self.send_command(
                0xBD, [0x01, *ipaddress.IPv4Address(ip_address).packed]
            )
        return self.send_command(0xBD, [0x03, int(bool(dhcp))])

    def GetEthernetConfiguration(self, option):
        """Read ``ip_address``, ``mac_address``, or ``dhcp`` configuration."""
        options = {"ip_address": 0x01, "mac_address": 0x02, "dhcp": 0x03}
        return self.send_command(0xBE, [_choice(option, options, "Ethernet option")])

    def SetTCPWatchdog(self, seconds):
        """Set the TCP connection watchdog interval from 1 to 600 seconds."""
        if not 1 <= seconds <= 600:
            raise ValueError("TCP watchdog interval must be between 1 and 600 seconds")
        return self.send_command(0xCF, [0x00, *_uint_bytes(seconds, 4)])

    def GetARMFirmwareID(self):
        """Read ARM developer, revision, and build information (``0xD0``)."""
        return self.send_command(0xD0)

    def GetDeviceID(self):
        """Read device type, serial number, delivery date, and developer data."""
        return self.send_command(0xD1)

    def GetFPGAFirmwareID(self):
        """Read FPGA developer, revision, and build information (``0xD2``)."""
        return self.send_command(0xD2)

    GetFPGAfirmwareID = GetFPGAFirmwareID

    def setup_as_dict(self):
        """Return the configured EIS setup as a dictionary, or ``None``."""
        return None if self.setup is None else asdict(self.setup)


__all__ = ["ISX_3", "ISXMeasurement", "EisMeasurementSetup"]
