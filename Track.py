################################################################################
#
# Track module for pocket1090
#
################################################################################

from dataclasses import dataclass

from geopy import Point
from geopy import distance as geoDistance

from __init__ import * #### FIXME

#### TODO add 'alt_baro', 'geom_rate', 'squawk', and 'emergency' keys

TRACK_DEFS = {'hex': "unknown",
              'flight': "n/a",
              'alt_geom': None,
              'alt_baro': None,
              'gs': None,
              'track': None,
              'geom_rate': None,
              'category': "?",
              'lat': None,
              'lon': None,
              'squawk': "n/a",
              'seen_pos': None,
              'seen': None,
              'emergency': None,
              'rssi': None}
TRACK_KEYS = TRACK_DEFS.keys()


@dataclass
class TrackSpec():
    uniqueId: str           # hex: 24-bit ICAO id, six hex digits, non-ICAO addresses start with '~'
    flightNumber: str       # flight: callsign, the flight name or aircraft registration as 8 chars
    altitude: int           # alt_geom: geometric (GNSS / INS) altitude in feet referenced to the WGS84 ellipsoid
    baroAltitude: int       # alt_baro: barometric altitude in feet above sea level
    speed: float            # gs: ground speed in knots
    heading: float          # track: true track over ground in degrees (0-359)
    rate: int               # baro_rate: barometric rate of climb/descent in feet per minute
    category: str           # category: emitter category, identifies aircraft classes (values "A0"-"D7")
    lat: float              # lat: aircraft position in decimal degrees
    lon: float              # lon: aircraft position in decimal degrees
    squawk: int             # squawk: transponder code
    seenPos: float          # seen_pos: how many seconds before "now" the position was last updated
    seen: float             # seen: how many seconds before "now" a message was last received from this aircraft
    emergency: str          # emergency: 
    rssi: float             # rssi: recent average RSSI (in dbFS); this will always be negative
    timestamp: float        # when the aircraft.json file was written (in Unix epoch time)
    location: (float,float) # (lat, lon) tuple as a geopy Point object
    distance: float         # distance of aircraft from current position in Km
    azimuth: float          # direction from current position to aircraft in degrees (0-359)


class Track():
    @staticmethod
    def distanceAndAzimuth(startPt, endPt):
        """Calculate and return the distance and bearing between two points
          #### TODO
        """
        distance = geoDistance.distance(startPt, endPt).km

        startLat = math.radians(startPt.latitude)
        startLon = math.radians(startPt.longitude)
        endLat = math.radians(endPt.latitude)
        endLon = math.radians(endPt.longitude)

        deltaLon = endLon - startLon
        if abs(deltaLon) > math.pi:
            deltaLon = -(2.0 * math.pi - deltaLon) if deltaLon > 0.0 else (2.0 * math.pi + deltaLon)

        tanStart = math.tan((startLat / 2.0) + (math.pi / 4.0))
        tanEnd = math.tan((endLat / 2.0) + (math.pi / 4.0))
        deltaPhi = math.log(tanEnd / tanStart)
        azimuth = ((math.degrees(math.atan2(deltaLon, deltaPhi)) + 360.0) % 360.0)
        return distance, azimuth

    '''
    def get_bearing(lat1,lon1,lat2,lon2):
        dLon = lon2 - lon1;
        y = math.sin(dLon) * math.cos(lat2);
        x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon);
        brng = np.rad2deg(math.atan2(y, x));
        if brng < 0: brng+= 360
        return brng
    '''

    def __init__(self, timestamp, selfLocation, **kwargs):
        self.history = []
        self.currentTrack = None
        self.update(timestamp, selfLocation, **kwargs)

    def __repr__(self):
        s = f"uniqueId: "
        if self.uniqueId:
            s += f"{self.uniqueId: >7}"
        else:
            s += f"     ?"
        s += f", flightNumber: "
        if self.flightNumber:
            s += f"{self.flightNumber: <8}"
        else:
            s += f"       ?"
        s += f", altitude: "
        if self.altitude:
            s += f"{self.altitude: >6}"
        else:
            s += f"     ?"
        s += f", baroAltitude: "
        if self.baroAltitude:
            s += f"{self.baroAltitude: >6}"
        else:
            s += f"     ?"
        s += f", speed: "
        if self.speed:
            s += f"{self.speed:5.1f}"
        else:
            s += f"    ?"
        s += f", heading: "
        if self.heading:
            s += f"{self.heading:5.1f}"
        else:
            s += f"    ?"
        s += f", rate: "
        if self.rate:
            s += f"{self.rate:5}"
        else:
            s += f"    ?"
        s += f", category: "
        if self.category:
            s += f"{self.category: >2}"
        else:
            s += f" ?"
        s += f", lat: "
        if self.lat:
            s += f"{self.lat:3.6f}"
        else:
            s += f"         ?"
        s += f", lon: "
        if self.lon:
            s += f"{self.lon:3.6f}"
        else:
            s += f"         ?"
        s += f", squawk: "
        if self.squawk:
            s += f"{self.squawk:5}"
        else:
            s += f"         ?"
        s += f", seenPos: "
        if self.seenPos:
            s += f"{self.seenPos:4.1f}"
        else:
            s += f"   ?"
        s += f", seen: "
        if self.seen:
            s += f"{self.seen:4.1f}"
        else:
            s += f"   ?"
        s += f", rssi: "
        if self.rssi:
            s += f"{self.rssi:5.1f}"
        else:
            s += f"   ?"
        s += f", emergency: "
        if self.emergency:
            s += f"{self.emergency}"
        else:
            s += f"   ?"
        s += f", timestamp: {self.timestamp}"
        s += f", location: {self.location}"
        return s

    def update(self, timestamp, selfLocation, **kwargs):
        """#### TODO
        """
        self.uniqueId = kwargs.get('hex', TRACK_DEFS['hex'])
        self.flightNumber = kwargs.get('flight', TRACK_DEFS['flight'])
        self.altitude = kwargs.get('alt_geom', TRACK_DEFS['alt_geom'])
        self.baroAltitude = kwargs.get('alt_baro', TRACK_DEFS['alt_baro'])
        self.speed = kwargs.get('gs', TRACK_DEFS['gs'])
        self.heading = kwargs.get('track', TRACK_DEFS['track'])
        self.rate = kwargs.get('geom_rate', TRACK_DEFS['geom_rate'])
        self.category = kwargs.get('category', TRACK_DEFS['category'])
        self.lat = kwargs.get('lat', TRACK_DEFS['lat'])
        self.lon = kwargs.get('lon', TRACK_DEFS['lon'])
        self.squawk = kwargs.get('squawk', TRACK_DEFS['squawk'])
        self.seenPos = kwargs.get('seen_pos', TRACK_DEFS['seen_pos'])
        self.seen = kwargs.get('seen', TRACK_DEFS['seen'])
        self.rssi = kwargs.get('rssi', TRACK_DEFS['rssi'])
        self.emergency = kwargs.get('emergency', TRACK_DEFS['emergency'])
        self.timestamp = timestamp
        self.location = Point(self.lat, self.lon)
        self.distance, self.azimuth = Track.distanceAndAzimuth(selfLocation, self.location)

        if self.currentTrack:
            self.history.append(self.currentTrack)
        self.currentTrack = TrackSpec(self.uniqueId, self.flightNumber, self.altitude,
                                      self.baroAltitude, self.speed, self.heading,
                                      self.rate, self.category, self.lat, self.lon,
                                      self.squawk, self.seenPos, self.seen, self.rssi,
                                      self.emergency, self.timestamp, self.location,
                                      self.distance, self.azimuth)

    def currentTrack(self):
        """#### TODO
        """
        return self.currentTrack

    def getHistory(self, depth, collapse=True):
        """ #### TODO
          Return list of tuple of (location, distance, azimuth) in order from
            newest to oldest, up to the given depth (0 means none of them and
            None means all of them), skipping the current location and
            (optionally) collapsing identical sequential locations into one
            tuple.
        """
        if depth == 0:
            return []
        numPts = depth if depth < (len(self.history) - 1) else -1

        history = self.history[-2::-1]
        if numPts > 0:
            history = history[0:numPts]
        trails = [(t.location, t.distance, t.azimuth) for n,t in enumerate(history) if (((n < 1) or (t.location != history[n - 1].location)) or not collapse)]
        return trails[1:depth]
