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
#
# N.B.
#  need to do "export SDL_VIDEODRIVER='dummy'"
#  workon POCKET_1090
#  /home/jdn/Code2/dump1090/dump1090 --write-json /tmp/ > /tmp/fa.txt
#
#
################################################################################

import argparse
from datetime import datetime, timezone
import json
import logging
import math
import os
import sys
import time
import yaml

from geopy import Point

from __init__ import * #### FIXME

from Compass import Compass
from GPS import GPS
from RadarDisplay import RadarDisplay
from Track import TrackSpec, Track

DEF_CONFIG_FILE = "./pocket1090.yml"

DEFAULT_CONFIG = {
    'logLevel': "DEBUG",  #"DEBUG" #"INFO" #"WARNING"
    'logFile': None,  # None means use stdout
    'assetsPath': "/opt/pocket1090/assets"
}

REQUIRED_FIELDS = set({'lat', 'lon'})


def run(options):
    rcvrFile = os.path.join(options.path, "receiver.json")
    if os.path.exists(rcvrFile):
        with open(rcvrFile, "r") as f:
            rcvrInfo = json.load(f)
        if options.verbose:
            print("Receiver Info:")
            json.dump(rcvrInfo, sys.stdout, indent=4, sort_keys=True)
            print("")

    if options.position is None:
        gps = GPS()
    if options.orientation is None:
        compass = Compass()
    radar = RadarDisplay(options.config['assetsPath'], fullScreen=options.config['fullScreen'], verbose=options.verbose)

    running = True
    aircraftFile = os.path.join(options.path, "aircraft.json")
    lastTs = 0
    now = None
    msgCount = 0
    tracks = {}
    while running:
        ts = os.stat(aircraftFile).st_mtime
        while ts == lastTs:
            ts = os.stat(aircraftFile).st_mtime
            time.sleep(0.5)
        lastTs = ts
        with open(aircraftFile, "r") as f:
            j = json.load(f)
            now = j['now']
            msgCount = j['messages']
            unfilteredAircraftInfo = {a['hex']: a for a in j['aircraft']}
        aircraftInfo = {k: v for k, v in unfilteredAircraftInfo.items() if REQUIRED_FIELDS.issubset(v.keys())}
        added, removed, changed, unchanged = dictDiff(aircraftInfo, unfilteredAircraftInfo)
        filtered = {k: v for k, v in unfilteredAircraftInfo.items() if k in removed}
        ##logging.debug(f"Filtered: {filtered}, {len(added)}, {len(removed)}, {len(changed)}, {len(unchanged)}")
        if options.verbose > 1:
            print("Aircraft Info:")
            json.dump(aircraftInfo, sys.stdout, indent=4, sort_keys=True)
            print("")
        ##logging.debug(f"Current number of aircraft: {len(aircraftInfo)}")
        if options.verbose:
            currentFlightNums = [a['flight'] for a in aircraftInfo.values() if 'flight' in a]
            if currentFlightNums:
                logging.info(f"Flights ({len(currentFlightNums)}): {currentFlightNums}")

        #### TODO detect "interesting" cases (e.g., emergency, other than "A?") and save them
        emergencies = {k: v for k, v in aircraftInfo.items() if v.get('emergency', "none") != "none"}
        if emergencies and options.exceptFd:
            options.exceptFd.write(f"\a\nEmergencies: {emergencies}\n\a")
        oddVehicles = {k: v for k, v in aircraftInfo.items() if not v.get('category', "A").startswith("A")}
        if oddVehicles:
            options.exceptFd.write(f"\a\nUnusual Vehicles: {oddVehicles}\n\a")

        if options.orientation is None:
            heading, roll, pitch = compass.getEulerAngles()
        else:
            heading, roll, pitch = options.orientation
        if options.position is None:
            curTime, selfLocation = gps.getFilteredLocation()  #### TODO consider adding and handling timeouts
        else:
            curTime = datetime.utcnow().isoformat()
            selfLocation = options.position
        logging.info(f"Self: curTime={curTime}, location={selfLocation}, heading={heading}, roll={roll}, pitch={pitch}")

        for uniqueId, info in aircraftInfo.items():
            if uniqueId in tracks.keys():
                tracks[uniqueId].update(ts, selfLocation, **info)
                logging.debug(f"Updated track '{uniqueId}'")
            else:
                tracks[uniqueId] = Track(ts, selfLocation, **info)
                logging.debug(f"New Track {uniqueId}: {tracks[uniqueId]}")

        uids = aircraftInfo.keys()
        tracks = {k: v for k,v in tracks.items() if k in uids}

        if radar.render((heading, roll, pitch), selfLocation, curTime, tracks):
            running = False
    radar.quit()
    print("DONE")
    return 0


def getOps():
    usage = f"Usage: {sys.argv[0]} [-c <configFile>] [-f] [-L <logLevel>]"
    usage += " [-l <logFile>] [-o <heading>,<roll>,<pitch>] [-p <lat>,<lon>]"
    usage += " [-e <path>] [-v] <path>"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c", "--configFile", action="store", type=str, default=DEF_CONFIG_FILE,
        help="Path to file with configuration information; will be created if doesn't exist")
    ap.add_argument(
        "-e", "--exceptsFile", action="store", type=str, default='-',
        help="Path to file where exceptional track information is to be stored ('-' means stdout)")
    ap.add_argument(
        "-f", "--fullScreen", action="store_true", default=False,
        help="Execute in full screen mode")
    ap.add_argument(
        "-L", "--logLevel", action="store", type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level")
    ap.add_argument(
        "-l", "--logFile", action="store", type=str,
        help="Path to location of logfile (create it if it doesn't exist)")
    ap.add_argument(
        "-o", "--orientation", action="store", type=str,
        help="Fixed orientation to use instead of Compass (string containing three comma-separated floats: 'heading, roll, pitch'))")
    ap.add_argument(
        "-p", "--position", action="store", type=str,
        help="Fixed position to use instead of GPS (string containing two comma-separated floats: 'lat, lon'))")
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
        c = list(yaml.load_all(configFile, Loader=yaml.Loader))[0]
        config = [] if c is None else c
    if opts.verbose > 1:
        print("Config file contents:")
        json.dump(config, sys.stdout, indent=4, sort_keys=True)
        print("")

    # N.B. precedence order: command line options then config file inputs.
    #      if neither given, then prompt user for console input
    opts.config = DEFAULT_CONFIG

    if opts.logLevel:
        config['logLevel'] = opts.logLevel
    if opts.logFile:
        config['logFile'] = opts.logFile
    if opts.orientation:
        config['orientation'] = opts.orientation
    if opts.position:
        config['position'] = opts.position
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

    opts.exceptFd = None
    if opts.config['exceptsFile']:
        if opts.config['exceptsFile'] == "-":
            opts.exceptFd = sys.stdout
        else:
            opts.exceptFd = open(opts.config['exceptsFile'], "w+")
    else:
        opts.config = None

    if opts.config.get('orientation', None):
        orientation = opts.config['orientation'].split(",")
        if len(orientation) != 3:
            logging.error(f"Invalid orientation tuple: '{opts.config['orientation']}'")
            sys.exit(1)
        opts.orientation = (float(orientation[0]), float(orientation[1]), float(orientation[2]))
    else:
        opts.orientation = None

    if opts.config.get('position', None):
        position = opts.config['position'].split(",")
        if len(position) != 2:
            logging.error(f"Invalid position tuple: '{opts.config['position']}'")
            sys.exit(1)
        opts.position = Point(float(position[0]), float(position[1]))

    if opts.verbose:
        print(f"    Config File Path:   {opts.configFile}")
        print(f"    JSON Files Path:    {opts.path}")
        if opts.exceptFd:
            print(f"    Excepts Track file: {opts.exceptFd.name}")
        print(f"    Asset Files Path:   {opts.config['assetsPath']}")
        if opts.config['fullScreen']:
            print(f"    Enable Full Screen Mode")
        print(f"    Log level:          {opts.config['logLevel']}")
        if opts.config['logFile']:
            print(f"    Logging to:         {opts.config['logFile']}")
        else:
            print(f"    Logging to stdout")
        if opts.position:
            print(f"    Fixed Position:     {opts.position}")
        else:
            print(f"    Using GPS for Time and Position")

    return opts


if __name__ == '__main__':
    opts = getOps()
    r = run(opts)
    sys.exit(r)
