################################################################################
#
# GPS module for pocket1090
#
# N.B. Currently hardwired to this location
#
# TODO
#  * implement the interface to the chosen GPS module
#
################################################################################

from collections import deque
import logging
import time

from geopy import Point
from pynmeagps import NMEAReader
from serial import Serial


DEF_SERIAL_PORT = "/dev/ttyAMA0"
STREAM_BAUD_RATE = 9600
STREAM_TIMEOUT = 3

WARN_INTERVAL = 1000

MAX_FILTER_LEN = 30


class GPS():
    def __init__(self, serialPort=DEF_SERIAL_PORT, fixedLocation=None):
        self.serialPort = serialPort
        self.fixedLocation = fixedLocation
        if fixedLocation:
            if not isinstance(fixedLocation, Point):
                logging.error("The arg 'fixedLocation' must by of type 'Point'")
                raise RuntimeError("Invalid GPS arg type")
        else:
            self.stream = Serial(serialPort, baudrate=STREAM_BAUD_RATE, timeout=STREAM_TIMEOUT)
            self.nmr = NMEAReader(self.stream)
        self.lats = deque([], maxlen=MAX_FILTER_LEN)
        self.lons = deque([], maxlen=MAX_FILTER_LEN)

    def getTimeLocation(self, maxWaitTime=None):
        """#### TODO
        """
        if self.fixedLocation:
            return self.fixedLocation
        utcTime, lat, lon = None, None, None
        lastWarning = start = time.time()
        while None in (lat, lon, utcTime):
            _, parsedMsg = self.nmr.read()
            if parsedMsg is None:
                logging.warning("Invalid GPS read")
                continue
            now = time.time()
            if parsedMsg.msgID == "GGA":
                if parsedMsg.quality == 0:
                    if ((now - lastWarning) > WARN_INTERVAL):
                        logging.warning("GPS quality issue: invalid data")
                        lastWarning = now
                    continue
                lat = parsedMsg.lat
                lon = parsedMsg.lon
                utcTime = parsedMsg.time  #### FIXME make the be the right format
            if maxWaitTime and ((now - start) > maxWaitTime):
                logging.warning("Returned without GPS information")
                return None, None
            time.sleep(.1)
        self.lats.append(lat)
        self.lons.append(lon)
        return utcTime, Point(lat, lon)

    def getFilteredLocation(self, maxWaitTime=None):
        """ #### FIXME
        """
        time, loc = self.getTimeLocation(maxWaitTime)
        avgLat = sum(self.lats) / len(self.lats)
        avgLon = sum(self.lons) / len(self.lons)
        return time, Point(avgLat, avgLon)
