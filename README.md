<img src="https://raw.githubusercontent.com/EITLabworks/sciopy/develop/docs/_static/logo_sciopy.jpg" alt="Sciopy-logo" width="200"/>

This package offers the serial interface for communication with an EIT device from ScioSpec. Commands can be written serially and the system response can be read out. With the current version, it is possible to start and stop measurements with defined burst counts and to read out the measurement data. In addition, the measurement data is packed into a data class for better further processing.

**WIP** Communication with ISX-3

## Installation

### Preliminary Installation for Windows

You need libusb, to get it, install Zadig (https://zadig.akeo.ie/). 
Then Option/list all devices. Having the Sciospec instrument connected select the Right entry and install libusb-win32 (v1.4.0.0).  


### For all platforms

Clone the project.

Run

´´´
conda create --file environment.yml
conda activate sciopy
pip install -e .
´´´




## Contact

If you have any ideas or other suggestions, please don't hesitate to contact me.

Email: jacob.thoenes@uni-rostock.de
