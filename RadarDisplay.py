################################################################################
#
# Display module for pocket1090
#
################################################################################

from geopy import distance
import logging

import pygame
from pygame.locals import *

from __init__ import * #### FIXME


DEF_DISPLAY_WIDTH = 480
DEF_DISPLAY_HEIGHT = 480

DEF_RANGE_NAME = "mid"
DEF_BACKGROUND_COLOR = (32, 32, 32)
DEF_RANGE_RING_COLOR = (255, 255, 0)
DEF_FONT_COLOR = (0, 240, 0)
FONT_SIZE = 10
SELF_COLOR = (255, 0, 0)


class RadarDisplay():
    def __init__(self, width=DEF_DISPLAY_WIDTH, height=DEF_DISPLAY_HEIGHT, rangeName=DEF_RANGE_NAME, bgColor=DEF_BACKGROUND_COLOR, ringColor=DEF_RANGE_RING_COLOR, fontColor=DEF_FONT_COLOR):
        #### TODO consider switching to **kwargs
        self.width = width
        self.height = height
        self.bgColor = bgColor
        self.ringColor = ringColor
        self.fontColor = fontColor

        self.center = ((width / 2), (height / 2))
        self.rings = {
            'near': (((self.width / 8), 0.25), ((self.width / 4), 0.5), ((self.width / 2), 1.0)),
            'mid': (((self.width / 8), 1.0), ((self.width / 4), 2.0), ((self.width / 2), 4.0)),
            'far': (((self.width / 8), 4.0), ((self.width / 4), 8.0), ((self.width / 2), 16.0)),
            'max': (((self.width / 16), 4.0), ((self.width / 8), 8.0), ((self.width / 4), 16.0), ((self.width / 2), 32.0))
        }

        pygame.init()
        pygame.font.init()
        if False:
            #print(f"\nFonts: {pygame.font.get_fonts()}\n")
            print(f"\nFonts: {pygame.font.get_default_font()}\n")
        if False:
            print(f"\nDisplay: \n{pygame.display.Info()}\n{pygame.display.get_driver()} {pygame.display.list_modes()}\n")
        self.surface = pygame.display.set_mode((self.width, self.height), DOUBLEBUF)
        pygame.display.set_caption('Radar Display')
        self.font = pygame.font.Font('freesansbold.ttf', FONT_SIZE)

        self.rotation = 0
        self.selectRange(rangeName)
        self.selfSymbol = self._createSelfSymbol()

        self._initScreen()

    #### TODO make screen coordinates (x,y) be Coordinate types, make Location dataclass and use for all (lat,lon) tuples

    #### FIXME precompute all symbols and render them and all the static info in north-up form then rotate everything rendering

    #### TODO if no speed, use min-length vector on symbol, come up with (display-size-independent) mapping from speed to vector length
    '''
    def _createSymbols(self):
        """Draw all symbols
        """

    def _renderSymbol(self, symbolName, coordinate, flight, altitude, speed, heading):
        """Render the named symbol at the given coordinate, with the appropriately sized speed and heading vector
          If symbolName is None, then use the unknown symbol
          If speed is None, use a min-length vector
          If heading is None, don't add a vector
          Add flightNumber and altitude as text next to the symbol if they exist, else use "-" character
        """
    '''

    def _createSelfSymbol(self):
        """Draw the device symbol onto the selfSymbol surface
        """
        delta = 10
        selfSymbol = pygame.Surface(((2 * delta), (2 * delta)))
        selfSymbol.fill(self.bgColor)
        selfSymbol.set_colorkey(self.bgColor)
        pygame.draw.line(selfSymbol, SELF_COLOR, (delta, 0), (delta, (2 * delta)))
        pygame.draw.line(selfSymbol, SELF_COLOR, (0, delta), ((2 * delta), delta))
        return selfSymbol

    def _renderSelfSymbol(self):
        s = pygame.transform.rotate(self.selfSymbol, self.rotation)
        self.surface.blit(s, ((self.center[0] - (s.get_width() / 2)),
                              (self.center[1] - (s.get_height() / 2))))

    def _createRangeRings(self):
        """Draw the labeled range rings for the selected range onto the rangeRings surface
          #### TODO
        """
        rangeRings = pygame.Surface((self.width, self.height))
        rangeRings.fill(self.bgColor)
        rangeRings.set_colorkey(self.bgColor)
        for ring in self.rangeSpec:
            pygame.draw.circle(rangeRings, self.ringColor, self.center, ring[0], 1)

            text = self.font.render(f"{ring[1]}km", True, self.fontColor, self.bgColor)
            textRect = text.get_rect()
            textRect.center = (self.center[0], (self.center[1] - ring[0] + (textRect.h / 2)))
            rangeRings.blit(text, textRect)
        return rangeRings

    def _renderRangeRings(self):
        """Render the range rings onto the display surface
          #### TODO
        """
        r = pygame.transform.rotate(self.rangeRings, self.rotation)
        self.surface.blit(r, ((self.center[0] - (r.get_width() / 2)),
                              (self.center[1] - (r.get_height() / 2))))

    def _initScreen(self):
        """Clear the screen and draw the static elements (i.e., range rings and self symbol)
          #### TODO
        """
        self.surface.fill(self.bgColor)
        self._renderSelfSymbol()
        self._renderRangeRings()

    '''
    def _calcPixelAddr(self, lat, lon):
        # map (lat,lon) to (x,y) for given display size and range selection
        return (x, y)
    '''

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

    def render(self, rotation, location, tracks):
        """Render the screen with the given rotation and location
          #### TODO
        """
        self.rotation = rotation
        self._initScreen()
        #### TODO add tracks
        for uid, track in tracks.items():
            dist = distance.distance(location, (track.lat, track.lon))
            if dist > self.rangeSpec[-1][1]:
                logging.info(f"Track '{uid}' out of range: {dist}")
#               continue
            latDist = distance.distance(location, (track.lat, location[1]))
            lonDist = distance.distance(location, (location[0], track.lon))
            print(f"Track {uid}: {dist}, {latDist}, {lonDist}")
            print(f"    alt: {track.altitude}, speed: {track.speed}, dir: {track.heading}, cat: {track.category}")
        pygame.display.flip()
