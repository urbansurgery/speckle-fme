"""Conversions of property values between FME and Speckle."""

from typing import Dict, TypedDict, Union
from fmeobjects import FMEAppearance

from specklepy.objects.other import RenderMaterial


class RGBA(TypedDict):
    """RGBA Color with named fields."""

    r: float
    g: float
    b: float
    a: float


def unit_color(color: int) -> float:
    """Convert a colour from 0-255 to 0-1.

    Args:
        colour (int): The colour to convert.

    Returns:
        float: The converted colour.
    """
    return color / 255.0


def rgba_from_argb_int(argb_int: int) -> Dict[str, float]:
    """Translate signed integer argb color to float rgba color.

    Args:
        argb_int (int): _description_

    Returns:
        Tuple[float, float, float, float]: _description_
    """
    alpha_mask = 0xFF000000
    red_mask = 0xFF0000
    green_mask = 0xFF00
    blue_mask = 0xFF

    alpha = (argb_int & alpha_mask) >> 24
    red = (argb_int & red_mask) >> 16
    green = (argb_int & green_mask) >> 8
    blue = argb_int & blue_mask

    return {
        "r": unit_color(red),
        "g": unit_color(green),
        "b": unit_color(blue),
        "a": unit_color(alpha),
    }


def render_material_to_appearance(
    render_material: RenderMaterial, fme_appearance: FMEAppearance
) -> Dict[str, Union[int, float]]:
    """Converts a Metalness map to an FME Appearance."""
    ...
