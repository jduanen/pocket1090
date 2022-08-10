################################################################################
#
# Display module for pocket1090
#
################################################################################

from collections import namedtuple
from dataclasses import astuple
import logging

from geopy import Point
import pygame
from pygame.locals import *

from __init__ import * #### FIXME


DEF_DISPLAY_DIAMETER = 480

DEF_RANGE_NAME = "mid"
DEF_BACKGROUND_COLOR = (32, 32, 32)
DEF_RANGE_RING_COLOR = (255, 255, 0)
DEF_FONT_COLOR = (240, 0, 240)
FONT_SIZE = 10
SELF_COLOR = (255, 0, 0)
MAX_SYMBOL_SIZE = 5
TRACKED_CATEGORIES = ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "?")


Ring = namedtuple("Ring", "radius km")


class RadarDisplay():
    def __init__(self, diameter=DEF_DISPLAY_DIAMETER, rangeName=DEF_RANGE_NAME, bgColor=DEF_BACKGROUND_COLOR, ringColor=DEF_RANGE_RING_COLOR, fontColor=DEF_FONT_COLOR):
        #### TODO consider switching to **kwargs
        self.diameter = diameter
        self.bgColor = bgColor
        self.ringColor = ringColor
        self.fontColor = fontColor

        self.center = Coordinate((diameter / 2), (diameter / 2))
        self.rings = {
            'near': (Ring((self.diameter / 8), 0.25), Ring((self.diameter / 4), 0.5), Ring((self.diameter / 2), 1.0)),
            'mid': (Ring((self.diameter / 8), 1.0), Ring((self.diameter / 4), 2.0), Ring((self.diameter / 2), 4.0)),
            'far': (Ring((self.diameter / 8), 4.0), Ring((self.diameter / 4), 8.0), Ring((self.diameter / 2), 16.0)),
            'max': (Ring((self.diameter / 16), 4.0), Ring((self.diameter / 8), 8.0), Ring((self.diameter / 4), 16.0), Ring((self.diameter / 2), 32.0))
        }

        pygame.init()
        pygame.font.init()
        if False:
            #print(f"\nFonts: {pygame.font.get_fonts()}\n")
            print(f"\nFonts: {pygame.font.get_default_font()}\n")
        if False:
            print(f"\nDisplay: \n{pygame.display.Info()}\n{pygame.display.get_driver()} {pygame.display.list_modes()}\n")
        self.surface = pygame.display.set_mode((self.diameter, self.diameter), DOUBLEBUF)
        pygame.display.set_caption('Radar Display')
        self.font = pygame.font.Font('freesansbold.ttf', FONT_SIZE)

        self.rotation = 0
        self.selectRange(rangeName)
        self.selfSymbol = self._createSelfSymbol()
        self.symbols = self._createSymbols()

        self._initScreen()

    def _calcPixelAddr(self, selfLocation, trackLocation):
        """Map the given a location (lat,lon) calculate and return the screen
            position (x,y) for the current display size and range selection
          #### TODO
          assumes trackLocation isn't off the screen
        """
#        latDist = distance.distance(location, (track.latitude, location.longitude)).km
#        lonDist = distance.distance(location, (location.latitude, track.longitude)).km
        metersPerPixel = (self.rangeSpec[-1].km * 1000) / self.diameter
        dist, bearing = distanceBearing(selfLocation, trackLocation)
        print(f"Dist: {dist:.2f}, Bearing: {bearing:.2f}")
        distPx = (dist * 1000) / metersPerPixel
        x = (distPx * math.sin(math.radians(bearing))) + (self.diameter / 2)
        y = -(distPx * math.cos(math.radians(bearing))) + (self.diameter / 2)
        print(f"DistPx: {distPx}, X:{x}, Y:{y}")
        return (x, y)

    #### TODO if no speed, use min-length vector on symbol, come up with (display-size-independent) mapping from speed to vector length
    def _createSymbols(self):
        """Draw all symbols
          #### TODO
        """
        delta = MAX_SYMBOL_SIZE
        symbols = {}
        for cat in TRACKED_CATEGORIES:
            s = pygame.Surface((delta, delta))
            s.fill(self.bgColor)
            s.set_colorkey(self.bgColor)
            #### TODO load bitmaps from files
            pygame.draw.circle(s, (0, 240, 0), ((delta / 2), (delta / 2)), delta)
            symbols[cat] = s
        return symbols

    def _renderSymbol(self, selfLocation, trackLocation, symbolName, flight, altitude, speed, heading):
        """Render the named symbol at the given coordinate, with the appropriately sized speed and heading vector
          If symbolName is None, then use the unknown symbol
          If speed is None, use a min-length vector
          If heading is None, don't add a vector
          Add flightNumber and altitude as text next to the symbol if they exist, else use "-" character
        """
        #### TODO add speed vector
        #### TODO add text -- flight, altitude
        #### TODO create and use bitmap files for A[0-7] and ? categories
        #### TODO age symbols by changing alpha value with seen times ?
        s = self.symbols[symbolName]
        dist = distance.distance(selfLocation, trackLocation).km
        if dist > self.rangeSpec[-1].km:
            logging.info(f"Track '{flight}' out of range: {dist}")
            return
        position = self._calcPixelAddr(selfLocation, trackLocation)
        print(f"Render: {symbolName} @ {trackLocation} = {position}")
        self.surface.blit(s, position)

    def _createSelfSymbol(self):
        """Draw the device symbol onto the selfSymbol surface
        """
        delta = 10
        selfSymbol = pygame.Surface(((2 * delta), (2 * delta)))
        selfSymbol.fill(self.bgColor)
        selfSymbol.set_colorkey(self.bgColor)
        pygame.draw.line(selfSymbol, SELF_COLOR, (delta, 0), (delta, (2 * delta)))
        pygame.draw.line(selfSymbol, SELF_COLOR, ((0.75 * delta), delta), ((1.25 * delta) + 1, delta))
        pygame.draw.line(selfSymbol, SELF_COLOR, (delta, 0), ((0.5 * delta), (0.5 * delta)))
        pygame.draw.line(selfSymbol, SELF_COLOR, (delta, 0), ((1.5 * delta), (0.5 * delta)))
        return selfSymbol

    def _renderSelfSymbol(self):
        s = pygame.transform.rotate(self.selfSymbol, self.rotation)
        self.surface.blit(s, ((self.center.x - (s.get_width() / 2)),
                              (self.center.y - (s.get_height() / 2))))

    def _createRangeRings(self):
        """Draw the labeled range rings for the selected range onto the rangeRings surface
          #### TODO
        """
        rangeRings = pygame.Surface((self.diameter, self.diameter))
        rangeRings.fill(self.bgColor)
        rangeRings.set_colorkey(self.bgColor)
        for ring in self.rangeSpec:
            pygame.draw.circle(rangeRings, self.ringColor, astuple(self.center), ring.radius, 1)

            text = self.font.render(f"{ring.km}km", True, self.fontColor, self.bgColor)
            textRect = text.get_rect()
            textRect.center = (self.center.x, (self.center.y - ring.radius + (textRect.h / 2)))
            rangeRings.blit(text, textRect)
        return rangeRings

    def _renderRangeRings(self):
        """Render the range rings onto the display surface
          #### TODO
        """
        self.surface.blit(self.rangeRings, ((self.center.x - (self.rangeRings.get_width() / 2)),
                                            (self.center.y - (self.rangeRings.get_height() / 2))))

    def _initScreen(self):
        """Clear the screen and draw the static elements (i.e., range rings and self symbol)
          #### TODO
        """
        self.surface.fill(self.bgColor)
        self._renderSelfSymbol()
        self._renderRangeRings()

    def rangeNames(self):
        """Return a list of the names of selectable ranges
          #### TODO
        """
        return list(self.rings.keys())

    def selectRange(self, rangeName):
        """Select the scale of the display and create the associated labeled range rings
          #### TODO
        """
        self.rangeSpec = self.rings[rangeName]
        self.rangeRings = self._createRangeRings()

    def render(self, rotation, selfLocation, tracks):
        """Render the screen with the given rotation and location
          #### TODO
        """
        self.rotation = rotation
        self._initScreen()
        for uid, track in tracks.items():
            trackLocation = Point(track.lat, track.lon)
            print(f"Track {uid}: flight: {track.flightNumber} alt: {track.altitude}, speed: {track.speed}, dir: {track.heading}, cat: {track.category}")
            print(track)
            self._renderSymbol(selfLocation, trackLocation, track.category, track.flightNumber, track.altitude, track.speed, track.heading)
        pygame.display.flip()
