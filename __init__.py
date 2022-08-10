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

from geopy import distance


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

def distanceBearing(startPt, endPt):
    """Calculate and return the distance and bearing between two points
      #### TODO
    """
    dist = distance.distance(startPt, endPt).km

    startLat = math.radians(startPt.latitude)
    startLon = math.radians(startPt.longitude)
    endLat = math.radians(endPt.latitude)
    endLon = math.radians(endPt.longitude)

    deltaLon = endLon - startLon
    if abs(deltaLon) > math.pi:
        deltaLon = -(2.0 * math.pi - deltaLon) if deltaLon > 0.0 else (2.0 * math.pi + deltaLon)

    tanStart = math.tan((startLat / 2.0) + (math.pi / 4.0))
    tanEnd = math.tan((endLat / 2.0) + (math.pi / 4.0))
    deltaPhi = math.log(tanEnd / tanStart)
    bearing = ((math.degrees(math.atan2(deltaLon, deltaPhi)) + 360.0) % 360.0)
    return dist, bearing


'''
def get_bearing(lat1,lon1,lat2,lon2):
    dLon = lon2 - lon1;
    y = math.sin(dLon) * math.cos(lat2);
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon);
    brng = np.rad2deg(math.atan2(y, x));
    if brng < 0: brng+= 360
    return brng
'''