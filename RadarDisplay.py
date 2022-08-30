################################################################################
#
# Display module for pocket1090
#
################################################################################

from collections import namedtuple
from dataclasses import astuple
from datetime import datetime
import logging
from math import dist, floor
import os
import threading
import time

import pygame
from pygame.locals import *
import pygame_widgets
from pygame_widgets.button import Button
from tabulate import tabulate

from TrackStats import TrackStats
from __init__ import * #### FIXME


#### TODO Move all of this stuff to config, include paths to assets as well -- config is from main
DEF_DISPLAY_DIAMETER = 480
DEF_WINDOW_SIZE = (480, 800)

DEF_BACKGROUND_COLOR = (32, 32, 32)
DEF_RANGE_RING_COLOR = (128, 128, 0)
DEF_VECTOR_COLOR = (0, 240, 0)
DEF_TRAIL_COLOR = (128, 128, 128)
DEF_SELF_COLOR = (255, 0, 0)
DEF_COLORS = {
    'bgColor': DEF_BACKGROUND_COLOR,
    'ringColor': DEF_RANGE_RING_COLOR,
    'vectorColor': DEF_VECTOR_COLOR,
    'trailColor': DEF_TRAIL_COLOR,
    'selfColor': DEF_SELF_COLOR
}
DEF_SYMBOL_FONT_COLOR = (0, 240, 0)
DEF_RING_FONT_COLOR = (192, 0, 192)
DEF_SUMMARY_FONT_COLOR = (0xFF, 0xBF, 0x00)
DEF_FONT_INFO = {
    'symbolFont': ("freesansbold.ttf", 10, DEF_SYMBOL_FONT_COLOR),
    'ringFont': ("freesansbold.ttf", 10, DEF_RING_FONT_COLOR),
    'summaryFont': ("FreeMono, Monospace", 12, DEF_SUMMARY_FONT_COLOR),
    'infoFont': ("FreeMono, Monospace", 14, DEF_SUMMARY_FONT_COLOR)
}
MAX_SYMBOL_SIZE = 5
ALL_CATEGORIES = (f"{letter}{number}" for letter in ("A", "B", "C", "D", "E") for number in range(8))
TRACKED_CATEGORIES = (*ALL_CATEGORIES, "?")
ROTATE_SYMBOL = ("A1", "A2", "A3", "A4", "A5", "A6")
DEF_MAX_DISTANCE = 64
RING_DIVISORS = (8, 4, 2, 1.333333, 1)

INFO_MODE    = 0
SUMMARY_MODE = 1
DETAILS_MODE = 2

BUTTON_INACTIVE_COLOR = (160, 160, 160)
BUTTON_PRESSED_COLOR = (96, 96, 96)
BUTTON_HOVER_COLOR = (192, 192, 192)


class RadarDisplay():
    def __init__(self, assetsPath, windowSize=DEF_WINDOW_SIZE, maxDistance=DEF_MAX_DISTANCE,
                 diameter=DEF_DISPLAY_DIAMETER, colors=DEF_COLORS, fontInfo=DEF_FONT_INFO,
                 fullScreen=False, verbose=False):
        self.assetsPath = assetsPath
        if not os.path.exists(assetsPath):
            logging.error(f"Invalid path to assets directory: {assetsPath}")
            raise RuntimeError("Bad assets path")
        self.windowSize = windowSize
        if maxDistance < 1:
            maxDistance = 1
            logging.warning("Minimum distance clamped to 1Km")
        self.diameter = diameter
        self.bgColor = colors['bgColor']
        self.ringColor = colors['ringColor']
        self.vectorColor = colors['vectorColor']
        self.trailColor = colors['trailColor']
        self.selfColor = colors['selfColor']
        self.symbolFontInfo = fontInfo['symbolFont']
        self.ringFontInfo = fontInfo['ringFont']
        self.summaryFontInfo = fontInfo['summaryFont']
        self.infoFontInfo = fontInfo['infoFont']
        self.fullScreen = fullScreen
        self.verbose = verbose

        self.center = Coordinate(floor(diameter / 2), floor(diameter / 2))
        self.ringRadii = [int(self.diameter / (2 * n)) for n in RING_DIVISORS]

        self.trails = 0
        self.infoMode = SUMMARY_MODE
        self.farthest = False
        self.selectedTrack = None

        self.tz = time.tzname[time.daylight]

        pygame.init()
        if self.verbose:
            print(f"\nDisplay: \n{pygame.display.Info()}\n{pygame.display.get_driver()} {pygame.display.list_modes()}\n")

        pygame.font.init()
        if self.verbose:
            print(f"\nFonts: {pygame.font.get_default_font()}\n")
        fonts = pygame.font.get_fonts()
        for fontName, fontSize, fontColor in (self.symbolFontInfo, self.ringFontInfo, self.summaryFontInfo):
            '''
            if fontName not in fonts:
                logging.error(f"Font '{fontName}' not available")
                raise RuntimeError("Invalid font")
            '''
        self.symbolFont = pygame.font.Font(self.symbolFontInfo[0], self.symbolFontInfo[1])
        self.symbolFontColor = self.symbolFontInfo[2]
        self.ringFont = pygame.font.Font(self.ringFontInfo[0], self.ringFontInfo[1])
        self.ringFontColor = self.ringFontInfo[2]
        self.summaryFont = pygame.font.SysFont(self.summaryFontInfo[0], self.summaryFontInfo[1])
        self.summaryFontColor = self.summaryFontInfo[2]
        self.infoFont = pygame.font.SysFont(self.infoFontInfo[0], self.infoFontInfo[1])
        self.infoFontColor = self.infoFontInfo[2]

        flags = DOUBLEBUF
        if fullScreen:
            flags |= FULLSCREEN
        self.screen = pygame.display.set_mode(self.windowSize, flags)
        if False:
            print(f"Screen Size: {self.screen.get_size()}")
        self.radarSurface = pygame.Surface((self.diameter, self.diameter))
        pygame.display.set_caption('Radar Display')
        self.rangeRings = pygame.Surface((self.diameter, self.diameter))
        self.autoRange = True

        self.trackPositions = []
        self.stats = TrackStats()

        self.lock = threading.Lock()

        self._setMaxDistance(maxDistance)
        self._createSelfSymbol()
        self._createSymbols()
        self._createButtons()
        self._setButtons()
        self._initScreen(None)

        self.startTime = datetime.utcnow()

        self.running = True
        threading.Thread(target=self._eventHandler, args=(), daemon=True).start()

    def _setMaxDistance(self, maxDistance):
        """ #### TODO
          force maxDistance to the next higher power of two, clips min distance at 1Km, no upper limit
          also sets ring distances and recreates/labels the range rings
          N.B. Distances are in Km
        """
        prepDist = lambda d: int(d) if d >= 2 else round(d, 2)
        maxD = maxDistance if maxDistance >= 1 else 1
        self.maxDistance = 1 << int(maxD).bit_length()
        self.ringDistances = [prepDist(self.maxDistance / d) for d in RING_DIVISORS]
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
        x = (distPx * math.sin(math.radians(azimuth))) + (self.diameter / 2.0)
        y = -(distPx * math.cos(math.radians(azimuth))) + (self.diameter / 2.0)
        return (x, y)

    def _setButtons(self):
        """ #### TODO
        """
        if self.autoRange:
            self.buttons["Range_Auto"].setInactiveColour(BUTTON_PRESSED_COLOR)
            self.buttons["Range_Manual"].setInactiveColour(BUTTON_INACTIVE_COLOR)
        else:
            self.buttons["Range_Auto"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Range_Manual"].setInactiveColour(BUTTON_PRESSED_COLOR)

        if self.farthest:
            self.buttons["Tracks_Nearest"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Tracks_Farthest"].setInactiveColour(BUTTON_PRESSED_COLOR)
        else:
            self.buttons["Tracks_Nearest"].setInactiveColour(BUTTON_PRESSED_COLOR)
            self.buttons["Tracks_Farthest"].setInactiveColour(BUTTON_INACTIVE_COLOR)

        if self.trails < 0:
            self.buttons["Trails_All"].setInactiveColour(BUTTON_PRESSED_COLOR)
            self.buttons["Trails_None"].setInactiveColour(BUTTON_INACTIVE_COLOR)
        elif self.trails == 0:
            self.buttons["Trails_All"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Trails_None"].setInactiveColour(BUTTON_PRESSED_COLOR)
        else:
            self.buttons["Trails_All"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Trails_None"].setInactiveColour(BUTTON_INACTIVE_COLOR)

        if self.infoMode == SUMMARY_MODE:
            self.buttons["Mode_Summary"].setInactiveColour(BUTTON_PRESSED_COLOR)
            self.buttons["Mode_Details"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Mode_Info"].setInactiveColour(BUTTON_INACTIVE_COLOR)
        elif self.infoMode == DETAILS_MODE:
            self.buttons["Mode_Summary"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Mode_Details"].setInactiveColour(BUTTON_PRESSED_COLOR)
            self.buttons["Mode_Info"].setInactiveColour(BUTTON_INACTIVE_COLOR)
        elif self.infoMode == INFO_MODE:
            self.buttons["Mode_Summary"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Mode_Details"].setInactiveColour(BUTTON_INACTIVE_COLOR)
            self.buttons["Mode_Info"].setInactiveColour(BUTTON_PRESSED_COLOR)

    def _buttonHandler(self, buttonGroup, buttonName):
        """ #### TODO
        """
        dirty = False
        if buttonGroup == "Range":
            if buttonName == "Auto":
                if self.autoRange is False:
                    self.autoRange = True
                    dirty = True
            elif buttonName == "Manual":
                if self.autoRange is True:
                    self.autoRange = False
                    dirty = True
            elif buttonName == " ^ ":
                if self.autoRange is True:
                    self.autoRange = False
                    dirty = True
                self.rangeUp()
            elif buttonName == " v ":
                if self.autoRange is True:
                    self.autoRange = False
                    dirty = True
                self.rangeDown()
        elif buttonGroup == "Tracks":
            if buttonName == "Nearest":
                if self.farthest is True:
                    self.farthest = False
                    dirty = True
            elif buttonName == "Farthest":
                if self.farthest is False:
                    self.farthest = True
                    dirty = True
        elif buttonGroup == "Trails":
            if buttonName == "All":
                if self.trails >= 0:
                    self.trails = -1
                    dirty = True
            elif buttonName == "None":
                if self.trails != 0:
                    self.trails = 0
                    dirty = True
            elif buttonName == " ^ ":
                if self.trails <= 0:
                    self.trails += 1
                    dirty = True
            elif buttonName == " v ":
                self.trails -= 1
        elif buttonGroup == "Mode":
            if buttonName == "Summary":
                if self.infoMode != SUMMARY_MODE:
                    self.infoMode = SUMMARY_MODE
                    dirty = True
            if buttonName == "Details":
                if self.infoMode != DETAILS_MODE:
                    self.infoMode = DETAILS_MODE
                    dirty = True
            elif buttonName == "Info":
                if self.infoMode != INFO_MODE:
                    self.infoMode = INFO_MODE
                    dirty = True
        if dirty:
            self._setButtons()

    def _createButtons(self):
        """ #### TODO
        """
        LABELS = ("Range", "Tracks", "Trails", "Mode")
        LABEL_WIDTH = int(round((self.diameter / len(LABELS))))
        LABEL_HEIGHT = 12
        self.labels = {}
        x = 0
        for l in LABELS:
            self.labels[l] = Button(self.screen,
                x + 1, self.diameter,
                LABEL_WIDTH - 2, LABEL_HEIGHT,
                text=l, fontSize=14, margin=1,
                inactiveColour=(128, 128, 128),
                hoverColour=(128, 128, 128),
                pressedColour=(128, 128, 128))
            x += LABEL_WIDTH

        BUTTON_LABELS = [
            ("Auto", "Manual", " ^ ", " v "),
            ("Nearest", "Farthest"),
            ("All", "None", " ^ ", " v "),
            ("Summary", "Details", "Info")]
        BUTTON_HEIGHT = 12
        self.buttons = {}
        for indx, labels in enumerate(BUTTON_LABELS):
            totalLabelsLen = sum(len(l) for l in labels)
            x = (indx * LABEL_WIDTH)
            totalButtonWidth = 0
            for b in labels:
                buttonName = f"{LABELS[indx]}_{b}"
                buttonWidth = int(round(((len(b) * LABEL_WIDTH)/ totalLabelsLen) + 0.5))
                totalButtonWidth += buttonWidth
                if totalButtonWidth >= LABEL_WIDTH:
                    x -= 1
                y = self.diameter + LABEL_HEIGHT + 1
                self.buttons[buttonName] = Button(self.screen,
                    x + 1, y,
                    buttonWidth - 2, BUTTON_HEIGHT,
                    text=b, fontSize=14, margin=2,
                    inactiveColour=BUTTON_INACTIVE_COLOR,
                    hoverColour=BUTTON_HOVER_COLOR,
                    pressedColour=BUTTON_PRESSED_COLOR,
                    onClickParams=(LABELS[indx], b),
                    onClick=self._buttonHandler)
                x += buttonWidth
        self.buttonHeight = (LABEL_HEIGHT * 2) + 1

    def _createSymbols(self):
        """Create all symbols and draw on the symbols surface
          #### TODO
        """
        delta = MAX_SYMBOL_SIZE
        symbols = {}
        for cat in TRACKED_CATEGORIES:
            if cat == "?":
                s.fill(self.bgColor)
                s.set_colorkey(self.bgColor)
                diameter = 9
                s = pygame.Surface((diameter, diameter))
                d = floor(diameter / 2)
                pygame.draw.circle(s, (0, 148, 255), (d, d), d)
                symbols[cat] = s
                continue
            if cat == "A0":
                diameter = 9
                s = pygame.Surface((diameter, diameter))
                s.fill(self.bgColor)
                s.set_colorkey(self.bgColor)
                d = floor(diameter / 2)
                pygame.draw.circle(s, self.vectorColor, (d, d), d, width=1)
                symbols[cat] = s
                continue
            filePath = os.path.join(self.assetsPath, f"{cat}.png")
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
          Add flightNumber and altitude as text next to the symbol
        """
        #### FIXME make symbols overwrite tracks (aot the converse, which is happening now)
        #### FIXME improve handling of interesting things -- log altitude/speed (above/below thresholds), emergencies, special categories
        #### TODO consider adding notifications for interesting events -- e.g., SMS when military aircraft, fast/high, etc.
        #### TODO improve the symbols -- bigger, more colors?
        #### TODO consider scaling symbols with range?
        #### TODO add symbols for all categories -- i.e., [A-D][0-7]
        #### TODO age symbols by changing alpha value with seen times ?
        #### TODO update README -- document inputs, document symbols, get screenshot at different ranges (with interesting traffic)
        if track.distance > self.maxDistance:
            logging.info(f"Track '{track.flightNumber}' out of range: {track.distance}")
            return
        trackPosition = self._calcPixelAddr(track.distance, track.azimuth)

        for trailLocation, trailDistance, trailAzimuth in track.getHistory(self.trails):
            x, y = self._calcPixelAddr(trailDistance, trailAzimuth)
            pygame.draw.rect(self.radarSurface, self.trailColor, Rect((x - 1), (y - 1), 3, 3))

        angle = 0
        if track.heading:
            startPt = pygame.math.Vector2(trackPosition)
            length = (5 + (track.speed / 10))
            angle = ((track.heading + 270) % 360)
            endPt = pygame.math.Vector2(startPt + pygame.math.Vector2(length, 0).rotate(angle))
            pygame.draw.line(self.radarSurface, self.vectorColor, startPt, endPt, 1)

        text = self.symbolFont.render(f"{track.flightNumber}", True, self.symbolFontColor, self.bgColor)
        text.set_colorkey(self.bgColor)
        textRect = text.get_rect()
        textRect.midbottom = (trackPosition[0], (trackPosition[1] - 5))
        self.radarSurface.blit(text, textRect)

        text = self.symbolFont.render(f"{track.altitude}", True, self.symbolFontColor, self.bgColor)
        text.set_colorkey(self.bgColor)
        textRect = text.get_rect()
        textRect.midtop = (trackPosition[0], (trackPosition[1] + 7))
        self.radarSurface.blit(text, textRect)

        symbol = self.symbols[track.category]
        newAngle = -(angle + 90.0) if angle <= 270.0 else -(angle - 270.0)
        s = pygame.transform.rotate(symbol, newAngle) if track.category in ROTATE_SYMBOL else symbol
        self.radarSurface.blit(s, ((trackPosition[0] - floor(s.get_width() / 2)),
                                   (trackPosition[1] - floor(s.get_height() / 2))))
        return trackPosition

    def _createSelfSymbol(self):
        """Draw the device symbol onto the selfSymbol surface
        """
        filePath = os.path.join(self.assetsPath, f"self.png")
        if os.path.exists(filePath):
            img = pygame.image.load(filePath)
            selfSymbol = pygame.Surface(img.get_size())
            selfSymbol.fill(self.bgColor)
            selfSymbol.set_colorkey(self.bgColor)
            selfSymbol.blit(img, (0,0))
        else:
            delta = 10
            selfSymbol = pygame.Surface(((2 * delta), (2 * delta)))
            selfSymbol.fill(self.bgColor)
            selfSymbol.set_colorkey(self.bgColor)
            pygame.draw.line(selfSymbol, self.selfColor, (delta, 0), (delta, (2 * delta)))
            pygame.draw.line(selfSymbol, self.selfColor, ((0.75 * delta), delta), ((1.25 * delta) + 1, delta))
            pygame.draw.line(selfSymbol, self.selfColor, (delta, 0), ((0.5 * delta), (0.5 * delta)))
            pygame.draw.line(selfSymbol, self.selfColor, (delta, 0), ((1.5 * delta), (0.5 * delta)))
        self.selfSymbol = selfSymbol

    def _renderSelfSymbol(self, rotation):
        if rotation is None:
            s = self.selfSymbol
        else:
            s = pygame.transform.rotate(self.selfSymbol, -rotation)
        self.radarSurface.blit(s, ((self.center.x - floor(s.get_width() / 2)),
                                   (self.center.y - floor(s.get_height() / 2))))

    def _createRangeRings(self):
        """Draw and label the range rings onto the rangeRings surface
          #### TODO
        """
        self.rangeRings.fill(self.bgColor)
        self.rangeRings.set_colorkey(self.bgColor)
        for ringRadius, ringDistance in zip(self.ringRadii, self.ringDistances):
            pygame.draw.circle(self.rangeRings, self.ringColor, astuple(self.center), ringRadius, 1)

            text = self.ringFont.render(f"{ringDistance}Km", True, self.ringFontColor, self.bgColor)
            textRect = text.get_rect()
            if ringDistance == self.maxDistance:
                textRect.center = (self.center.x, (self.center.y - ringRadius + floor(textRect.h / 2)))
            else:
                textRect.center = (self.center.x, (self.center.y - ringRadius + floor(textRect.h / 4)))
            self.rangeRings.blit(text, textRect)

    def _renderRangeRings(self):
        """Render the range rings onto the display surface
          #### TODO
        """
        self.radarSurface.blit(self.rangeRings, ((self.center.x - floor(self.rangeRings.get_width() / 2)),
                                                 (self.center.y - floor(self.rangeRings.get_height() / 2))))

    def _initScreen(self, rotation):
        """Clear the screen and draw the static elements (i.e., range rings and self symbol)
          #### TODO
        """
        self.radarSurface.fill(self.bgColor)
        self._renderRangeRings()
        self._renderSelfSymbol(rotation)

    def _getSelectedTrack(self, location):
        """ #### TODO
          assume always have small number of tracks so don't have to worry about performance
        """
        if (location[1] > self.diameter):
            return None
        minDist = 10
        nearestTrack = None
        if self.trackPositions:
            for position, track in self.trackPositions:
                if not isinstance(position, tuple):
                    print("PPPP", type(position))
                if not isinstance(location, tuple):
                    print("LLLL", type(location))
                d = dist(location, position)
                if d < minDist:
                    minDist = d
                    nearestTrack = track
        return nearestTrack
        '''
        ? = []
        tree = spatial.KDTree(?)
        nearestTrack = tree.query([location])
        print("TTTT", nearestTrack)
        if nearestTrack?:
            return nearestTrack
        '''

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

    def render(self, orientation, selfLocation, currentTime, tracks):
        """Render the screen with the given orientation and location
          #### TODO
        """
        #### FIXME allow the Mode displays to work even when there's no tracks
        if len(tracks) < 1:
            sortedTracks = []
            maxDist = DEF_MAX_DISTANCE
        else:
            sortedTracks = sorted(tracks.values(), key=lambda t: t.distance, reverse=self.farthest)
            if self.autoRange:
                indx = 0 if self.farthest else -1
                maxDist = sortedTracks[indx].distance
                logging.info(f"Max Track (Ring) Distance: {maxDist:.2f} ({self.maxDistance}) Km")
                with self.lock:
                    self._setMaxDistance(maxDist)

        self._initScreen(orientation[0])

        if self.verbose >= 2:
            print("flight      alt.  speed   dir.  dist.   azi.  cat.")
            print("--------  ------  -----  -----  -----  -----  ----")
        table = []
        self.trackPositions = []
        for track in sortedTracks:
            alt = track.altitude if isinstance(track.altitude, int) else " "
            speed = round(track.speed, 0) if isinstance(track.speed, float) else " "
            heading = round(track.heading, 1) if isinstance(track.heading, float) else " "
            table.append([track.flightNumber, alt, speed, heading, round(track.distance, 2), round(track.azimuth, 1), track.category, track.rssi])
            if self.verbose >= 2:
                alt = f"{track.altitude: >6}" if isinstance(track.altitude, int) else "      "
                speed = f"{track.speed:5.1f}" if isinstance(track.speed, float) else "     "
                heading = f"{track.heading:5.1f}" if isinstance(track.heading, float) else "     "
                print(f"{track.flightNumber: <8}, {alt}, {speed}, {heading}, {track.distance:5.1f}, {track.azimuth:5.1f},  {track.category: >2}")
            if self.verbose >= 2:
                print(track)
            #### TODO implement per-track trails, for now do them all the same
            pos = self._renderSymbol(track, selfLocation, self.trails)
            self.trackPositions.append((pos, track))
            self.stats.update(track)
        if self.verbose >= 2:
            print("")
        y = self.diameter + self.buttonHeight + 4
        self.screen.fill(self.bgColor, Rect(0, y, self.diameter, (self.windowSize[1] - y)))
        if self.infoMode == SUMMARY_MODE:
            columns = ["Flight", "Feet", "Knots", "Head.", "Dist.", "Azi.", "Cat.", "RSSI"]
            t = tabulate(table, headers=columns)
            for line in t.split('\n'):
                text = self.summaryFont.render(line, True, self.summaryFontColor, self.bgColor)
                textRect = text.get_rect()
                textRect.topleft = (4, y)
                self.screen.blit(text, textRect)
                y += textRect.h + 2
                if y >= self.windowSize[1]:
                    break
        elif self.infoMode == DETAILS_MODE:
            #### FIXME test if track is gone
            #if self.selectedTrack not in ?:
            #    self.selectedTrack = None
            if self.selectedTrack:
                trk = self.selectedTrack
                alt = f"{trk.altitude: >6}" if isinstance(trk.altitude, int) else "      "
                speed = f"{trk.speed:5.1f}" if isinstance(trk.speed, float) else "     "
                heading = f"{trk.heading:5.1f}" if isinstance(trk.heading, float) else "     "
                lines = [
                    f"UniqueId:       {trk.uniqueId}",
                    f"Flight Number:  {trk.flightNumber}",
                    f"Baro Altitude:  {trk.altitude} FASL",
                    f"Ground Speed:   {trk.speed} knots",
                    f"Track Heading:  {trk.heading} deg",
                    f"Category:       {trk.category}",
                    f"Latitude:       {trk.lat}",
                    f"Longitude:      {trk.lon}",
                    f"Distance to:    {trk.distance:.3f} Km",
                    f"Azimuth to:     {trk.azimuth:.1f} deg",
                    f"Last Seen:      {trk.seen} secs",
                    f"Last Position:  {trk.seenPos} secs",
                    f"RSSI:           {trk.rssi} dBFS",
                    f"Timestamp:      {datetime.fromtimestamp(trk.timestamp).isoformat()} {self.tz}",
                    f"Location:       {trk.location}"
                ]
                y += 8
                for line in lines:
                    text = self.infoFont.render(line, True, self.infoFontColor, self.bgColor)
                    textRect = text.get_rect()
                    textRect.topleft = (12, y)
                    self.screen.blit(text, textRect)
                    y += textRect.h + 2
                    if y >= self.windowSize[1]:
                        logging.warning("Window overrun")
                        break
        elif self.infoMode == INFO_MODE:
            lines = [
                f"Start Time:      {self.startTime} UTC",
                f"Orientation:     heading = {orientation[0]}, roll = {orientation[1]}, pitch = {orientation[2]}",
                f"Location:        {selfLocation}",
                f"Time:            {currentTime} UTC",
                f"CPU Temperature: {cpuTemp()} C",
                f"Number of Uids:  {len(self.stats.uids)}",
                f"Altitude Stats:  min={self.stats.minAltitude}, max={self.stats.maxAltitude}, avg={self.stats.avgAltitude:.2f}",
                f"Speed Stats:     min={self.stats.minSpeed}, max={self.stats.maxSpeed}, avg={self.stats.avgSpeed:.2f}",
                f"Distance Stats:  min={self.stats.minDistance:.2f}, max={self.stats.maxDistance:.2f}, avg={self.stats.avgDistance:.2f}",
                f"RSSI Stats:      min={self.stats.minRSSI}, max={self.stats.maxRSSI}, avg={self.stats.avgRSSI:.2f}"
                #### TODO add category histogram
            ]
            y += 8
            for line in lines:
                text = self.infoFont.render(line, True, self.infoFontColor, self.bgColor)
                textRect = text.get_rect()
                textRect.topleft = (22, y)
                self.screen.blit(text, textRect)
                y += textRect.h + 2
                if y >= self.windowSize[1]:
                    break
        text = self.summaryFont.render(f"{len(table)}", True, self.summaryFontColor, self.bgColor)
        textRect = text.get_rect()
        textRect.bottomleft = (2, (self.diameter - 2))
        with self.lock:
            self.screen.blit(self.radarSurface, (0, 0))
            if text:
                self.screen.blit(text, textRect)
            pygame.display.flip()
            r = not self.running
        return r

    def _eventHandler(self):
        """#### TODO
        """
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                dirty = False
                if event.type == KEYDOWN:
                    if event.key == K_LEFT:
                        dirty = True
                        self.trails -= 1
                    elif event.key == K_RIGHT:
                        dirty = True
                        self.trails += 1
                    elif event.key == K_HOME:
                        dirty = True
                        self.trails = 0
                    elif event.key == K_END:
                        dirty = True
                        self.trails = -1
                    elif event.key == K_UP:
                        dirty = True
                        self.rangeUp()
                    elif event.key == K_DOWN:
                        dirty = True
                        self.rangeDown()
                    elif event.key == K_LCTRL:
                        print("L-CTRL")
                    elif event.key == K_BACKSPACE:
                        dirty = True
                        self.trailsNone()
                    elif event.key in (K_a, ):
                        dirty = True
                        self.autoRange = True
                    elif event.key in (K_d, ):
                        dirty = True
                        self.infoMode = DETAILS_MODE
                    elif event.key in (K_i, ):
                        dirty = True
                        self.infoMode = INFO_MODE
                    elif event.key in (K_s, ):
                        dirty = True
                        self.infoMode = SUMMARY_MODE
                    elif event.key in (K_p, ):
                        self.stats.printStats()
                    elif event.key in (K_r, ):
                        self.stats.resetStats()
                    elif event.key in (K_m, ):
                        dirty = True
                        self.autoRange = False
                    elif event.key in (K_h, ):
                        print("Keyboard Inputs:")
                        print("  Left Arrow: reduce maximum number of trail points displayed")
                        print("  Right Arrow: increase maximum number of trail points displayed")
                        print("  Home: display no trail points")
                        print("  End: display all trail points")
                        print("  Up Arrow: increase the max distance to the next power of two Km")
                        print("  Down Arrow: decrease the max distance to the next power of two Km")
                        print("  'a': auto-range -- enable auto-range mode")
                        print("  'm': manual range -- disable auto-range mode")
                        print("  'i': info mode")
                        print("  's': summary mode")
                        print("  'd': detail mode")
                        print("  'p': print info")
                        print("  'r': reset info")
                        print("  'q': quit -- exit the application")
                    elif event.key in (K_q, ):
                        self.running = False
                if dirty:
                    self._setButtons()
                if event.type == KEYUP:
                    if event.key == K_LEFT:
                        pass
                    elif event.key == K_RIGHT:
                        pass
                    elif event.key == K_UP:
                        pass
                    elif event.key == K_DOWN:
                        pass
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mousePresses = pygame.mouse.get_pressed()
                    if mousePresses[0]:
                        mouseLocation = pygame.mouse.get_pos()
                        self.selectedTrack = self._getSelectedTrack(mouseLocation)
            with self.lock:
                pygame_widgets.update(events)

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
