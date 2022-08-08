################################################################################
#
# Display module for pocket1090
#
################################################################################

import pygame
from pygame.locals import *

from __init__ import * #### FIXME


DEF_DISPLAY_WIDTH = 320
DEF_DISPLAY_HEIGHT = 320

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

        self.center = Coordinate((width / 2), (height / 2))
        self.rangeRings = {
            'mid': (((self.width / 8), "0.25nm"), ((self.width / 4), "0.5nm"), ((self.width / 2), "1.0nm"))
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

        self.selectRange(rangeName)
        self._initScreen()

    def _drawRings(self):
        """Draw the range rings with their labels
          #### TODO
        """
        for ring in self.range:
            pygame.draw.circle(self.surface, self.ringColor, (self.center.x, self.center.y), ring[0], 1)
            #### TODO add labels
            self.surface.blit(*self.texts[ring[1]])

    def _drawSelfSymbol(self):
        """Add device symbol in the center
        """
        delta = 10
        pygame.draw.line(self.surface, SELF_COLOR, (self.center.x, (self.center.y - delta)), (self.center.x, (self.center.y + delta)))
        pygame.draw.line(self.surface, SELF_COLOR, ((self.center.x - delta), self.center.y), ((self.center.x + delta), self.center.y))

    def _initScreen(self):
        """Clear the screen and draw the labeled range rings
          #### TODO
        """
        self.surface.fill(self.bgColor)
        self._drawSelfSymbol()
        self._drawRings()

    def rangeNames(self):
        """Return a list of the names of selectable ranges
          #### TODO
        """
        return self.rangeRings.keys()

    def selectRange(self, rangeName):
        """Select the scale of the display
          #### TODO
        """
        self.range = self.rangeRings[rangeName]
        #### TODO create text rects for labels
        self.texts = {}
        for ring in self.range:
            text = self.font.render(ring[1], True, self.fontColor, self.bgColor)
            textRect = text.get_rect()
            textRect.center = (160, (160 - ring[0] + (textRect.h / 2)))
            self.texts[ring[1]] = (text, textRect)

    def addTrack(self, track):
        """Add a track to the screen
          #### TODO
        """

    def render(self):
        """Render the screen
          #### TODO
        """
        pygame.display.flip()
