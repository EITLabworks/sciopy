import struct

import numpy as np

from sciopy.datatype_conversion import (
    bytelist_to_int,
    byteintarray_to_float,
    bytesarray_to_double,
    bytesarray_to_float,
    del_hex_in_list,
    four_byte_to_int,
    two_byte_to_int,
)


def test_hex_list_is_normalized_to_two_digits():
    assert del_hex_in_list(["0x0", "0xa", "0xff", 1]).tolist() == [
        "00",
        "0a",
        "ff",
        "01",
    ]


def test_float_conversions_use_network_byte_order():
    float_bytes = struct.pack("!f", 12.5)
    double_bytes = struct.pack("!d", -0.125)

    assert byteintarray_to_float(float_bytes) == 12.5
    assert bytesarray_to_float([f"{value:02x}" for value in float_bytes]) == 12.5
    assert bytesarray_to_double([f"{value:02x}" for value in double_bytes]) == -0.125


def test_integer_conversions_include_every_byte():
    assert two_byte_to_int([0x12, 0x34]) == 0x1234
    assert four_byte_to_int([0x12, 0x34, 0x56, 0x78]) == 0x12345678
    assert bytelist_to_int([0x12, 0x34]) == 0x1234
    assert bytelist_to_int(np.array([0x12, 0x34, 0x56])) == 0x123456
