#!/usr/bin/env python3
################################################################################
#
# **Handheld Air Traffic Monitor**
#
# This app uses the dump1090-fa 1.09GHz SDR-based ADS-B and Mode S/3A/3C decoder
#  to monitor local air traffic in real time
#
# **TODO**
# * ?
################################################################################

import argparse
from dataclasses import dataclass
from enum import Enum
import json
import logging
import math
import matplotlib as mpl
import matplotlib.patches as patches
from matplotlib.path import Path
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import time
import yaml

from __init__ import * #### FIXME


DEF_CONFIG_FILE = "./pocket1090.yml"

DEFAULT_CONFIG = {
    'logLevel': "INFO",  #"DEBUG"  #"WARNING"
    'logFile': None,  # None means use stdout
}


class EntityType(Enum):
    STATIC = 0
    DYNAMIC = 1

class Category(Enum):
    A0 = 0  # No ADS-B emitter category information
    A1 = 1  # Light (< 15500 lbs)
    A2 = 2  # Small (15500 to 75000 lbs)
    A3 = 3  # Large (75000 to 300000 lbs)
    A4 = 4  # High vortex large (aircraft such as B-757)
    A5 = 5  # Heavy (> 300000 lbs)
    A6 = 6  # High performance (> 5g acceleration and 400 kts)
    A7 = 7  # Rotorcraft

    B0 = 8  # No ADS-B emitter category information
    B1 = 9  # Glider / sailplane
    B2 = 10 # Lighter-than-air
    B3 = 11 # Parachutist / skydiver
    B4 = 12 # Ultralight / hang-glider / paraglider
    B5 = 13 # Reserved
    B6 = 14 # Unmanned aerial vehicle
    B7 = 15 # Space / trans-atmospheric vehicle

    C0 = 16 # No ADS-B emitter category information
    C1 = 17 # Surface vehicle – emergency vehicle
    C2 = 18 # Surface vehicle – service vehicle
    C3 = 19 # Point obstacle (includes tethered balloons)
    C4 = 20 # Cluster obstacle
    C5 = 21 # Line obstacle
    C6 = 22 # Reserved
    C7 = 23 # Reserved

@dataclass
class Coordinate:
    x: float
    y: float

    def __add__(self, other):
        new = Coordinate(self.x, self.y)
        new.x += other.x
        new.y += other.y
        return new

    def __sub__(self, other):
        new = Coordinate(self.x, self.y)
        new.x -= other.x
        new.x = new.x if new.x >= 0.0 else 0.0
        new.y -= other.y
        new.y = new.y if new.y >= 0.0 else 0.0

@dataclass
class Motion:
    steeringAngle: float
    velocity: float
    duration: float


'''
"""The ? object ????"""
class ?():
  def __init__(self):

  def render(self, ax, color="gray"):
    vertices = [
                (self.x1, self.y1), # BL
                (self.x1, self.y2), # LT
                (self.x2, self.y2), # RT
                (self.x2, self.y1),  # RB
                (0.0, 0.0)
    ]
    codes = [
             Path.MOVETO,
             Path.LINETO,
             Path.LINETO,
             Path.LINETO,
             Path.CLOSEPOLY
    ]
    path = Path(vertices, codes)
    patch = patches.PathPatch(path, facecolor=color, lw=2)
    ax.add_patch(patch)
'''


def run(options):
    rcvrFile = os.path.join(options.path, "receiver.json")
    with open(rcvrFile, "r") as f:
        rcvrInfo = json.load(f)
    if options.verbose:
        print("Receiver Info:")
        json.dump(rcvrInfo, sys.stdout, indent=4, sort_keys=True)
        print("")

    running = True
    aircraftFile = os.path.join(options.path, "aircraft.json")
    lastTs = 0
    while running:
        ts = os.stat(aircraftFile).st_mtime
        print("TS: ", ts)
        while ts == lastTs:
            ts = os.stat(aircraftFile).st_mtime
            time.sleep(0.5)
        lastTs = ts
        with open(aircraftFile, "r") as f:
            aircraftInfo = json.load(f)
        if options.verbose:
            print("Aircraft Info:")
            json.dump(aircraftInfo, sys.stdout, indent=4, sort_keys=True)
            print("")

    print("DONE")
    return 0


def getOps():
    usage = f"Usage: {sys.argv[0]} [-v] [-c <configFile>] [-L <logLevel>] [-l <logFile>] <path>"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c", "--configFile", action="store", type=str, default=DEF_CONFIG_FILE,
        help="Path to file with configuration information; will be created if doesn't exist")
    ap.add_argument(
        "-L", "--logLevel", action="store", type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level")
    ap.add_argument(
        "-l", "--logFile", action="store", type=str,
        help="Path to location of logfile (create it if it doesn't exist)")
    ap.add_argument(
        "-v", "--verbose", action="count", default=0, help="Print debug info")
    ap.add_argument(
        "path", action="store", type=str,
        help="Path to where dump1090-fa writes its json files")
    opts = ap.parse_args()

    if not os.path.exists(opts.configFile):
        with open(opts.configFile, "w+") as f:
            f.write("%YAML 1.1\n---\n{}\n")
            if opts.verbose:
                print(f"Creating config file: '{opts.configFile}'")

    with open(opts.configFile, "r") as configFile:
        config = list(yaml.load_all(configFile, Loader=yaml.Loader))[0]
    if opts.verbose > 1:
        print("Config file contents:")
        json.dump(config, sys.stdout, indent=4, sort_keys=True)
        print("")

    # N.B. precedence order: command line options then config file inputs.
    #      if neither given, then propmt user for console input
    opts.config = DEFAULT_CONFIG

    if opts.logLevel:
        config['logLevel'] = opts.logLevel
    if opts.logFile:
        config['logFile'] = opts.logFile
    dictMerge(opts.config, config)
    if opts.verbose:
        print("CONFIG:")
        json.dump(opts.config, sys.stdout, indent=4, sort_keys=True)
        print("")

    if opts.config['logFile'] and not os.path.exists(opts.config['logFile']):
        with open(opts.config['logFile'], "w+") as f:
            if opts.verbose:
                print(f"Creating log file: '{opts.config['logFile']}'")
            f.write("")

    opts.config['level'] = getattr(logging, opts.config['logLevel'], None)
    if not isinstance(opts.config['level'], int):
        fatalError(f"Invalid log level: {opts.config['logLevel']}")
    logging.basicConfig(filename=opts.config.get('logFile', None),
                        level=opts.config['level'])

    if opts.verbose:
        print(f"    JSON Files Path: {opts.path}")
        print(f"    Log level:       {opts.config['logLevel']}")
        if opts.config['logFile']:
            print(f"    Logging to:      {opts.config['logFile']}")
        else:
            print(f"    Logging to stdout")

    return opts


if __name__ == '__main__':
    opts = getOps()
    r = run(opts)
    sys.exit(r)
