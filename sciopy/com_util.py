from typing import Union

try:
    import serial
except ImportError:
    print("Could not import module: serial")

from .sciopy_dataclasses import EitMeasurementSetup, SingleFrame

import numpy as np
import struct
import sys
from glob import glob


def available_serial_ports() -> list:
    """
    Lists serial port names.

    Returns
    -------
    list
        a list of the serial ports available on the system

    Raises
    ------
    EnvironmentError
        on unsupported or unknown platforms
    OtherError
        when an other error
    """
    if sys.platform.startswith("win"):
        ports = ["COM%s" % (i + 1) for i in range(256)]
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        # this excludes your current terminal "/dev/tty"
        ports = glob("/dev/tty[A-Za-z]*")
    elif sys.platform.startswith("darwin"):
        ports = glob("/dev/tty.*")
    else:
        raise EnvironmentError("Unsupported platform")

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


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


def del_hex_in_list(lst: list) -> np.ndarray:
    """
    Delete the hexadecimal 0x python notation.

    Parameters
    ----------
    lst : list
        list of hexadecimals

    Returns
    -------
    np.ndarray
        cleared message
    """
    return np.array(
        [
            "0" + ele.replace("0x", "") if len(ele) == 1 else ele.replace("0x", "")
            for ele in lst
        ]
    )


def reshape_full_message_in_bursts(lst: list, ssms: EitMeasurementSetup) -> np.ndarray:
    """
    Takes the full message buffer and splits this message depeding on the measurement configuration into the
    burst count parts.

    Examples
    --------
    - input: n_el=16 -> lst.shape=(44804) | n_el=32 -> lst.shape=(89604,)
    - delete acknowledgement message: lst.shape=(4480,0) | lst.shape=(89600,)
    - split this depending on burst count: split_list.shape=(5, 8960) | split_list.shape=(5, 17920)
    """

    def length_correction(array: list) -> list:
        """
        Implemented by: Oveys Javanmardtilaki
        """
        seq_index = 0
        mask = np.ones(len(array), dtype=bool)
        seq_to_remove = ["18", "1", "92", "18"]
        for i in range(len(array)):
            if seq_to_remove[seq_index] in array[i]:
                seq_index += 1
                if seq_index == len(seq_to_remove):
                    start = i - len(seq_to_remove) + 1
                    end = i + 1
                    mask[start:end] = False
                    seq_index = 0
            else:
                seq_index = 0
        new_array = array[mask]
        return new_array

    lst = length_correction(lst)
    split_list = []
    # delete acknowledgement message
    lst = lst[4:]
    # split in burst count messages
    split_length = lst.shape[0] // ssms.burst_count
    for split in range(ssms.burst_count):
        split_list.append(lst[split * split_length : (split + 1) * split_length])
    return np.array(split_list)


def single_hex_to_int(str_num: str) -> int:
    """
    Delete the hexadecimal 0x python notation.

    Parameters
    ----------
    str_num : str
        single hexadecimal string

    Returns
    -------
    int
        integer number
    """
    if len(str_num) == 1:
        str_num = f"0x0{str_num}"
    else:
        str_num = f"0x{str_num}"
    return int(str_num, 16)


def bytesarray_to_float(bytes_array: np.ndarray) -> float:
    """
    Converts a bytes array to a float number.

    Parameters
    ----------
    bytes_array : np.ndarray
        array of bytes

    Returns
    -------
    float
        double precision float
    """
    bytes_array = [int(b, 16) for b in bytes_array]
    bytes_array = bytes(bytes_array)
    return struct.unpack("!f", bytes(bytes_array))[0]


def bytesarray_to_byteslist(bytes_array: np.ndarray) -> list:
    """
    Converts a bytes array to a list of bytes.

    Parameters
    ----------
    bytes_array : np.ndarray
        array of bytes

    Returns
    -------
    list
        list of bytes
    """
    bytes_array = [int(b, 16) for b in bytes_array]
    return bytes(bytes_array)


def bytesarray_to_int(bytes_array: np.ndarray) -> int:
    """
    Converts a bytes array to int number.

    Parameters
    ----------
    bytes_array : np.ndarray
        array of bytes

    Returns
    -------
    int
        integer number
    """
    bytes_array = bytesarray_to_byteslist(bytes_array)
    return int.from_bytes(bytes_array, "big")


def parse_single_frame(lst_ele: np.ndarray) -> SingleFrame:
    """
    Parse single data to the class SingleFrame.

    Parameters
    ----------
    lst_ele : np.ndarray
        single measurement list element

    Returns
    -------
    SingleFrame
        dataclass eit frame
    """
    channels = {}
    enum = 0
    for i in range(11, 135, 8):
        enum += 1
        channels[f"ch_{enum}"] = complex(
            bytesarray_to_float(lst_ele[i : i + 4]),
            bytesarray_to_float(lst_ele[i + 4 : i + 8]),
        )

    excitation_stgs = np.array([single_hex_to_int(ele) for ele in lst_ele[3:5]])

    sgl_frm = SingleFrame(
        start_tag=lst_ele[0],
        channel_group=int(lst_ele[2]),
        excitation_stgs=excitation_stgs,
        frequency_row=lst_ele[5:7],
        timestamp=bytesarray_to_int(lst_ele[7:11]),
        **channels,
        end_tag=lst_ele[139],
    )
    return sgl_frm


def split_bursts_in_frames(
    split_list: np.ndarray, burst_count: int, channel_group: list
) -> np.ndarray:
    """
    Takes the splitted list from `reshape_full_message_in_bursts()` and parses the single frames.

    Returns
    -------
    np.ndarray
        channel depending burst frames
    """
    msg_len = 140  # Constant
    frame = []  # Channel group depending frame
    burst_frame = []  # single burst count frame with channel depending frame
    subframe_length = split_list.shape[1] // msg_len
    for bursts in range(burst_count):  # Iterate over bursts
        tmp_split_list = np.reshape(split_list[bursts], (subframe_length, msg_len))
        for subframe in range(subframe_length):
            parsed_sgl_frame = parse_single_frame(tmp_split_list[subframe])
            # Select the right channel group data
            if parsed_sgl_frame.channel_group in channel_group:
                frame.append(parsed_sgl_frame)
        burst_frame.append(frame)
        frame = []  # Reset channel depending single burst frame
    return np.array(burst_frame)
