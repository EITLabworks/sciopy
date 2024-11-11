try:
    import serial
except ImportError:
    print("Could not import module: serial")

from sciopy import (
    StartStopMeasurement_usb_hs,
    del_hex_in_list,
    reshape_full_message_in_bursts,
    split_bursts_in_frames,
)

from sciopy.sciopy_dataclasses import EitMeasurementSetup


def sciospec_measurement(COM_Sciospec, ssms: EitMeasurementSetup) -> None:
    measurement_data_hex = StartStopMeasurement_usb_hs(COM_Sciospec)
    measurement_data = del_hex_in_list(measurement_data_hex)
    split_measurement_data = reshape_full_message_in_bursts(measurement_data, ssms)
    measurement_data = split_bursts_in_frames(split_measurement_data, ssms)
    return measurement_data
