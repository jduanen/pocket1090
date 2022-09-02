#!/bin/bash
#
# Setup/install script for pocket1090
#
#### WIP -- don't run this yet

# Set up Raspi OS and HW base
# * Install Raspbian Bullseye
#   - use 'rpi-imager' on external host
#	  * set hostname, locale, and user, enable SSH

# * Update OS
sudo apt update
sudo apt upgrade

# * Update Firmware to 5.15.56+ in order to fix HDMI issue (should be fixed in future releases)
## sudo rpi-update

# * Enable SPI, I2C, and UART (no console) interfaces 
raspi-config

# * Disable audio
sudo ex /boot/config.txt
#   - add ",noaudio" to the end of "dtoverlay=vc4-kms-v3d"
#   - comment out "dtparam=audio=on"
sudo apt-get purge pulseaudio


# Set up for add-in HW
# * 4" HDMI LCD with Resistive Touch Screen (Waveshare)
#   - ensure that /boot/config.txt contains:
#     dtparam=i2c_arm=on
#     dtparam=spi=on
#     dtoverlay=vc4-kms-v3d
#   - add to end of /boot/config.txt
sudo cat - >> /boot/config.txt
dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900

#  - install SW to calibrate touchpanel
sudo apt-get install xserver-xorg-input-evdev xinput-calibrator
sudo cp -rf /usr/share/X11/xorg.conf.d/10-evdev.conf /usr/share/X11/xorg.conf.d/45-evdev.conf
sudo cat - >> /usr/share/X11/xorg.conf.d/99-calibration.conf
Section "InputClass"
        Identifier      "calibration"
        MatchProduct    "ADS7846 Touchscreen"
        Option  "Calibration"   "208 3905 288 3910"
        Option  "SwapAxes"      "0"
        Option "EmulateThirdButton" "1"
        Option "EmulateThirdButtonTimeout" "1000"
        Option "EmulateThirdButtonMoveThreshold" "300"
EndSection

# * RTL_SDR Receiver (Flightaware)
#   - find vendor and product Id for the dongle
lsusb | egrep RTL

#   - create rules file to set permissions/group
#### FIXME
##sudo cat - >> /etc/udev/rules.d/50.rtlsdr.rules
##SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", GROUP="users", MODE="0666"

# * GPS Receiver (Adafruit MTK3339)
#   - enable serial port for first UART, with no console running on it
sudo raspi-config

#   - configure serial port
sudo stty -F /dev/serial0 raw 9600 cs8 clocal -cstopb

#   - test to make sure NMEA strings are coming from the GPS unit
cat /dev/serial0

# * 9DoF IMU (Adafruit BNO055)
#   - install Adafruit BNO055 library
sudo pip3 install adafruit-bno055


# Set up the dump1090 server
# * prepare the environment
sudo apt-get install build-essential fakeroot debhelper librtlsdr-dev pkg-config libncurses5-dev libbladerf-dev libhackrf-dev liblimesuite-dev

# * make the Code2 directory and install the repo
mkdir ${HOME}/Code2
cd ${HOME}/Code2
git clone git@github.com:flightaware/dump1090.git

# * patch the dump1090 server to not write history files
cd dump1090
#### FIXME
## patch dump1090.patch

# * build the modified dump1090 server
./prepare-build.sh bullseye
cd package-bullseye
dpkg-buildpackage -b --no-sign


# Set up the pocket1090 application
# * make the Code directory and install the repo
mkdir ${HOME}/Code
cd ${HOME}/Code
git clone https://github.com/jduanen/pocket1090.git

# * prepare the environment
cd pocket1090
pip3 install pygame==2.1
sudo apt install libsdl-gfx1.2-5 libsdl-image1.2 libsdl-kitchensink1 libsdl-mixer1.2 libsdl-sound1.2 libsdl-ttf2.0-0 libsdl1.2debian libsdl2-2.0-0 libsdl2-gfx-1.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0
pip3 install -r requirements.txt

# * install the application and supporting files
./pocket1090.sh install


# Configure systemd to run the dump1090 server and pocket1090 application on boot and restart on failure
# * install service files and set their permissions
##sudo cp ./{dump,pocket}1090.service /lib/systemd/system
##sudo chmod 0644 /lib/systemd/system/{dump,pocket}1090.service
##sudo systemctl daemon-reload
##sudo systemctl start dump1090.service
##sudo systemctl enable dump1090.service
##sudo systemctl start pocket1090.service
##sudo systemctl enable pocket1090.service

# Reboot
sudo reboot
