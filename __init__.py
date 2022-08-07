################################################################################
#
# pocket1090 package
#
################################################################################


from enum import Enum
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
