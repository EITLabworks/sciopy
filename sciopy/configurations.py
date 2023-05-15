# TBD: https://stackoverflow.com/questions/3898572/what-are-the-most-common-python-docstring-formats
from .sciopy_dataclasses import ScioSpecMeasurementConfig
from datetime import datetime


def conf_n_el_16_adjacent(
    serial, cnf: ScioSpecMeasurementConfig
) -> ScioSpecMeasurementConfig:
    """
    Amplitude 	1 mA
    Framerate 	10
    Burst Count 10 (cnf)
    Range 		+/-5V
    Gain 		1
    Min/Max f 	10.000	Steps 1	Scale LINEAR

    Numb of ing.16
    Skip 		0
    Channel Group 	1 (Inject+ : 1, Inject- : 1)
    Switch Type 	Reed Relays
    """

    serial.write(bytearray([0xB0, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x02, 0x00, hex(cnf.burst_count), 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x09,
                0x05,
                0x3F,
                0x50,
                0x62,
                0x4D,
                0xD2,
                0xF1,
                0xA9,
                0xFC,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x02, 0x0D, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x09, 0x01, 0x00, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x05, 0x03, 0x41, 0x20, 0x00, 0x00, 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x0C,
                0x04,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x00,
                0x01,
                0x00,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x01, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x02, 0x03, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x03, 0x04, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x04, 0x05, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x05, 0x06, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x06, 0x07, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x07, 0x08, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x08, 0x09, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x09, 0x0A, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0A, 0x0B, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0B, 0x0C, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0C, 0x0D, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0D, 0x0E, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0E, 0x0F, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0F, 0x10, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x10, 0x01, 0xB0]))
    serial.write(bytearray([0xB1, 0x01, 0x03, 0xB1]))
    serial.write(bytearray([0xB2, 0x02, 0x01, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x03, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x02, 0x01, 0xB2]))
    serial.write(bytearray([0xB4, 0x01, 0x01, 0xB4]))
    serial.write(bytearray([0xB4, 0x01, 0x00, 0xB4]))
    return ScioSpecMeasurementConfig(
        com_port=serial.name,
        burst_count=cnf.burst_count,
        n_el=16,
        channel_group=[1],
        actual_sample=cnf.actual_sample,
        s_path=cnf.s_path,
        object=cnf.object,
        size=cnf.size,
        material=cnf.material,
        saline_conductivity=cnf.saline_conductivity,
        temperature=cnf.temperature,
        water_lvl=cnf.water_lvl,
        exc_freq=10000.0,
        datetime=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    )


def conf_n_el_16_opposite(
    serial, cnf: ScioSpecMeasurementConfig
) -> ScioSpecMeasurementConfig:
    """
    Amplitude 	1 mA
    Framerate 	10
    Burst Count 10 (cnf)
    Range 		+/-5V
    Gain 		1
    Min/Max f 	10.000	Steps 1	Scale LINEAR

    Numb of ing.16
    Skip 		8
    Channel Group 	1 (Inject+ : 1, Inject- : 9)
    Switch Type 	Reed Relays
    """
    serial.write(bytearray([0xB0, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x02, 0x00, hex(cnf.burst_count), 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x09,
                0x05,
                0x3F,
                0x50,
                0x62,
                0x4D,
                0xD2,
                0xF1,
                0xA9,
                0xFC,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x02, 0x0D, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x09, 0x01, 0x00, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x05, 0x03, 0x41, 0x20, 0x00, 0x00, 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x0C,
                0x04,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x00,
                0x01,
                0x00,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x01, 0x09, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x02, 0x0A, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x03, 0x0B, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x04, 0x0C, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x05, 0x0D, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x06, 0x0E, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x07, 0x0F, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x08, 0x10, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x09, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0A, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0B, 0x03, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0C, 0x04, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0D, 0x05, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0E, 0x06, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0F, 0x07, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x10, 0x08, 0xB0]))
    serial.write(bytearray([0xB1, 0x01, 0x03, 0xB1]))
    serial.write(bytearray([0xB2, 0x02, 0x01, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x03, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x02, 0x01, 0xB2]))
    serial.write(bytearray([0xB4, 0x01, 0x01, 0xB4]))
    serial.write(bytearray([0xB4, 0x01, 0x00, 0xB4]))
    return ScioSpecMeasurementConfig(
        serial.name,
        burst_count=cnf.burst_count,
        n_el=16,
        channel_group=[1],
        actual_sample=cnf.actual_sample,
        s_path=cnf.s_path,
        object=cnf.object,
        size=cnf.size,
        material=cnf.material,
        saline_conductivity=cnf.saline_conductivity,
        temperature=cnf.temperature,
        water_lvl=cnf.water_lvl,
        exc_freq=10000.0,
        datetime=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    )


def conf_n_el_32_adjacent(
    serial, cnf: ScioSpecMeasurementConfig
) -> ScioSpecMeasurementConfig:
    """
    Amplitude 	1 mA
    Framerate 	10
    Burst Count 1 (pay attention to maximal buffer size)
    Range 		+/-5V
    Gain 		1
    Min/Max f 	10.000	Steps 1	Scale LINEAR

    Numb of ing.32
    Skip 		0
    Channel Group 	1 (Inject+ : 1, Inject- : 2)
    Switch Type 	Reed Relays
    """
    serial.write(bytearray([0xB0, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x02, 0x00, hex(cnf.burst_count), 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x09,
                0x05,
                0x3F,
                0x50,
                0x62,
                0x4D,
                0xD2,
                0xF1,
                0xA9,
                0xFC,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x02, 0x0D, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x09, 0x01, 0x00, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x05, 0x03, 0x41, 0x20, 0x00, 0x00, 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x0C,
                0x04,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x00,
                0x01,
                0x00,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x01, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x02, 0x03, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x03, 0x04, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x04, 0x05, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x05, 0x06, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x06, 0x07, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x07, 0x08, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x08, 0x09, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x09, 0x0A, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0A, 0x0B, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0B, 0x0C, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0C, 0x0D, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0D, 0x0E, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0E, 0x0F, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0F, 0x10, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x10, 0x11, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x11, 0x12, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x12, 0x13, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x13, 0x14, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x14, 0x15, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x15, 0x16, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x16, 0x17, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x17, 0x18, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x18, 0x19, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x19, 0x1A, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1A, 0x1B, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1B, 0x1C, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1C, 0x1D, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1D, 0x1E, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1E, 0x1F, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1F, 0x20, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x20, 0x01, 0xB0]))
    serial.write(bytearray([0xB1, 0x01, 0x03, 0xB1]))
    serial.write(bytearray([0xB2, 0x02, 0x01, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x03, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x02, 0x01, 0xB2]))
    serial.write(bytearray([0xB4, 0x01, 0x01, 0xB4]))
    serial.write(bytearray([0xB4, 0x01, 0x00, 0xB4]))
    return ScioSpecMeasurementConfig(
        serial.name,
        burst_count=cnf.burst_count,
        n_el=32,
        channel_group=[1, 2],
        actual_sample=cnf.actual_sample,
        s_path=cnf.s_path,
        object=cnf.object,
        size=cnf.size,
        material=cnf.material,
        saline_conductivity=cnf.saline_conductivity,
        temperature=cnf.temperature,
        water_lvl=cnf.water_lvl,
        exc_freq=10000.0,
        datetime=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    )


def conf_n_el_32_opposite(
    serial, cnf: ScioSpecMeasurementConfig
) -> ScioSpecMeasurementConfig:
    """
    Amplitude 	1 mA
    Framerate 	10
    Burst Count 1 (pay attention to maximal buffer size)
    Range 		+/-5V
    Gain 		1
    Min/Max f 	10.000	Steps 1	Scale LINEAR

    Numb of ing. 	32
    Skip 		16
    Channel Group 	1 (Inject+ : 1, Inject- : 17)
    Switch Type 	Reed Relays
    """
    serial.write(bytearray([0xB0, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x02, 0x00, 0x01, 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x09,
                0x05,
                0x3F,
                0x50,
                0x62,
                0x4D,
                0xD2,
                0xF1,
                0xA9,
                0xFC,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x02, 0x0D, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x09, 0x01, 0x00, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x08, 0x01, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x02, 0x0C, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x05, 0x03, 0x41, 0x20, 0x00, 0x00, 0xB0]))
    serial.write(
        bytearray(
            [
                0xB0,
                0x0C,
                0x04,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x46,
                0x1C,
                0x40,
                0x00,
                0x00,
                0x01,
                0x00,
                0xB0,
            ]
        )
    )
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x01, 0x11, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x02, 0x12, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x03, 0x13, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x04, 0x14, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x05, 0x15, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x06, 0x16, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x07, 0x17, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x08, 0x18, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x09, 0x19, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0A, 0x1A, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0B, 0x1B, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0C, 0x1C, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0D, 0x1D, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0E, 0x1E, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x0F, 0x1F, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x10, 0x20, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x11, 0x01, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x12, 0x02, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x13, 0x03, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x14, 0x04, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x15, 0x05, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x16, 0x06, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x17, 0x07, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x18, 0x08, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x19, 0x09, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1A, 0x0A, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1B, 0x0B, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1C, 0x0C, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1D, 0x0D, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1E, 0x0E, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x1F, 0x0F, 0xB0]))
    serial.write(bytearray([0xB0, 0x03, 0x06, 0x20, 0x10, 0xB0]))
    serial.write(bytearray([0xB1, 0x01, 0x03, 0xB1]))
    serial.write(bytearray([0xB2, 0x02, 0x01, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x03, 0x01, 0xB2]))
    serial.write(bytearray([0xB2, 0x02, 0x02, 0x01, 0xB2]))
    serial.write(bytearray([0xB4, 0x01, 0x01, 0xB4]))
    serial.write(bytearray([0xB4, 0x01, 0x00, 0xB4]))
    return ScioSpecMeasurementConfig(
        serial.name,
        burst_count=1,
        n_el=32,
        channel_group=[1, 2],
        actual_sample=cnf.actual_sample,
        s_path=cnf.s_path,
        object=cnf.object,
        size=cnf.size,
        material=cnf.material,
        saline_conductivity=cnf.saline_conductivity,
        temperature=cnf.temperature,
        water_lvl=cnf.water_lvl,
        exc_freq=10000.0,
        datetime=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
    )
