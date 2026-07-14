<img src="https://raw.githubusercontent.com/EITLabworks/sciopy/develop/docs/_static/logo_sciopy.jpg" alt="Sciopy-logo" width="200"/>

This package offers the serial interface for communication with an EIT device from ScioSpec. Commands can be written serially and the system response can be read out. With the current version, it is possible to start and stop measurements with defined burst counts and to read out the measurement data. In addition, the measurement data is packed into a data class for better further processing.

## Installation

### Windows: USB Driver Setup

To communicate with the Sciospec instrument over USB on Windows, you must install the `libusb` driver.

> [!WARNING]
> Installing the `libusb` driver will prevent the Sciospec instrument from working with the official Sciospec software on the selected USB port (`FS` or `HS`).
>
> After installation, the Sciospec software may no longer recognize the device on that port.
>
> To restore the original behavior, you will need to uninstall the driver manually.  
> *(This rollback process has not been fully tested.)*


### Linux/Unix Platforms

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

___

