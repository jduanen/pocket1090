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

import logging
import time

from geopy import Point
from gps import gps, WATCH_ENABLE, WATCH_NEWSTYLE


class GPS():
    def __init__(self):
        self.gpsd = gps(mode=(WATCH_ENABLE | WATCH_NEWSTYLE))
        self.sampleTime = None
        self.location = None

    def getTimeLocation(self, maxWaitTime=None):
        """#### TODO
        """
        utcTime = None
        lat = None
        lon = None
        start = time.time()
        while None in (lat, lon, utcTime):
            report = self.gpsd.next()
            if report['class'] == "TPV":
                lat = getattr(report, 'lat', None)
                lon = getattr(report, 'lon', None)
                utcTime = getattr(report, 'time', None)
            if maxWaitTime and ((time.time() - start) > maxWaitTime):
                logging.warning("Returned without GPS information")
                return None, None
            time.sleep(.1)
        self.sampleTime = utcTime
        self.location = Point(lat, lon)
        return self.sampleTime, self.location
