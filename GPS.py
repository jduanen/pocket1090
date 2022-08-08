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

from __init__ import * #### FIXME


class GPS():
    def __init__(self):
        self.location = Coordinate()

    def getLocation(self):
        return self.location
