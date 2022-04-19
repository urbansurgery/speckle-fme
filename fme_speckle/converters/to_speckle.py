"""Object Conversions from FME native to Speckle."""

from typing import List, Union

from fmeobjects import FMEFeature
from specklepy.objects.base import Base
from specklepy.objects.geometry import Box, Interval, Plane

from fme_speckle.features import set_feature_attribute, set_feature_rejection

CONVERSION_TYPES_FROM_FME_TO_SPECKLE = ()


def convert_features_to_speckle(feature_list: List[FMEFeature]):
    """General handler for the conversion of FME features to Speckle objects.

    Args:
        feature_list (list[FMEFeature]): The list of FME features to convert.
    """
    result = []
    for idx, feature in enumerate(feature_list):
        result.append(feature_to_speckle(feature, idx))
    return result


def feature_to_speckle(feature: FMEFeature, idx: int = 0) -> Union[Base, None]:
    """Converts a FME feature to a Speckle object.

    Args:
        feature (FMEFeature): The FME feature to convert.
        idx (int, optional): The index of the feature. Defaults to 0.
    """
    converted_object: Union[Base, None] = None
    if feature.getAttribute("targetType", str, None) in CONVERSION_TYPES_FROM_FME_TO_SPECKLE:
        try:
            converted_object = target_conversion(feature)
        except Exception as ex:
            print(f"Error converting {feature} \n{ex}")
            set_feature_rejection(feature, f"Error converting {feature} \n{ex}")
            raise ex

    if feature.hasGeometry():
        geom = feature.getGeometry()
        geom_type = geom.getName()

        if geom_type not in CONVERSION_TYPES_FROM_FME_TO_SPECKLE:
            raise Exception(f"Unsupported geometry type {geom_type}")

        converted_object = geom_to_speckle(feature)

    return converted_object


def target_conversion(feature: FMEFeature) -> Base:
    """Converts a FME feature to a Speckle object.

    Args:
        feature (FMEFeature): The FME feature to convert.
    """
    target_type = feature.getAttribute("targetType", str, None)
    if target_type == "Mesh":
        return mesh_to_speckle(feature)
    elif target_type == "Curve":
        return curve_to_speckle(feature)
    elif target_type == "Plane":
        return plane_to_speckle(feature)
    elif target_type == "Box":
        return box_to_speckle(feature)
    elif target_type == "Interval":
        return interval_to_speckle(feature)
    else:
        raise Exception(f"Unsupported target type {target_type}")


def geom_to_speckle(feature: FMEFeature) -> Base:
    """Converts a FME geometry to a Speckle object.

    Args:
        feature (FMEFeature): The FME feature to convert.
    """
    geom = feature.getGeometry()
    geom_type = geom.getName()

    if geom_type == "Point":
        return point_to_speckle(feature)
    elif geom_type == "Polyline":
        return polyline_to_speckle(feature)
    elif geom_type == "Polygon":
        return polygon_to_speckle(feature)
    elif geom_type == "MultiPoint":
        return multipoint_to_speckle(feature)
    elif geom_type == "MultiPolyline":
        return multipolyline_to_speckle(feature)
    elif geom_type == "MultiPolygon":
        return multipolygon_to_speckle(feature)
    elif geom_type == "MultiCurve":
        return multicurve_to_speckle(feature)
    elif geom_type == "MultiSurface":
        return multisurface_to_speckle(feature)
    elif geom_type == "Curve":
        return curve_to_speckle(feature)
    elif geom_type == "Surface":
        return surface_to_speckle(feature)
    elif geom_type == "MultiGeometry":
        return multigeometry_to_speckle(feature)
    else:
        raise Exception(f"Unsupported geometry type {geom_type}")
