"""A Python package for Sciospec device communication"""

from .com_util import (
    available_serial_ports,
)

from .EIT_16_32_64_128 import EIT_16_32_64_128, EitMeasurementSetup
from .ISX_3 import ISX_3, EisMeasurementSetup


__all__ = [
    "available_serial_ports",
    "EIT_16_32_64_128",
    "EitMeasurementSetup",
    "ISX_3",
    "EisMeasurementSetup",
]
