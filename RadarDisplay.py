################################################################################
#
# Display module for pocket1090
#
################################################################################

import pygame
from pygame.locals import *


DEF_DISPLAY_WIDTH = 320
DEF_DISPLAY_HEIGHT = 320

DEF_RANGE_NAME = "mid"
DEF_BACKGROUND_COLOR = (240, 240, 240)
DEF_RANGE_RING_COLOR = (255, 255, 0)


class RadarDisplay():
    def __init__(self, width=DEF_DISPLAY_WIDTH, height=DEF_DISPLAY_HEIGHT, rangeName=DEF_RANGE_NAME, bgColor=DEF_BACKGROUND_COLOR, ringColor=DEF_RANGE_RING_COLOR):
        self.width = width
        self.height = height
        self.bgColor = bgColor
        self.ringColor = ringColor

        self.center = ((width / 2), (height / 2))
        self.rangeRings = {
            'mid': (((self.width / 8), "0.25nm"), ((self.width / 4), "0.5nm"), ((self.width / 2), "1.0nm"))
        }
        self.selectRange(rangeName)

        pygame.init()
        pygame.font.init()
        if False:
            print(f"\nDisplay: \n{pygame.display.Info()}\n{pygame.display.get_driver()} {pygame.display.list_modes()}\n")
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF)
        self._initScreen()

    def _drawRings(self):
        """Draw the range rings with their labels
          #### TODO
        """
        for ring in self.rangeRings[self.range]:
            pygame.draw.circle(self.screen, self.ringColor, self.center, ring[0], 1)
            #### TODO add labels

    def _initScreen(self):
        """Clear the screen and draw the labeled range rings
          #### TODO
        """
        screen.fill(self.bgColor)
        #### TODO add device symbol in the center
        self._drawRings()

    def rangeNames(self):
        """
          #### TODO
        """
        return self.rangeRings.keys()

    def selectRange(self, rangeName):
        """Select the scale of the display
          #### TODO
        """
        self.range = self.rangeRings[rangeName]

    def addTrack(self, track):
        """Add a track to the screen
          #### TODO
        """

    def render(self):
        """Render the screen
          #### TODO
        """
        pygame.display.flip()


####    pygame.quit()
