# pocket1090
Handheld, standalone, network-free, air traffic monitoring application.
Uses the dump1090-fa 1.09GHz SDR-based ADS-B and Mode S/3A/3C decoder.

**WIP**

## Key Features
* Range
  - Automatic: automatically select smallest (power of two Km) range that includes all current tracks
  - Manual: increase/decrease range in powers of two Km distances
* Trails (i.e., position points)
  - show position point history
  - can select no points, all points, or just the last 'N' points
* Aging of Tracks
  - enable/disable fade-out with time since last seen
* Summary
  - list of current tracks, sorted by distance from receiver
  - includes: flight number, altitude, speed, direction, distance, azimuth, and category
* Details
  - popup with detailed information on selected track
  - all current information about the track
* Filters
  - inside/outside altitude/speed range
  - categories
  - flight number (prefix)
  - uniqueIds
  - greater-/less-than distance
  - heading

![Desktop Display 5](screen1.png)

## Interacting with the Application
* Command-line Arguments
  - *TBD*
* Touch Panel Inputs
  - *TBD*
* Keyboard Inputs
  - Left Arrow: reduce maximum number of trail points displayed
  - Right Arrow: increase maximum number of trail points displayed
  - Home: display no trail points
  - End: display all trail points
  - Up Arrow: increase the max distance to the next power of two Km
  - Down Arrow: decrease the max distance to the next power of two Km
  - 'a': auto-range -- enable auto-range mode
  - 'm': manual range -- disable auto-range mode
  - 'q': quit -- exit the application
  - 'h': print the keyboard inputs

## SW

### Raspberry Pi Zero 2W
* Set up for LCD Panel
  - install raspi os
  - edit /boot/config.txt
    * add to end of file
hdmi_group=2
hdmi_mode=87 
hdmi_timings=480 0 40 10 80 800 0 13 3 32 0 0 0 60 0 32000000 dtoverlay=ads7846,cs=1,penirq=25,penirq_pull=2,speed=50000,keep_vref_on=0,swapxy=0,pmax=255,xohms=150,xmin=200,xmax=3900,ymin=200,ymax=3900
hdmi_drive=1
hdmi_force_hotplug=1
  - setup xinput-calibrator
    * sudo apt-get install xserver-xorg-input-evdev xinput-calibrator

* Prepare SW Environment
  - update pygame
    * Ubuntu: pygame 2.1.2 (SDL 2.0.16, Python 3.8.10)
    * RasPi: pygame 2.0.0 (SDL 2.0.14, python 3.9.2)
  - install 2.x pygame
    * 'pip3 install pygame==2'
  - also install missing package:
    * 'sudo apt-get install libsdl2-image-2.0-0'
    * sudo cp -rf /usr/share/X11/xorg.conf.d/10-evdev.conf /usr/share/X11/xorg.conf.d/45-evdev.conf
    * edit conf file
      - sudo ex /usr/share/X11/xorg.conf.d/99-calibration.conf
      - add to file:
Section "InputClass"
        Identifier      "calibration"
        MatchProduct    "ADS7846 Touchscreen"
        Option  "Calibration"   "208 3905 288 3910"
        Option  "SwapAxes"      "0"
        Option "EmulateThirdButton" "1"
        Option "EmulateThirdButtonTimeout" "1000"
        Option "EmulateThirdButtonMoveThreshold" "300"
EndSection

### GPS Receiver
* Enable serial port without console
  - using 'sudo raspi-config'
* Configure and test serial port
  - 'stty -F /dev/serial0 raw 9600 cs8 clocal -cstopb'
  - 'cat /dev/serial0'
    * should get NMEA strings from GPS unit
* N.B.
  - Using $GPGGA NMEA messages to get orientation information
  - Doing simple filtering of lat/lon
    * Assuming device not near poles/equator (where discontinuities occur)
  - Not using gpsd to reduce background load on the CPU

### 9DoF IMU
* RasPi didn't handle I2C clock-stretching properly
  - seems to work fine with PiZero V2
* install Adafruit BNO055 library from PyPi
  - sudo pip3 install adafruit-bno055

### dump1090-fa
* set up environment
  - 'sudo apt-get install build-essential fakeroot debhelper librtlsdr-dev pkg-config libncurses5-dev libbladerf-dev libhackrf-dev liblimesuite-dev'
* clone dump1090-fa
  - 'git clone git@github.com:flightaware/dump1090.git'
* patch dump1090-fa to not write history files
  - e.g., as defined in dump1090.patch
* build modified dump1090-fa
  - './prepare-build.sh bullseye'
  - 'cd package-bullseye'
  - 'dpkg-buildpackage -b --no-sign'
* run dump1090-fa
  - '/home/jdn/Code2/dump1090/dump1090 --write-json /tmp/ > /tmp/fa.txt

### pocket1090
* set up environment
  - 'sudo apt install libsdl2-ttf-2*'
  - 'pip3 install -r requirements.txt'
* run pocket1090 application
  - './pocket1090.py -v /tmp -L INFO -f'
  - run in full-screen mode

### pocket1090.sh
* script to install, run, stop, get the status, and remove installation of pocket1090 application

### Screenshots
![Desktop Display 1](screen1.png)

![Desktop Display 2](screen2.png)

![Desktop Display 3](screen3.png)

![Desktop Display 4](screen4.png)

## HW

### Raspberry Pi Zero 2W
* https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/

### LCD Display
* https://www.waveshare.com/product/raspberry-pi/displays/4inch-hdmi-lcd.htm
* https://www.waveshare.com/wiki/4inch_HDMI_LCD
  - 4" 480x800 IPS LCD display
  - portrait-mode
  - 170 degree viewing angle
  - separate (micro-USB) power input for backlight
  - HDMI video input interface
  - resistive touch panel, XPT2046 controller
  - 3-/4-wire SPI interface to touch panel
  - 26pin dual-row connector
    * 1: 3.3V                   2: 5V
    * 3: SDA                    4: 5V
    * 5: SCL                    6: GND
    * 7: P7                     8: TX
    * 9: GND                   10: RX
    * 11: P0                   12: P1
    * 13: P2                   14: GND
    * 15: P3                   16: P4
    * 17: 3V3                  18: P5
    * 19: MOSI (TP SPI in)     20: GND
    * 21: MISO (TP SPI out)    22: P6 (TP IRQ)
    * 23: SCLK (TP SCLK)       24: CE0 (TP CS)
    * 25: GND                  26: CE1

### RTLSDI USB Dongle
* FlightAware Pro-Stick Plus: https://flightaware.store/products/pro-stick-plus
  - built-in 1090MHz bandpass filter
  - SMA F connector

### GPS Receiver
* https://www.adafruit.com/product/746
* GPS Receiver
  - 66 channel, 22 tracking
  - 10Hz updates, 34 secs warm/cold start
  - NMEA 0183, 9600 baud, 3V levels (5V tolerant)
  - PA1616S module, MTK3339
  - -165dBm sensitivity
  - 20mA
  - 3.3-5V input
  - battery-backed RTC, CR1220
  - Red Fix LED
    * blinks at ~1Hz while searching for satelites
    * blinks once every ~15 seconds when a fix is acheieved
  - PPS output
  - on-board patch antenna, u.FL connector
* pins
  - 3.3V (out)
  - ENB (in)
  - VBAT (in)
  - FIX (out)
  - TX (out)
  - RX (in)
  - GND
  - VIN (in)
  - PPS (out)
* RasPi Connection
  - GPIO 4:  ENB
  - GPIO 14: RX
  - GPIO 15: TX
  - 5V:      VIN
  - GND:     GND
  - GPIO 27: PPS

### 9DoF IMU
* https://www.adafruit.com/product/2472
* IMU
  - I2C interface, Address: 0x28, 10K pullups
    * might need 3.3K SCL and 2.2K SDA for 3.3V operation
  - auto-calibration
  - (black-box) sensor fusion
  - emits:
    * Euler Vector @ 100Hz
      - only use Euler Angles for pitch/roll < 45 degrees
    * Four Point Quaternion @ 100Hz
    * Angular Velocity Vector @ 100Hz
    * Accleration Vector @ 100Hz
    * Magnetic Field Strength Vector @ 20Hz
    * Linear Accleration Vector @ 100Hz
    * Gravity Vector @ 100Hz
    * Temperature @ 1Hz
  - N.B. highly sensitive to RF -- need to worry about placement/sheilding
* pins
  - VIN (in): 3-5V
  - 3VO (out): 3.3V output from regulator, < 50mA
  - GND
  - SCL (in): 3-5V, 10K pullup
  - SDA (bidir): 3-5V, 10K pullup
  - RST (in): reset on rising edge
  - P0: n/c
  - P1: n/c
  - INT (out): interrupt on motion, 3V
  - ADR (in): I2C address selection, 1=0x29, 0=0x28, 3V
* RasPi Connection
  - 3.3V:   VIN
  - GND:    GND
  - GPIO 2: SDA
  - GPIO 3: SCL
  - GPIO 5: DC

### Battery and Charger
*TBD*

### External antenna
*TBD*

------------------------------------------------------------------------------

## Notes

### Automatic Dependent Surveillance-Broadcast (ADS-B) Notes
* 1090MHz: Mode-A/C/S transponder
  - additional information (i.e., "extended squitter" message) aka 1090ES
  - aircraft flying above 18,000ft are required to have 1090ES
* 978MHz: Universal Access Transceiver (UAT)
  - aircraft flying above 18,000ft can have either UAT or 1090ES
* FLT ID: max of seven alphanumeric characters, same as id in ATC flight plan
  - commonly associated with airline and flight number (e.g., AAL3342)
  - for general aviation, its the aircraft's registration number
* ICAO address: 24b unique address, programmed at installation (like a MAC address?)
* in UAT Anonymous Mode, may not send ICAO address
* Unique Id starting with '~' means non-ICAO address -- e.g., TIS-B data coming from ground station?

#### Interesting Events Captured So Far
 * statistics
   - captured over four days
   - 52601 samples
   - 219 uniqueIds
* Categories
  - A[0-7]
  - B[1,2,4,6,7]
  - C[0-7]
  - D[1,2,7]
* Emergency/priority
  - no communications (7600)
  - lifeguard / medical emergency
* Groundspeed
  - min: 9.9 kt
  - max: 571.4 kt
* Baro altitude
  - min: -925 ft
  - max: 126700 ft
* RSSI
  - min: -20.3
  - max: -2.0

### Design Notes
* use dump1090-fa to emit json files, generate console display using pygame
* Display features:
  - concentric rings indicating range (device is in the center)
  - selectable range (between some min/max values that make sense)
  - use NATO symbology? -- shape indicates type, vector indicates heading and speed, text for other values
  - touch icon to get additional info pop-up
    * e.g., squawk, emergency, altitude, RSSI, roll, category, nav mode, seen, *_rate
  - age tracks by dimming them -- larger 'seen' value, the dimmer the track
* poll <path>/aircraft.json for data
* read <path>/receiver.json at startup to get receiver info (e.g., selected update rate)
* enable "track mode" where icon(s) leave slug trail behind?
* use color to indicate something interesting
  - e.g., emergency, special aircraft, really high/low/fast/slow/etc.
* use gps receiver to get location of device?
* use flux-gate magnetometer to get orientation?
  - select north is always up, or have the display reflect the device's current orientation
* use RasPi wifi to communicate with an external device (desktop, laptop, smartphone)
  - stream raw data
  - transfer history files
* save history files (with long save intervals)
  - enable offline analysis or replay of tracks
* set alarms -- things to watch for
  - e.g., specific planes, specific types of planes, specific metrics?
* switch to making auto-ranging the default
  - max range is always a power of two in Km
  - start with default range
  - after each polling cycle, determine max distance of all tracks, make max range be next higher power of two (in Km)
  - allow switching off autoRange (i.e., keep current range) and switching back on
  - turn off autoRange whenever range-up/down/reset/max command given
  - use last range or default range when no tracks available
* create different profiles for Handheld and Desktop uses -- do it all with config files
  - put screen size and where to get assets into config (use different sized symbols based on screen size)

## TODO
* Figure out what kind of input device to use -- e.g., track point, touchscreen, shaft-encoder
  - use touch panel -- figure out how to make it work on Ubuntu
* Add UTC clock display (from GPS)
* Add map overlays?
  - get map rectangles from https://openstreetmap.org
    * export image as .png file with Export button
    * define bounding box with min/max lat/lon values
      - fixed size (e.g., 64km on a side) from given center point?
  - load image with: myMap = plt.imread(<path>)
* Change radar display if held vertically or horizontally?
* Make sure all temp files are written to appropriate file system
* come up with simple way of defining filters
* indicate how many tracks are being filtered at any point in time?
* add text table for additional information
  - time (UTC) and location (lat/lon)
  - summary of current tracks: (flight number, category, altitude, speed, distance)
  - filtered tracks
  - details of selected track: (?)
* improve symbols
  - create different sized ones for different displays
  - use color and shape better
  - rotate (or not) properly

-----------------------------------------------------------------------------------------

* egrep RSSI /tmp/fa.txt | cut -d ":" -f 2 | cut -d " " -f 2 | awk '{cnt += 1; sum += $1} END {print "Avg RSSI: " sum/cnt " dBFS"}'
  - Avg RSSI: -10.8692 dBFS

  - install and use gpsd
    * sudo apt-get update; sudo apt-get install gpsd gpsd-clients
    * disable gpsd
      - sudo systemctl stop gpsd.socket
      - sudo systemctl disable gpsd.socket
    * manually start daemon
      - sudo gpsd /dev/serial0 -F /var/run/gpsd.sock
    * keep it running?
      - sudo systemctl enable gpsd.socket
      - sudo systemctl start gpsd.socket
  - run desktop client
    * sudo cgps -s
  - gpsd installs python package
    * from gps import *
  - can install adafruit-circuitpython-gps
    * import adafruit_gps
  --> running gpsd incurs a constant cpu load and so would rather just query on-demand
    * need to use library that works without gpsd
      - pip install adafruit-circuitpython-gps
      - pip install pynmeagps
      - from serial import Serial
        import adafruit_gps
        from pynmeagps import NMEAReader
        uart = Serial(port="/dev/ttyAMA0", baudrate=9600, timeout=30)
        gps = adafruit_gps.GPS(uart, debug=False)
        stream = Serial('/dev/ttyAMA0', baudrate=9600, timeout=3)
        nmr = NMEAReader(stream)
        (raw, parsed) = nmr.read()

* GPS
  - NMEA 0183 parsing
    * "$GPGGA,181908.00,3404.7041778,N,07044.3966270,W,4,13,1.00,495.144,M,29.200,M,0.10,0000*40"
      - $GPGGA: message with fix data
        *'GP' means GPS, 'GL' means GLONASS
      - MsgId:
        * VTG: Course over ground and ground speed
        * GSV: GPS Satellites in view
        * RMC: Recommended Minimum Specific GPS Data -- UTC time, status, latitude, longitude, speed over ground, date, magnetic variation of position
        * GSA: GPS DOP and Active Satellites
        * GGA: GPS Fix Data
          - UTC of position fix in HHMMMSS.SS format
          - Latitude in DD MM,MMMM format (0-7 decimal places)
          - direction of latitude: 'N', 'S'
          - Longitude in DD MM,MMMM format (0-7 decimal places)
          - direction of longitude: 'E', 'W'
          - GPS Quality indicator:
            * 0: invalid
            * 1: GPS fix
            * 2: DGPS fix
            * 3: ?
            * 4: real-time kinematic, fixed integers
            * 5: real-time kinematic, float integers
          - Number of SVs in use: [00-12]
          - HDOP
          - Antenna height -- MSL reference
          - "M": meters
          - Geoidal separation
          - "M" indicates the Geoidal separation is in meters
          - Correction age of the GPS data record: Null when not using DGPS
          - Base Station ID: [0000-1023]
        * RMC: Minimum GPS Data
          - UTC of position fix in HHMMMSS.SS format
          - Status: 'A'=valid, 'V'=invalid
          - Latitude coordinate (0-7 decimal places)
          - Latitude direction: 'N', 'S'
          - Longitude coordinate (0-7 decimal places)
          - Longitude direction: 'E', 'W'
          - Speed over Ground in knots (0-3 decimal places)
          - Track Made Good, True, in degrees
          - Date in dd/mm/yy format
          - Magnetic variation in degrees
    * looks like I receive as many RMC and GGA messages, so I'll use the GGA messages
      while True:
        _, p = nmr.read()
        if p.msgID == "GGA":
    * filter (lat,lon) samples (assuming not near poles/equator/where discontinuities occur)
      - look at set of samples
        * import matplotlib.pyplot as plt
          plt.scatter(x=lat,y=lon)
          avgLat = sum(lats)/len(lats)
          avgLon = sum(lons)/len(lons)
          plt.plot(avgLat, avgLon, marker="x")
          plt.show()
      - ????

* IMU
  - set up I2C for IMU
    * I2C HW: SCL=3, SDA=2
    * Raspi doesn't do I2C clock stretching properly so have to do something else
      - could switch and use the IMU in serial mode (with the second HW UART?)
    * replace i2c device with bit-banging driver (using same pins) via device tree overlay
      - sudo raspi-config
      - Interfaces->I2C -- disable ('<NO>')
      - sudo cp /boot/config.txt /boot/config.txt.orig
      - sudo ex /boot/config.txt
        * add: dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=02,i2c_gpio_scl=03
      - reboot and "ls -l /dev/i2c*" look for /dev/i2c-3
        * crw-rw---- 1 root i2c 89,  3 Dec 1 18:30 /dev/i2c-3
      - verify with: i2cdetect -y -r 3
        * should show BNO055 at address 28
    * alternatively use second HW UART and strap BNO055 to use serial (instead of I2C)
  - sudo pip3 install Adafruit-Blinka
    import board
    import busio
    i2c = busio.I2C(board.SCL, board.SDA)

  - sudo pip3 install adafruit-bno055
  - from Adafruit_BNO055 import BNO055
    bno = BNO055.BNO055(address=0x28, i2c="/dev/i2c-3", rst=5)
    if not bno.begin():
      print("ERROR: failed to init")
  - consider getting this: http://gps-pie.com/L80_slice.htm
