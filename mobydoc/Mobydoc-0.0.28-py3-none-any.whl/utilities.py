"""
Mobydoc.utilities module

* Finding coordinates from objects that have them

"""

import inspect
import logging

log = logging.getLogger(__name__)

# 
# coordinates parsing
#

def coordToFloat(coord):
    # cleans up '28.275078°' for now
    coord = coord.replace('°','')
    coord = coord.strip()
    value = float(coord)
    return value

#
# Handling of coordinates imports
#

def findCoordinate(coords_list, name):
    """Finds a coordinate by name in the list of coords_list

    Parameters
    ----------
    coords_list : list
        a list that may contained the coordinate sought after, or None
    name : str
        the name of a coordinate we're looking for

    Returns
    -------
    float
        the value of the coordinate, or None if not found
    """
    if coords_list and name:
        # we may have anything here, coordinates names are compared in a 
        # case-insensitive manner
        name = name.lower()
        # loop into the list
        for c in coords_list:
            # if this fail, there's nothing we can really do
            try:
                ac = c.autre_coordonnee.label.lower()
            except:
                continue
            # log.info("look for %s: => %s: %s"%(name, ac, c.valeur))
            if ac==name:
                return coordToFloat(c.valeur)
    return None

def getCoordinates(located_object):
    """Obtain the coordinates from a located object

    Parameters
    ----------
    located_object : object
        the object that the coordinates should be found in

    Returns
    -------
    tuple
        a 3 values tuple with latitude, longitude and altitude, or None
    """

    # first, check if the object is eligible
    # we should have 
    # * latitude and longitude
    # or
    # * autres_coordonnees
    # or both
    has_latitude = hasattr(located_object, 'latitude')
    has_longitude = hasattr(located_object, 'longitude')
    has_autres_coordonnees = hasattr(located_object, 'autres_coordonnees')
    if not ((has_latitude and has_longitude) or has_autres_coordonnees):
        log.error("ERROR: %s: object %s is not eligible"%(inspect.currentframe().f_code.co_name, repr(located_object)))
        return None

    # default values
    latitude = getattr(located_object, 'latitude', None)
    longitude = getattr(located_object, 'longitude', None)
    altitude = None

    if has_autres_coordonnees:
        if not latitude:
            latitude = findCoordinate(located_object.autres_coordonnees, 'latitude')
        if not longitude: 
            longitude = findCoordinate(located_object.autres_coordonnees, 'longitude')
        if not altitude:
            altitude = findCoordinate(located_object.autres_coordonnees, 'altitude')

    # if latitude or longitude:
    #     log.info("lat: %s lon: %s alt: %s"%(latitude, longitude, altitude))

    if (latitude is not None) and (longitude is not None) and (altitude is not None):
        if altitude is None:
            altitude = 0
        
        # values are valid
        return (latitude, longitude, altitude,)

    return None

def listGenUpdates(orig, new, dupes=False):
    log.info("listGenUpdates")
    log.info("    * %s"%(orig))
    log.info("    * %s"%(new))

    rem = []
    ok  = []
    add = []

    def _in_a(ob, l):
        for o in l:
            if ob == o:
                return True
        return False

    def _in_b(ob, l):
        for o in l:
            if o == ob:
                return True
        return False

    for o in orig:
        if _in_a(o, new):
            ok.append(o)
        else:
            rem.append(o)

    if dupes:

        t_ok = []
        for o in ok:
            # test if o is in t_ok
            found = False
            for to in t_ok:
                if o == to:
                    rem.append(o)
                    found = True
                    break
            if not found:
                t_ok.append(o)
        log.info("listGenUpdates | t_ok = %s"%(t_ok))
        ok = t_ok
    
    for n in new:
        if not _in_b(n, orig):
            add.append(n)

    return rem, ok, add

def renumber(o_list):
    i = 1
    for o in o_list:
        if o.ordre != i:
            log.info("renum * %d"%(i))
            o.ordre = i
        else:
            log.info("renum   %d"%(i))

        i += 1
    return i
    
