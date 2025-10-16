from dataclasses import dataclass
from typing import List, Tuple, Union


@dataclass
class EitMeasurementSetup:
    """
    Represents the setup parameters for Electrical Impedance Tomography (EIT) measurements.

    Attributes:
        burst_count (int): Number of bursts per measurement cycle.
        n_el (int): Number of electrodes used in the measurement.
        exc_freq (int or float): Excitation frequency in Hz.
        framerate (int or float): Frame rate of the measurement in Hz.
        amplitude (int or float): Amplitude of the excitation signal.
        inj_skip (int or list): Electrode(s) to skip during current injection.
        gain (int): Amplifier gain setting.
        adc_range (int): Analog-to-digital converter range setting.
    """

    burst_count: int
    n_el: int
    exc_freq: Union[int, float]
    framerate: Union[int, float]
    amplitude: Union[int, float]
    inj_skip: Union[int, list]
    gain: int
    adc_range: int
    # TBD: lin/log/sweep


@dataclass
class EisMeasurementSetup:
    """
    Represents the setup parameters for an Electrochemical Impedance Spectroscopy (EIS) measurement.

    Attributes:
        start (int | float): Start frequency in Hz (e.g., 500000 for 500kHz).
        stop (int | float): Stop frequency in Hz.
        step (int | float): Number of frequency steps.
        stepmode (str): Type of frequency distribution over the interval ('lin' for linear, 'log' for logarithmic).
        AVG (int | float): Number of averages taken per measurement.
        Amplitude (int | float): Amplitude of the excitation signal in mV.
        Precision (int): Desired precision configuration (≥0):
            - 1: Standard configuration (max relative deviation < 0.1%)
            - <1: Faster measurement, less precise
            - >1: More precise, slower measurement
        MeasurementTime (int | float): Duration of the measurement in seconds.

    Note:
        Additional parameters may include measurement channel settings and other hardware-specific configurations.
    """

    start: Union[int, float]  # min 100mHz
    stop: Union[int, float]  # max 10MHz
    step: Union[int, float]
    stepmode: str  # 'lin', 'log'
    avg: Union[int, float]
    amplitude: Union[int, float]
    precision: int
    measurement_time: Union[int, float]


@dataclass
class SingleFrame:
    """
    This class is for parsing single excitation stages.

    Parameters
    ----------
    start_tag : str
        has to be 'b4'
    channel_group : int
        channel group: CG=1 -> Channels 1-16, CG=2 -> Channels 17-32 up to CG=4
    excitation_stgs : List[str]
        excitation setting: [ESout, ESin]
    frequency_row : List[str]
        frequency row
    timestamp : int
        milli seconds
    ch_1 : complex
        complex value of channel 1
    ch_2 : complex
        complex value of channel 2
    ch_3 : complex
        complex value of channel 3
    ch_4 : complex
        complex value of channel 4
    ch_5 : complex
        complex value of channel 5
    ch_6 : complex
        complex value of channel 6
    ch_7 : complex
        complex value of channel 7
    ch_8 : complex
        complex value of channel 8
    ch_9 : complex
        complex value of channel 9
    ch_10 : complex
        complex value of channel 10
    ch_11 : complex
        complex value of channel 11
    ch_12 : complex
        complex value of channel 12
    ch_13 : complex
        complex value of channel 13
    ch_14 : complex
        complex value of channel 14
    ch_15 : complex
        complex value of channel 15
    ch_16 : complex
        complex value of channel 16
    end_tag : str
        has to be 'b4'
    """

    start_tag: str
    channel_group: int
    excitation_stgs: List[int]
    frequency_row: List[str]
    timestamp: int  # [ms]
    ch_1: complex
    ch_2: complex
    ch_3: complex
    ch_4: complex
    ch_5: complex
    ch_6: complex
    ch_7: complex
    ch_8: complex
    ch_9: complex
    ch_10: complex
    ch_11: complex
    ch_12: complex
    ch_13: complex
    ch_14: complex
    ch_15: complex
    ch_16: complex
    end_tag: str


@dataclass
class ScioSpecMeasurementConfig:
    """
    Measurement config of the current measurement.

    Parameters
    ----------
    com_port : str
        ScioSpec device com port
    burst_count : int
        total number of measurements between start and stop command
    n_el : int
        total number of injecting electrodes
    channel_group : list
        list of channel groups participating in the measurement
    actual_sample : int
        numbering of samples
    s_path : str
        savepath for the samples
    object : str
        selected measurement geometry
    size : float
        size of the object in percent relating the unit circle tank
    material : str
        material of the placed object
    saline_conductivity : Tuple[float, str]
        measured conductivity of the saline
    temperature : float
        temperature of the Ender 5 printing bed
    water_lvl : float
        water level inside the phantom tank
    exc_freq : float
        excitation signal frequency
    datetime : str
        ISO 8601: YYYY/MM/DD hh/mm/ss
    """

    com_port: str
    burst_count: int
    n_el: int
    channel_group: list
    actual_sample: int
    s_path: str
    object: str
    size: float
    material: str
    saline_conductivity: Tuple[float, str]
    temperature: float
    water_lvl: float
    exc_freq: float
    datetime: str


@dataclass
class SingleEitFrame:
    pass


# @dataclass
# class BaseSettingForEstimation:
#    active_channel_groups: np.ndarray
#    burst_count: int


@dataclass
class PreperationConfig:
    lpath: str
    spath: str
    n_samples: int
