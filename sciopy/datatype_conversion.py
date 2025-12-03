"""
Project ：sciopy
Directory: sciopy/sciopy
File : datatype_conversion.py
Author ：Patricia Fuchs
Date ：03.12.2025 14:02
"""

import struct
import numpy as np

TWOPOWER24 = 16777216
TWOPOWER16 = 65536
TWOPOWER8 = 256

# -------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------- #
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


# -------------------------------------------------------------------------------------------------------------------- #
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


# -------------------------------------------------------------------------------------------------------------------- #
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
        single precision float
    """
    bytes_array = [int(b, 16) for b in bytes_array]
    bytes_array = bytes(bytes_array)
    return struct.unpack("!f", bytes(bytes_array))[0]


# -------------------------------------------------------------------------------------------------------------------- #
def byteintarray_to_float(bytes_array: np.ndarray) -> float:
    """
    Converts a bytes array to a float number. Array is array of integers representing bytes.

    Parameters
    ----------
    bytes_array : np.ndarray
        array of integers former being bytes

    Returns
    -------
    float
        single precision float
    """
    return struct.unpack("!f", bytes(bytes_array))[0]


# -------------------------------------------------------------------------------------------------------------------- #
def bytesarray_to_double(bytes_array: np.ndarray) -> float:
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
    return struct.unpack("!d", bytes(bytes_array))[0]


# -------------------------------------------------------------------------------------------------------------------- #
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


# -------------------------------------------------------------------------------------------------------------------- #
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


# -------------------------------------------------------------------------------------------------------------------- #
def four_byte_to_int(bytelist):
    """
    Converts a list of 4 integers representing bytes to int.

    Parameters
    ----------
    bytelist : np.ndarray/list of integers representing bytes MSB first

    Returns
    -------
    int
        integer number
    """
    return TWOPOWER24 * bytelist[0] + TWOPOWER16 * bytelist[1] + TWOPOWER8 * bytelist[2] + bytelist[3]


# -------------------------------------------------------------------------------------------------------------------- #
def two_byte_to_int(bytelist):
    """
    Converts a list of 2 integers representing bytes to int.

    Parameters
    ----------
    bytelist : np.ndarray/list of integers representing bytes MSB first

    Returns
    -------
    int
        integer number
    """
    return TWOPOWER8 * bytelist[0] + bytelist[1]


# -------------------------------------------------------------------------------------------------------------------- #
def bytelist_to_int(bytelist):
    """
    Converts a list of integers representing bytes MSB first to int.
    Parameters
    ----------
    bytelist : np.ndarray/list of integers representing bytes MSB first

    Returns
    -------
    int
        integer number
    """
    r = bytelist[-1]
    for j in range(2, len(bytelist)):
        r += bytelist[-j] * 2 ** ((j - 1) * 8)
    return r
