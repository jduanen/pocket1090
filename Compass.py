################################################################################
#
# Compass module for pocket1090
#
# N.B. Currently hardwired to always return true north
#
# TODO
#  * implement the interface to the chosen flux-gate magnetometer
#
################################################################################

from __init__ import * #### FIXME


class Compass():
    def __init__(self):
        self.azimuth = 0.0

    def getAzimuth(self):
        return self.azimuth
