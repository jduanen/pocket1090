################################################################################
#
# Display module for pocket1090
#
################################################################################

from collections import namedtuple
from dataclasses import astuple
import logging
import os

import pygame
from pygame.locals import *

from __init__ import * #### FIXME


#### TODO Move all of this stuff to config, include paths to assets as well -- config is from main
DEF_DISPLAY_DIAMETER = 480

DEF_BACKGROUND_COLOR = (32, 32, 32)
DEF_RANGE_RING_COLOR = (128, 128, 0)
DEF_RING_FONT_COLOR = (192, 0, 192)
DEF_TRACK_FONT_COLOR = (0, 240, 0)
DEF_VECTOR_COLOR = (0, 240, 0)
DEF_TRAIL_COLOR = (128, 128, 128)
DEF_SELF_COLOR = (255, 0, 0)
DEF_COLORS = {
    'bgColor': DEF_BACKGROUND_COLOR,
    'ringColor': DEF_RANGE_RING_COLOR,
    'ringFontColor': DEF_RING_FONT_COLOR,
    'trackFontColor': DEF_TRACK_FONT_COLOR,
    'vectorColor': DEF_VECTOR_COLOR,
    'trailColor': DEF_TRAIL_COLOR,
    'selfColor': DEF_SELF_COLOR
}
FONT_SIZE = 10
MAX_SYMBOL_SIZE = 5
ALL_CATEGORIES = (f"{letter}{number}" for letter in ("A", "B", "C", "D", "E") for number in range(8))
TRACKED_CATEGORIES = (*ALL_CATEGORIES, "?")
ROTATE_SYMBOL = ("A1", "A2", "A3", "A4", "A5", "A6")
DEF_MAX_DISTANCE = 64
RING_DIVISORS = (8, 4, 2, 1.333333, 1)


class RadarDisplay():
    def __init__(self, maxDistance=DEF_MAX_DISTANCE, diameter=DEF_DISPLAY_DIAMETER, colors=DEF_COLORS, fullScreen=False, verbose=False):
        if maxDistance < 1:
            maxDistance = 1
            logging.warning("Minimum distance clamped to 1Km")
        self.diameter = diameter
        self.bgColor = colors['bgColor']
        self.ringColor = colors['ringColor']
        self.ringFontColor = colors['ringFontColor']
        self.trackFontColor = colors['trackFontColor']
        self.vectorColor = colors['vectorColor']
        self.trailColor = colors['trailColor']
        self.selfColor = colors['selfColor']
        self.fullScreen = fullScreen
        self.verbose = verbose

        self.center = Coordinate((diameter / 2), (diameter / 2))
        self.ringRadii = [int(self.diameter / (2 * n)) for n in RING_DIVISORS]

        self.trails = 0

        pygame.init()
        pygame.font.init()
        if False:
            #print(f"\nFonts: {pygame.font.get_fonts()}\n")
            print(f"\nFonts: {pygame.font.get_default_font()}\n")
        if False:
            print(f"\nDisplay: \n{pygame.display.Info()}\n{pygame.display.get_driver()} {pygame.display.list_modes()}\n")
        flags = DOUBLEBUF
        if fullScreen:
            flags |= FULLSCREEN
        self.surface = pygame.display.set_mode((self.diameter, self.diameter), flags)
        pygame.display.set_caption('Radar Display')
        self.font = pygame.font.Font('freesansbold.ttf', FONT_SIZE)
        self.rangeRings = pygame.Surface((self.diameter, self.diameter))

        self.autoRange = True

        self._setMaxDistance(maxDistance)
        self._createSelfSymbol()
        self._createSymbols()

        self._initScreen(None)

    def _setMaxDistance(self, maxDistance):
        """ #### TODO
          force maxDistance to the next higher power of two, clips min distance at 1Km, no upper limit
          also sets ring distances and recreates/labels the range rings
          N.B. Distances are in Km
        """
        maxD = maxDistance if maxDistance >= 1 else 1
        self.maxDistance = 1 << int(maxD).bit_length()
        self.ringDistances = [int(self.maxDistance / d) for d in RING_DIVISORS]
        self._createRangeRings()

    def _calcPixelAddr(self, distance, azimuth):
        """Map the given a location (lat,lon) calculate and return the screen
            position (x,y) for the current display size and range selection
          #### TODO
          assumes trackLocation isn't off the screen
        """
        metersPerPixel = (self.maxDistance * 1000.0) / (self.diameter / 2.0)
        if self.verbose > 1:
            print(f"      Distance: {distance:.2f}, Azimuth: {azimuth:.2f}")
        distPx = (distance * 1000) / metersPerPixel
        x = (distPx * math.sin(math.radians(azimuth))) + (self.diameter / 2)
        y = -(distPx * math.cos(math.radians(azimuth))) + (self.diameter / 2)
        return (x, y)

    def _createSymbols(self):
        """Create all symbols and draw on the symbols surface
          #### TODO
        """
        delta = MAX_SYMBOL_SIZE
        symbols = {}
        for cat in TRACKED_CATEGORIES:
            if cat == "?":
                diameter = 9
                s = pygame.Surface((diameter, diameter))
                s.fill(self.bgColor)
                s.set_colorkey(self.bgColor)
                pygame.draw.circle(s, (0, 148, 255), ((diameter / 2), (diameter / 2)), (diameter / 2))
                symbols[cat] = s
                continue
            if cat == "A0":
                diameter = 9
                s = pygame.Surface((diameter, diameter))
                s.fill(self.bgColor)
                s.set_colorkey(self.bgColor)
                pygame.draw.circle(s, self.vectorColor, ((diameter / 2), (diameter / 2)), (diameter / 2), width=1)
                symbols[cat] = s
                continue
            filePath = f"./assets/{cat}.png"  #### FIXME put these somewhere well-known in install and reference it
            if not os.path.exists(filePath):
                #### FIXME improve this -- e.g., different colors for different categories
                dim = 8
                s = pygame.Surface((dim, dim))
                s.fill(self.bgColor)
                s.set_colorkey(self.bgColor)
                pygame.draw.rect(s, (165, 255, 127), (0, 0, dim, dim))
                symbols[cat] = s
                continue
            img = pygame.image.load(filePath)
            surface = pygame.Surface(img.get_size())
            surface.fill(self.bgColor)
            surface.set_colorkey(self.bgColor)
            surface.blit(img, (0,0))
            symbols[cat] = surface
        self.symbols = symbols

    def _renderSymbol(self, track, selfLocation, trail=0):
        """Render the named symbol at the given coordinate, with the appropriately sized speed and heading vector
          If symbolName is None, then use the unknown symbol
          If speed is None, use a min-length vector
          If heading is None, don't add a vector
          Add flightNumber and altitude as text next to the symbol if they exist, else use "-" character
        """
        #### TODO make auto-range mode (enable/disable) -- reduce to smallest range that includes all current tracks
        #### FIXME improve handling of interesting things -- log altitude/speed (above/below thresholds), emergencies, special categories
        #### TODO consider adding notifications for interesting events -- e.g., SMS when military aircraft, fast/high, etc.
        #### FIXME improve the symbols -- bigger, more colors?
        #### FIXME make rotation of symbol match vector
        #### TODO consider scaling symbols with range?
        #### TODO add symbols for all categories -- i.e., [A-D][0-7]
        #### TODO age symbols by changing alpha value with seen times ?
        #### TODO update README -- document inputs, document symbols, get screenshot at different ranges (with interesting traffic)
        #### TODO print summary -- flight number, altitude, speed, distance, category
        ##print(f"      Category: {track.category}, Flight: {track.flightNumber}, Altitude: {track.altitude}, Speed: {track.speed}")

        if track.distance > self.maxDistance:
            logging.info(f"Track '{track.flightNumber}' out of range: {track.distance}")
            return
        trackPosition = self._calcPixelAddr(track.distance, track.azimuth)

        for trailLocation, trailDistance, trailAzimuth in track.getHistory(self.trails):
            x, y = self._calcPixelAddr(trailDistance, trailAzimuth)

            #### FIXME try a 1x1 or 2x2 rectangle instead
            pygame.draw.circle(self.surface, self.trailColor, (x, y), 1)

        angle = 0
        if track.heading:
            startPt = pygame.math.Vector2(trackPosition)
            length = (5 + (track.speed / 10))
            angle = ((track.heading + 270) % 360)
            endPt = pygame.math.Vector2(startPt + pygame.math.Vector2(length, 0).rotate(angle))
            pygame.draw.line(self.surface, self.vectorColor, startPt, endPt, 1)

        text = self.font.render(f"{track.flightNumber}", True, self.trackFontColor, self.bgColor)
        text.set_colorkey(self.bgColor)
        textRect = text.get_rect()
        textRect.midbottom = (trackPosition[0], (trackPosition[1] - 5))
        self.surface.blit(text, textRect)

        text = self.font.render(f"{track.altitude}", True, self.trackFontColor, self.bgColor)
        text.set_colorkey(self.bgColor)
        textRect = text.get_rect()
        textRect.midtop = (trackPosition[0], (trackPosition[1] + 7))
        self.surface.blit(text, textRect)

        #### FIXME fix rotation of symbol to match the vector (which seems correct)
        symbol = self.symbols[track.category]
        s = pygame.transform.rotate(symbol, ((angle + 180) % 360)) if track.category in ROTATE_SYMBOL else symbol
        self.surface.blit(s, ((trackPosition[0] - (s.get_width() / 2)),
                              (trackPosition[1] - (s.get_height() / 2))))

    def _createSelfSymbol(self):
        """Draw the device symbol onto the selfSymbol surface
        """
        delta = 10
        selfSymbol = pygame.Surface(((2 * delta), (2 * delta)))
        selfSymbol.fill(self.bgColor)
        selfSymbol.set_colorkey(self.bgColor)
        #### TODO replace this with a bitmap file glyph
        pygame.draw.line(selfSymbol, self.selfColor, (delta, 0), (delta, (2 * delta)))
        pygame.draw.line(selfSymbol, self.selfColor, ((0.75 * delta), delta), ((1.25 * delta) + 1, delta))
        pygame.draw.line(selfSymbol, self.selfColor, (delta, 0), ((0.5 * delta), (0.5 * delta)))
        pygame.draw.line(selfSymbol, self.selfColor, (delta, 0), ((1.5 * delta), (0.5 * delta)))
        self.selfSymbol = selfSymbol

    def _renderSelfSymbol(self, rotation):
        if rotation is None:
            s = self.selfSymbol
        else:
            s = pygame.transform.rotate(self.selfSymbol, rotation)
        self.surface.blit(s, ((self.center.x - (s.get_width() / 2)),
                              (self.center.y - (s.get_height() / 2))))

    def _createRangeRings(self):
        """Draw and label the range rings onto the rangeRings surface
          #### TODO
        """
        self.rangeRings.fill(self.bgColor)
        self.rangeRings.set_colorkey(self.bgColor)
        for ringRadius, ringDistance in zip(self.ringRadii, self.ringDistances):
            pygame.draw.circle(self.rangeRings, self.ringColor, astuple(self.center), ringRadius, 1)

            text = self.font.render(f"{ringDistance}km", True, self.ringFontColor, self.bgColor)
            textRect = text.get_rect()
            if ringDistance == self.maxDistance:
                textRect.center = (self.center.x, (self.center.y - ringRadius + (textRect.h / 2)))
            else:
                textRect.center = (self.center.x, (self.center.y - ringRadius + (textRect.h / 4)))
            self.rangeRings.blit(text, textRect)

    def _renderRangeRings(self):
        """Render the range rings onto the display surface
          #### TODO
        """
        self.surface.blit(self.rangeRings, ((self.center.x - (self.rangeRings.get_width() / 2)),
                                            (self.center.y - (self.rangeRings.get_height() / 2))))

    def _initScreen(self, rotation):
        """Clear the screen and draw the static elements (i.e., range rings and self symbol)
          #### TODO
        """
        self.surface.fill(self.bgColor)
        self._renderRangeRings()
        self._renderSelfSymbol(rotation)

    def getRange(self):
        """Return the current max distance (in Km)
          #### TODO
        """
        return self.maxDistance

    def setRange(self, maxDistance):
        """Set the current max distance (in Km)
          #### TODO
        """
        if maxDistance <= 0:
            raise ValueError("Invalid distance, must be greater than zero")
        if maxDistance < 1:
            logging.warning("Minimum distance clamped to 1Km")
        self.autoRange = False
        self._setMaxDistance(maxDistance)

    def rangeUp(self):
        """Select the next larger (power of two) range setting
          #### TODO
        """
        self.autoRange = False
        self._setMaxDistance(self.maxDistance)

    def rangeDown(self):
        """Select the next smaller (power of two) range setting
          #### TODO
        """
        self.autoRange = False
        self._setMaxDistance((self.maxDistance - 1) >> 1)

    def autoRange(self, enable=True):
        """Enable/disable the auto-ranging function
          #### TODO
        """
        self.autoRange = True

    def trailsLess(self):
        """ #### TODO
        """
        if self.trails > 0:
            self.trails -= 1
        logging.info(f"Trails: {self.trails}")

    def trailsMore(self):
        """ #### TODO
        """
        self.trails += 1
        logging.info(f"Trails: {self.trails}")

    def trailsMax(self):
        """ #### TODO
        """
        self.trails = -1
        logging.info(f"Trails: {self.trails}")

    def trailsReset(self):
        """ #### TODO
        """
        self.trails = 0
        logging.info(f"Trails: {self.trails}")

    def render(self, rotation, selfLocation, tracks):
        """Render the screen with the given rotation and location
          #### TODO
        """
        if self.autoRange:
            maxDist = max([t.distance for t in tracks.values()])
            logging.info(f"Max Track Distance: {maxDist}")
            self._setMaxDistance(maxDist)
        self._initScreen(rotation)
        #### TODO implement per-track trails, for now do them all the same
        for uid, track in tracks.items():
            if self.verbose < 2:
                alt = f"{track.altitude: >6}" if isinstance(track.altitude, int) else "      "
                speed = f"{track.speed:5.1f}" if isinstance(track.speed, float) else "     "
                heading = f"{track.heading:5.1f}" if isinstance(track.heading, float) else "     "
                try:
                    print(f"  flight: {track.flightNumber: <8} alt: {alt}, speed: {speed}, dir: {heading}, distance: {track.distance:5.1f} cat: {track.category: >2}")
                except:
                    print("XXXX:", track)
            if self.verbose >= 2:
                print(track)
            self._renderSymbol(track, selfLocation, self.trails)
        pygame.display.flip()

    def eventHandler(self):
        """#### TODO
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                return True
            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    self.trailsLess()
                elif event.key == K_RIGHT:
                    self.trailsMore()
                elif event.key == K_HOME:
                    self.trailsReset()
                elif event.key == K_END:
                    self.trailsMax()
                elif event.key == K_UP:
                    self.rangeUp()
                elif event.key == K_DOWN:
                    self.rangeDown()
                elif event.key == K_LCTRL:
                    print("L-CTRL")
                elif event.key == K_BACKSPACE:
                    self.trailsReset()
                elif event.key in (K_a, ):
                    self.autoRange = True
                elif event.key in (K_m, ):
                    self.autoRange = False
                elif event.key in (K_q, ):
                    self.quit()
                    return True
            if event.type == KEYUP:
                if event.key == K_LEFT:
                    pass
                elif event.key == K_RIGHT:
                    pass
                elif event.key == K_UP:
                    pass
                elif event.key == K_DOWN:
                    pass
        return False

    def quit(self):
        pygame.quit()

'''
def draw_dashed_line(surf, color, p1, p2, prev_line_len, dash_length=8):
    dx, dy = p2[0]-p1[0], p2[1]-p1[1]
    if dx == 0 and dy == 0:
        return 
    dist = math.hypot(dx, dy)
    dx /= dist
    dy /= dist

    step = dash_length*2
    start = (int(prev_line_len) // step) * step
    end = (int(prev_line_len + dist) // step + 1) * step
    for i in range(start, end, dash_length*2):
        s = max(0, start - prev_line_len)
        e = min(start - prev_line_len + dash_length, dist)
        if s < e:
            ps = p1[0] + dx * s, p1[1] + dy * s 
            pe = p1[0] + dx * e, p1[1] + dy * e 
            pygame.draw.line(surf, color, pe, ps)

def draw_dashed_lines(surf, color, points, dash_length=8):
    line_len = 0
    for i in range(1, len(points)):
        p1, p2 = points[i-1], points[i]
        dist = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
        draw_dashed_line(surf, color, p1, p2, line_len, dash_length)
        line_len += dist

def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=10):
    origin = Point(start_pos)
    target = Point(end_pos)
    displacement = target - origin
    length = len(displacement)
    slope = displacement/length

    for index in range(0, length/dash_length, 2):
        start = origin + (slope *    index    * dash_length)
        end   = origin + (slope * (index + 1) * dash_length)
        pygame.draw.line(surf, color, start.get(), end.get(), width)


def draw_line_dashed(surface, color, start_pos, end_pos, width = 1, dash_length = 10, exclude_corners = True):

    # convert tuples to numpy arrays
    start_pos = np.array(start_pos)
    end_pos   = np.array(end_pos)

    # get euclidian distance between start_pos and end_pos
    length = np.linalg.norm(end_pos - start_pos)

    # get amount of pieces that line will be split up in (half of it are amount of dashes)
    dash_amount = int(length / dash_length)

    # x-y-value-pairs of where dashes start (and on next, will end)
    dash_knots = np.array([np.linspace(start_pos[i], end_pos[i], dash_amount) for i in range(2)]).transpose()

    return [pg.draw.line(surface, color, tuple(dash_knots[n]), tuple(dash_knots[n+1]), width)
            for n in range(int(exclude_corners), dash_amount - int(exclude_corners), 2)]

'''
