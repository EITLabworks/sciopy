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
    result = []
    for element in lst:
        value = int(element, 16) if isinstance(element, str) else int(element)
        if not 0 <= value <= 0xFF:
            raise ValueError(f"Value {element!r} is not a byte.")
        result.append(f"{value:02x}")
    return np.asarray(result)


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
    return struct.unpack("!f", _hex_array_to_bytes(bytes_array, expected_length=4))[0]


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
    values = bytes(bytes_array)
    if len(values) != 4:
        raise ValueError("A single-precision float requires exactly 4 bytes.")
    return struct.unpack("!f", values)[0]


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
    return struct.unpack("!d", _hex_array_to_bytes(bytes_array, expected_length=8))[0]


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
    return _hex_array_to_bytes(bytes_array)


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
    if len(bytelist) != 4:
        raise ValueError("Expected exactly 4 bytes.")
    return int.from_bytes(bytes(int(value) for value in bytelist), "big")


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
    if len(bytelist) != 2:
        raise ValueError("Expected exactly 2 bytes.")
    return int.from_bytes(bytes(int(value) for value in bytelist), "big")


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
    return int.from_bytes(bytes(int(value) for value in bytelist), "big")


def _hex_array_to_bytes(values, expected_length=None):
    result = bytes(
        int(value, 16) if isinstance(value, str) else int(value) for value in values
    )
    if expected_length is not None and len(result) != expected_length:
        raise ValueError(f"Expected exactly {expected_length} bytes.")
    return result
