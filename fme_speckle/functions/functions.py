"""Helper functions for FME Speckle."""

import fmeobjects

from fme_speckle.utilities.logging import log

"""
Speckle functions
"""

unit_scale = {
    "meters": 1.0,
    "centimeters": 0.01,
    "millimeters": 0.001,
    "inches": 0.0254,
    "feet": 0.3048,
    "kilometers": 1000.0,
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.340,
}

"""
Utility functions
"""


def _report(msg):
    """Function for printing messages to the console."""
    log(f"Speckle: {msg}")


def get_scale_length(units):
    """Get the unit scale length for the given units."""
    if units.lower() in unit_scale.keys():
        return unit_scale[units]
    _report("Units <{}> are not supported.".format(units))
    return 1.0


"""
Client, user, and stream functions
"""
