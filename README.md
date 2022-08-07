# pocket1090
Handheld Air Traffic Monitor using the dump1090-fa 1.09GHz SDR-based ADS-B and Mode S/3A/3C decoder


## Automatic Dependent Surveillance-Broadcast (ADS-B) Notes
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


**WIP**

## Design Notes
* use dump1090-fa to emit json files, generate console display using matplotlib
* Main HW Components
  - LiPo battery, FlightAware Pro-Stick Plus, Raspi Zero, round LCD display with capacitive touchscreen and HDMI interface, external whip antenna, GPS receiver
* Display features:
  - annular rings indicating range (device is in the center)
  - selectable range (between some min/max values that make sense)
  - use NATO symbology? -- shape indicates type, vector indicates heading and speed, text for other values
  - touch icon to get additional info pop-up
    * e.g., squawk, emergency, altitude, RSSI, roll, category, nav mode, seen
* maybe a shaft-encoder or tiny joystick as additional input
* on-board LiPo charger and USB-C connection (power and RasPi interface)
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


