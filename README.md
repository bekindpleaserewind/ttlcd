# ttlcd
Linux controller for the Thermaltake LCD Panel Kit (Tower 200 Mini Chassis Model)

![Thermaltake LCD Panel Kit running ttlcd](https://raw.githubusercontent.com/bekindpleaserewind/ttlcd/main/contrib/ttlcd.jpg)

## Overview
Implementation (rough at that) of the Thermaltake LCD Panel API.  Currently CPU, RAM and Load Average widgets are built and can be displayed on a custom background.

Background images are streamed as fast as they can be processed (a few frames per second usually).  Supported resolution is 480x128.  File format is non progressive JPEGs via JFIF streams. See contrib/background.jpg for an example image.

## Usage
### Source
General source build instructions.

1. Install the pip modules by running ```pip install -r requirements.txt```. I recommend doing this in a python virtual environment dedicated to ttlcd.
2. If you wish to run as a user other than root, you'll need to provide access to the usb device via udev.  See the section "Permissions and USB Devices".
3. Create a config.yaml (based off etc/config.yaml.default) which suits your background image.
3. Execute ```python ttlcd.py -c <config>```.

## Permissions and USB Devices

See https://github.com/pyusb/pyusb/blob/master/docs/faq.rst#how-to-practically-deal-with-permission-issues-on-linux for further information on configuring udev rules for allowing unprivileged access to USB devices.

## Donations

If you are feeling nice today, I would be extremely greatful if you bought me a coffee on https://buymeacoffee.com/bekindpleaserewind
