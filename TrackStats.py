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
      N.B. The averages are trailing exponential averages
    """
    def __init__(self):
        self.resetStats()

    def resetStats(self):
        """ #### TODO
        """
        self.uids = set([])

        self.maxAltitude = -1
        self.minAltitude = sys.maxsize
        self.avgAltitude = 0

        self.maxRate = -1
        self.minRate = sys.maxsize
        self.avgRate = 0

        self.maxSpeed = -1
        self.minSpeed = sys.maxsize
        self.avgSpeed = 0

        self.categoryCounts = {l: {str(n): 0 for n in range(8)} for l in list("ABCDE")}
        self.unkCategoryCount = 0

        self.maxRSSI = -sys.maxsize
        self.minRSSI = 0
        self.avgRSSI = 0

        self.maxDistance = -1
        self.minDistance = sys.maxsize
        self.avgDistance = 0

    def update(self, track):
        """ #### TODO
        """
        self.uids.add(track.uniqueId)

        if isinstance(track.altitude, int):
            self.avgAltitude = (track.altitude / 2) + (self.avgAltitude / 2)
            self.maxAltitude = track.altitude if track.altitude > self.maxAltitude else self.maxAltitude
            self.minAltitude = track.altitude if track.altitude < self.minAltitude else self.minAltitude

        rate = None
        if isinstance(track.geomRate, int):
            rate = track.geomRate
        elif isinstance(track.baroRate, int):
            rate = track.baroRate
        if rate is not None:
            self.avgRate = (rate / 2) + (self.avgRate / 2)
            self.maxRate = rate if rate > self.maxRate else self.maxRate
            self.minRate = rate if rate < self.minRate else self.minRate

        if isinstance(track.speed, float):
            self.avgSpeed = (track.speed / 2) + (self.avgSpeed / 2)
            self.maxSpeed = track.speed if track.speed > self.maxSpeed else self.maxSpeed
            self.minSpeed = track.speed if track.speed < self.minSpeed else self.minSpeed

        if isinstance(track.distance, float):
            self.avgDistance = (track.distance / 2) + (self.avgDistance / 2)
            self.maxDistance = track.distance if track.distance > self.maxDistance else self.maxDistance
            self.minDistance = track.distance if track.distance < self.minDistance else self.minDistance

        if track.category[0] in list("ABCDE"):
            self.categoryCounts[track.category[0]][track.category[1]] += 1
        elif track.category[0] == "?":
            self.unkCategoryCount += 1

        if isinstance(track.rssi, float):
            self.avgRSSI = (track.rssi / 2) + (self.avgRSSI / 2)
            self.maxRSSI = track.rssi if track.rssi > self.maxRSSI else self.maxRSSI
            self.minRSSI = track.rssi if track.rssi < self.minRSSI else self.minRSSI

    def printStats(self):
        """ #### TODO
        """
        print(f"Number of UniqueIds: {len(self.uids)}")
        print(f"Altitude: min={self.minAltitude}, max={self.maxAltitude}, avg={self.avgAltitude:.2f}")
        print(f"Rate:     min={self.minRate}, max={self.maxRate}, avg={self.avgRate:.2f}")
        print(f"Speed:    min={self.minSpeed}, max={self.maxSpeed}, avg={self.avgSpeed:.2f}")
        print(f"Distance: min={self.minDistance:.2f}, max={self.maxDistance:.2f}, avg={self.avgDistance:.2f}")
        print(f"RSSI:     min={self.minRSSI}, max={self.maxRSSI}, avg={self.avgRSSI:.2f}")
        print("Categories:")
        for a in list("ABCDE"):
            print (f"{a}: {self.categoryCounts[a]}")
        print("")

    #### TODO make histogram of categories seen

