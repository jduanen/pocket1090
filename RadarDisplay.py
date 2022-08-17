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


DEF_DISPLAY_DIAMETER = 480

DEF_RANGE_NUM = 5
DEF_BACKGROUND_COLOR = (32, 32, 32)
DEF_RANGE_RING_COLOR = (255, 255, 0)
DEF_RING_FONT_COLOR = (240, 0, 240)
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
DO_NOT_ROTATE = ("?", "A0", "A7", "B6")


Ring = namedtuple("Ring", "radius km")


class RadarDisplay():
    def __init__(self, diameter=DEF_DISPLAY_DIAMETER, rangeNumber=DEF_RANGE_NUM, colors=DEF_COLORS, fullScreen=False, verbose=False):
        self.diameter = diameter
        self.rangeNumber = rangeNumber
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
        self.rings = [
            (Ring((self.diameter / 16), 0.25), Ring((self.diameter / 8), 0.5), Ring((self.diameter / 4), 1.0), Ring((self.diameter / 2), 2.0)),
            (Ring((self.diameter / 16), 0.5), Ring((self.diameter / 8), 1.0), Ring((self.diameter / 4), 2.0), Ring((self.diameter / 2), 4.0)),
            (Ring((self.diameter / 16), 1.0), Ring((self.diameter / 8), 2.0), Ring((self.diameter / 4), 4.0), Ring((self.diameter / 2), 8.0)),
            (Ring((self.diameter / 16), 2.0), Ring((self.diameter / 8), 4.0), Ring((self.diameter / 4), 8.0), Ring((self.diameter / 2), 16.0)),
            (Ring((self.diameter / 16), 4.0), Ring((self.diameter / 8), 8.0), Ring((self.diameter / 4), 16.0), Ring((self.diameter / ((2 * 32) / 24)), 24.0), Ring((self.diameter / 2), 32.0)),
            (Ring((self.diameter / 16), 8.0), Ring((self.diameter / 8), 16.0), Ring((self.diameter / 4), 32.0), Ring((self.diameter / ((2 * 64) / 48)), 48.0), Ring((self.diameter / 2), 64.0)),
            (Ring((self.diameter / 16), 16.0), Ring((self.diameter / 8), 32.0), Ring((self.diameter / 4), 64.0), Ring((self.diameter / ((2 * 128) / 96)), 96.0), Ring((self.diameter / 2), 128.0))
        ]
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

        self.rotation = 0
        self.selectedRange = rangeNumber
        self.rangeSpec = self.rings[rangeNumber]
        self.rangeRings = self._createRangeRings()
        self.selfSymbol = self._createSelfSymbol()
        self.symbols = self._createSymbols()

        self._initScreen()

    def _calcPixelAddr(self, dist, bearing):
        """Map the given a location (lat,lon) calculate and return the screen
            position (x,y) for the current display size and range selection
          #### TODO
          assumes trackLocation isn't off the screen
        """
        metersPerPixel = (self.rangeSpec[-1].km * 1000) / self.diameter
        if self.verbose > 1:
            print(f"      Dist: {dist:.2f}, Bearing: {bearing:.2f}\n")
        distPx = (dist * 1000) / metersPerPixel
        x = (distPx * math.sin(math.radians(bearing))) + (self.diameter / 2)
        y = -(distPx * math.cos(math.radians(bearing))) + (self.diameter / 2)
        return (x, y)

    def _createSymbols(self):
        """Draw all symbols
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
            filePath = f"assets/{cat}.png"
            if not os.path.exists(filePath):
                #### FIXME
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
        return symbols

    def _calcPixelCoordinates(self, selfPoint, targetPoint):
        dist, bearing = distanceBearing(selfPoint, targetPoint)
        return self._calcPixelAddr(dist, bearing)

    def _renderSymbol(self, track, selfLocation, trackLocation, trail=0):
        """Render the named symbol at the given coordinate, with the appropriately sized speed and heading vector
          If symbolName is None, then use the unknown symbol
          If speed is None, use a min-length vector
          If heading is None, don't add a vector
          Add flightNumber and altitude as text next to the symbol if they exist, else use "-" character
        """
        #### TODO make auto-range mode (enable/disable) -- reduce to smallest range that includes all current tracks
        #### FIXME improve handling of interesting things -- log altitude/speed (above/below thresholds), emergencies, special categories
        #### TODO consider adding notifications for interesting events -- e.g., SMS when military aircraft, fast/high, etc.
        #### FIXME make trail controls go from no trails, to longer/shorter ones with L/R arrow keys
        #### FIXME improve the symbols -- bigger, more colors?
        #### FIXME make rotation of symbol match vector
        #### TODO consider scaling symbols with range?
        #### TODO track and include symbols for all categories -- i.e., [A-D][0-7]
        #### TODO age symbols by changing alpha value with seen times ?

        #### TODO update README -- document inputs, document symbols, get screenshot at different ranges (with interesting traffic)
        #### TODO port to RasPi
        #### TODO implement GPS function with real HW
        #### TODO implement compass function with real HW
        ##print(f"      Category: {track.category}, Flight: {track.flightNumber}, Altitude: {track.altitude}, Speed: {track.speed}")
        symbol = self.symbols[track.category]
        dist, bearing = distanceBearing(selfLocation, trackLocation)
        if dist > self.rangeSpec[-1].km:
            logging.info(f"Track '{track.flightNumber}' out of range: {dist}")
            return
        position = self._calcPixelAddr(dist, bearing)

        if trail:
            points = [t.location for n,t in enumerate(track.history) if ((n < 1) or (t.location != track.history[n - 1].location))]
            '''
            for n, t in enumerate(track.history):
                pass
                ##print(f"XXXX: {n}, {t.location.latitude, t.location.longitude}, {track.history[n - 1].location.latitude, track.history[n - 1].location.longitude}, {(n < 1) or (t.location != track.history[n - 1].location)}")
            print(f"Track: {track.flightNumber}, History: {points}")
            '''
            for pt in points:
                x, y = self._calcPixelCoordinates(selfLocation, pt)
                #### FIXME try a 1x1 or 2x2 rectangle instead
                pygame.draw.circle(self.surface, self.trailColor, (x, y), 1)

        angle = 0
        if track.heading:
            startPt = pygame.math.Vector2(position)
            length = (5 + (track.speed / 10))
            angle = ((track.heading + 270) % 360)
            endPt = pygame.math.Vector2(startPt + pygame.math.Vector2(length, 0).rotate(angle))
            pygame.draw.line(self.surface, self.vectorColor, startPt, endPt, 1)

        text = self.font.render(f"{track.flightNumber}", True, self.trackFontColor, self.bgColor)
        text.set_colorkey(self.bgColor)
        textRect = text.get_rect()
        textRect.midbottom = (position[0], (position[1] - 5))
        self.surface.blit(text, textRect)

        text = self.font.render(f"{track.altitude}", True, self.trackFontColor, self.bgColor)
        text.set_colorkey(self.bgColor)
        textRect = text.get_rect()
        textRect.midtop = (position[0], (position[1] + 7))
        self.surface.blit(text, textRect)

        s = pygame.transform.rotate(symbol, ((angle + 180) % 360)) if track.category not in DO_NOT_ROTATE else symbol
        self.surface.blit(s, ((position[0] - (s.get_width() / 2)),
                              (position[1] - (s.get_height() / 2))))

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

            text = self.font.render(f"{ring.km / 2}km", True, self.ringFontColor, self.bgColor)
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

    def numberRanges(self):
        """Return the number of selectable ranges
          #### TODO
        """
        return len(self.rings)

    def rangeUp(self):
        """Select the next larger range setting
          #### TODO
        """
        self.selectRange(self.selectedRange + 1)

    def rangeDown(self):
        """Select the next smaller range setting
          #### TODO
        """
        self.selectRange(self.selectedRange - 1)

    def selectRange(self, rangeNumber):
        """Select the scale of the display and create the associated labeled range rings
          #### TODO
        """
        rangeNumber = rangeNumber if rangeNumber >= 0 else 0
        rangeNumber = rangeNumber if rangeNumber < len(self.rings) else (len(self.rings) - 1)
        if rangeNumber == self.selectedRange:
            return
        self.selectedRange = rangeNumber
        self.rangeSpec = self.rings[rangeNumber]
        self.rangeRings = self._createRangeRings()

    def trailsLess(self):
        """ #### TODO
        """
        if self.trails > 0:
            self.trails -= 1

    def trailsMore(self):
        """ #### TODO
        """
        self.trails += 1

    def trailsReset(self):
        """ #### TODO
        """
        self.trails = 0

    def render(self, rotation, selfLocation, tracks):
        """Render the screen with the given rotation and location
          #### TODO
        """
        #### TODO implement per-track trails, for now do them all the same
        self.rotation = rotation
        self._initScreen()
        for uid, track in tracks.items():
            if self.verbose:
                ##print(f"  Track {uid}: flight: {track.flightNumber} alt: {track.altitude}, speed: {track.speed}, dir: {track.heading}, cat: {track.category}")
                print(track)
            self._renderSymbol(track, selfLocation, track.location, self.trails)
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
                elif event.key == K_UP:
                    self.rangeUp()
                elif event.key == K_DOWN:
                    self.rangeDown()
                elif event.key == K_LCTRL:
                    print("L-CTRL")
                elif event.key == K_BACKSPACE:
                    self.trailsReset()
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
