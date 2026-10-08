<img src="https://raw.githubusercontent.com/EITLabworks/sciopy/develop/docs/_static/logo_sciopy.jpg" alt="Sciopy-logo" width="200"/>

This package offers the serial interface for communication with an EIT device from ScioSpec. Commands can be written serially and the system response can be read out. With the current version, it is possible to start and stop measurements with defined burst counts and to read out the measurement data. In addition, the measurement data is packed into a data class for better further processing.

## Installation

You can simply install the package via [`pip`](https://pypi.org/project/sciopy/).

```bash
pip install sciopy
```

### Windows: USB Driver Setup

USB FS:  
To communicate with the Sciospec instrument over USB FS on Windows, follow the Linux platform instructions, since they are the same.

USB HS:  
To communicate with the Sciospec instrument over USB (HS) on Windows, you must install the `libusb` driver.

> [!WARNING]
> Installing the `libusb` driver will prevent the Sciospec instrument from working with the official Sciospec software on the selected USB port (`HS`).
>
> After installation, the Sciospec software may no longer recognize the device on that port.  
>  _(This process has been tested, but not successfully. The understanding is based on the Sciospec documentation that installing the libusb driver should enable usage on Windows, but Python still has communication issues. Using USB HS on Windows is therefore not solved.)_
>
> To restore the original behavior, you will need to uninstall the driver manually.  
> _(This rollback process has not been fully tested.)_

### Linux/Unix Platforms

_Alternative_

Clone the repository, then create and activate the Conda environment:

```bash
conda create --file environment.yml
conda activate sciopy
pip install -e .
```

- FTDI Driver installation: https://www.ftdichip.com/old2020/Drivers/D2XX.htm

#### Install `libusb` using Zadig

1. Download and install Zadig:  
   https://zadig.akeo.ie/

2. Connect the Sciospec instrument to your computer.

3. Open Zadig and enable:
   Options → List All Devices

4. Select the correct Sciospec USB device from the list.

5. Install the driver:
   `libusb-win32 (v1.4.0.0)`

---

## Contact

If you have any ideas or other suggestions, please don't hesitate to contact me.

Email: jacob.thoenes@uni-rostock.de

> [!TIP]
> I developed and tested this package on an Ubuntu/Linux system. If you encounter errors or issues on other operating systems and find a solution, you are welcome to contribute it to this repository.
>
> Thank you!

---

## EIT frequency blocks and multiple injection patterns

The existing scalar frequency and `exc_freq_max` / `n_freq` / `freq_scale`
sweep configuration remain supported. To configure several sweeps or discrete
frequencies in one measurement, pass ordered `EitFrequencyBlock` objects:

```python
from sciopy import EitFrequencyBlock, EitMeasurementSetup

setup = EitMeasurementSetup(
    burst_count=2,
    n_el=16,
    exc_freq=[
        EitFrequencyBlock(1_000, 10_000, 10, "lin"),
        EitFrequencyBlock(10_000, 100_000, 20, "log"),
    ],
    framerate=2,
    amplitude=0.001,
    inj_skip=[0, 1],
    gain=1,
    adc_range=1,
)
# With a connected EIT device:
# device.SetMeasurementSetup(setup)
# data = device.StartStopMeasurement(return_as="pot_mat")
```

Do not combine block lists with the legacy sweep fields. Each injection skip
adds `n_el` excitation settings in the order given. Skip values must be distinct.
`SetMeasurementSetup` resets the device configuration before appending blocks
and injection pairs. Direct frequency-update calls append to the device stack;
use a complete setup to replace an earlier configuration.

For multiple frequencies, `pot_mat` has shape
`(frames, excitation settings, frequencies, channels)`. The example above
returns `(2, 32, 30, 16)` for two complete frames. A single frequency keeps the
existing `(frames, excitation settings, channels)` shape. Frame
`frequency_stgs` contains the configured frequencies **in Hz**, computed from
the requested blocks; these are not device readback or independently measured
frequencies. The wire frequency-row identifier is an index into that list.

Software tests verify command encoding and synthetic frame parsing. Physical
device validation is still required for each supported model and firmware.

Measurement reads tolerate transient empty USB reads and stop after the requested
number of complete frames, including saved frames deleted from RAM. The default
idle timeout is five seconds; slower measurements may require a larger
`idle_timeout_seconds` when calling `MessageParser.read_usb_till_timeout`.
Command-response reads retain their immediate empty-read timeout.
