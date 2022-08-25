################################################################################
#
# pocket1090 package
#
################################################################################


from dataclasses import dataclass
from enum import Enum
import math
import sys
from time import sleep


def condPrint(str):
    """Conditional print
      Print a string if VERBOSE is non-zero
    """
    if (VERBOSE):
        print(str)

def fatalError(msg):
    """Print error message and exit
    """
    sys.stderr.write(f"Error: {msg}\n")
    sys.exit(1)

def dictDiff(newDict, oldDict):
    '''Take a pair of dictionaries and return a four-tuple with the elements
       that are: added, removed, changed, and unchanged between the new
       and the old dicts.
       Inputs:
         newDict: dict whose content might have changed
         oldDict: dict that is being compared against

       Returns
         added: set of dicts that were added
         removed: set of dicts that were removed
         changed: set of dicts that were changed
         unchanged: set of dicts that were not changed
    '''
    inOld = set(oldDict)
    inNew = set(newDict)

    added = (inNew - inOld)
    removed = (inOld - inNew)

    common = inOld.intersection(inNew)

    changed = set(x for x in common if oldDict[x] != newDict[x])
    unchanged = (common - changed)

    return (added, removed, changed, unchanged)

def dictMerge(old, new):
    ''' Merge a new dict into an old one, updating the old one (recursively).
    '''
    for k, _ in new.items():
        if (k in old and isinstance(old[k], dict) and
                isinstance(new[k], collections.Mapping)):
            dictMerge(old[k], new[k])
        else:
            old[k] = new[k]


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

    D0 = 24 # ?
    D1 = 25 # ?
    D2 = 26 # ?
    D3 = 27 # ?
    D4 = 28 # ?
    D5 = 29 # ?
    D6 = 30 # ?
    D7 = 31 # ?

@dataclass
class Coordinate:
    """ #### TODO
    """
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

def cpuTemp():
    """ #### TODO
    """
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        mC = float(f.read().strip())
        return (mC / 1000.0)
