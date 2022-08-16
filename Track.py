################################################################################
#
# Track module for pocket1090
#
################################################################################

from dataclasses import dataclass

from geopy import Point

from __init__ import * #### FIXME


TRACK_KEYS = ('hex', 'flight', 'alt_geom', 'gs', 'track', 'category', 'lat', 'lon', 'seen_pos', 'seen', 'rssi')
TRACK_DEFS = {'hex': "unknown", 'flight': "n/a", 'alt_geom': None, 'gs': None, 'track': None, 'category': "?", 'lat': None, 'lon': None, 'seen_pos': None, 'seen': None, 'rssi': None}


@dataclass
class TrackSpec():
    uniqueId: str       # hex: 24-bit ICAO id, six hex digits, non-ICAO addresses start with '~'
    flightNumber: str   # flight: callsign, the flight name or aircraft registration as 8 chars
    altitude: int       # alt_geom: geometric (GNSS / INS) altitude in feet referenced to the WGS84 ellipsoid
    speed: float        # gs: ground speed in knots
    heading: float        # track: true track over ground in degrees (0-359)
    category: str       # category: emitter category, identifies aircraft classes (values "A0"-"D7")
    lat: float          # lat: aircraft position in decimal degrees
    lon: float          # lon: aircraft position in decimal degrees
    seenPos: float      # seen_pos: how many seconds before "now" the position was last updated
    seen: float         # seen: how many seconds before "now" a message was last received from this aircraft
    rssi: float         # rssi: recent average RSSI (in dbFS); this will always be negative
    timestamp: float    # when the aircraft.json file was written (in Unix epoch time)
    location: (float,float) # (lat, lon) tuple as a geopy Point object


class Track():
    def __init__(self, timestamp, **kwargs):
        self.history = []
        self.currentTrack = None
        self.update(timestamp, **kwargs)

    def __repr__(self):
        s = f"uniqueId: {self.uniqueId}, flightNumber: {self.flightNumber}"
        s += f", altitude: {self.altitude}, speed: {self.speed}, heading: {self.heading}"
        s += f", category: {self.category}, lat: {self.lat}, lon: {self.lon}"
        s += f", seenPos: {self.seenPos}, seen: {self.seen}, rssi: {self.rssi}"
        return s

    def update(self, timestamp, **kwargs):
        """#### TODO
        """
        self.uniqueId = kwargs.get('hex', TRACK_DEFS['hex'])
        self.flightNumber = kwargs.get('flight', TRACK_DEFS['flight'])
        self.altitude = kwargs.get('alt_geom', TRACK_DEFS['alt_geom'])
        self.speed = kwargs.get('gs', TRACK_DEFS['gs'])
        self.heading = kwargs.get('track', TRACK_DEFS['track'])
        self.category = kwargs.get('category', TRACK_DEFS['category'])
        self.lat = kwargs.get('lat', TRACK_DEFS['lat'])
        self.lon = kwargs.get('lon', TRACK_DEFS['lon'])
        self.seenPos = kwargs.get('seen_pos', TRACK_DEFS['seen_pos'])
        self.seen = kwargs.get('seen', TRACK_DEFS['seen'])
        self.rssi = kwargs.get('rssi', TRACK_DEFS['rssi'])
        self.timestamp = timestamp
        self.location = Point(self.lat, self.lon)

        if self.currentTrack:
            self.history.append(self.currentTrack)
        self.currentTrack = TrackSpec(self.uniqueId, self.flightNumber, self.altitude,
                                      self.speed, self.heading, self.category, self.lat,
                                      self.lon, self.seenPos, self.seen, self.rssi,
                                      self.timestamp, self.location)

    def currentTrack(self):
        """#### TODO
        """
        return self.currentTrack

    def trackHistory(self):
        """#### TODO
        """
        return self.history
