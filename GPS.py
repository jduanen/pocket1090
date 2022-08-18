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
    def __init__(self, fixedLocation=None):
        self.gpsd = gps(mode=(WATCH_ENABLE | WATCH_NEWSTYLE))
        if (fixedLocation and not isinstance(fixedLocation, Point)):
            logging.error("The arg 'fixedLocation' must by of type 'Point'")
            raise AssertionError("Invalid arg type")
        self.fixedLocation = fixedLocation

    def getTimeLocation(self, maxWaitTime=None):
        """#### TODO
        """
        if self.fixedLocation:
            return self.fixedLocation
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
        return utcTime, Point(lat, lon)
