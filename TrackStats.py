################################################################################
#
# Track Statistics module for pocket1090
#
################################################################################

import json
import logging
import sys
import time


class TrackStats():
    """ #### TODO
    """
    def __init__(self):
        self.uidLastSeen = {}

        self.maxAltitude = -1
        self.minAltitude = sys.maxsize
        self.avgAltitude = 0

        self.maxSpeed = -1
        self.minSpeed = sys.maxsize
        self.avgSpeed = 0

        self.categoryCounts = {l: {str(n): 0 for n in range(8)} for l in list("ABCDE")}
        self.unkCategoryCount = 0

        self.minRSSI = 0
        self.maxRSSI = -sys.maxsize
        self.avgRSSI = 0

        self.minDistance = -1
        self.maxDistance = sys.maxsize
        self.avgDistance = 0

    def update(self, track):
        """ #### TODO
        """
        waitTime = (5 * 60) # haven't seen in five minutes
        if ((track.uniqueId not in self.uidLastSeen) or 
            ((track.uniqueId in self.uidLastSeen) and self.uidLastSeen[track.uniqueId] < (time.time() + waitTime))):
            self.uidLastSeen[track.uniqueId] = track.timestamp

        if isinstance(track.altitude, int):
            self.avgAltitude = (track.altitude / 2) + (self.avgAltitude / 2)
            self.maxAltitude = track.altitude if track.altitude > self.maxAltitude else self.maxAltitude
            self.minAltitude = track.altitude if track.altitude < self.minAltitude else self.minAltitude

        if isinstance(track.speed, float):
            self.avgSpeed = (track.speed / 2) + (self.avgSpeed / 2)
            self.maxSpeed = track.speed if track.speed > self.maxSpeed else self.maxSpeed
            self.minSpeed = track.speed if track.speed < self.minSpeed else self.minSpeed

        if track.category[0] in list("ABCDE"):
            self.categoryCounts[track.category[0]][track.category[1]] += 1
        elif track.category[0] == "?":
            self.unkCategoryCount += 1

    def getStats(self):
        """ #### TODO
        """
        print("UniqueIds:")
        json.dump(self.uidLastSeen, sys.stdout, indent=4, sort_keys=True)
        print("")

        print(f"Altitude: min={self.minAltitude}, max={self.maxAltitude}, avg={self.avgAltitude:.2f}")

        print(f"Ground Speed: min={self.minSpeed}, max={self.maxSpeed}, avg={self.avgSpeed:.2f}")

        print("Categories:")
        for a in list("ABCDE"):
            print (f"{a}: {self.categoryCounts[a]}")
        print("")

    #### TODO make histogram of categories seen
    #### TODO counts of unique Ids

