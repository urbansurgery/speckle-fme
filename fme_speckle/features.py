"""FME Feature manipulation.

Methods for managing the geometry and attributes of a FME feature.
"""

from typing import Dict

from fmeobjects import FMEFeature

from fmeobjects import (
    FME_ATTR_STRING,
    FME_ATTR_INT64,
    FME_ATTR_BOOLEAN,
    FME_ATTR_REAL64,
    kFMEFeatureTypeAttr,
)


def set_feature_rejection(fme_feature: FMEFeature, reason: str) -> None:
    """Sets the rejection reason of the feature.

    Args:
        fme_feature (FMEFeature): The feature to set the rejection reason on.
        reason (str): The reason for the rejection.
    """
    set_feature_attribute(fme_feature, "REJECTED", reason)


def set_feature_attribute(
    fme_feature: FMEFeature, attr_name: str, attr_value, attr_type: type = str, is_list: bool = False
) -> None:
    """Sets the attribute of the feature or Null if the value is None.

    If None then optionally type set the attribute.

    Args:
        feature (FMEFeature): The feature to set the attribute on.
        attrName (str): The name of the attribute to set.
        attrValue (object): The value of the attribute to set.
        attrType (type): (Optional) The type of the attribute. Defaults to str.
        isList(bool): (Optional) Whether the attribute is a list. Defaults to False.

    Raises:
        FMEException: If something goes wrong.
    """
    attr_name = attr_name.replace(" ", "␣")

    type_map: Dict[type, int] = {
        str: FME_ATTR_STRING,
        int: FME_ATTR_INT64,
        bool: FME_ATTR_BOOLEAN,
        float: FME_ATTR_REAL64,
    }

    fme_attr_type = type_map[attr_type] or FME_ATTR_STRING

    if attr_value is None:
        fme_feature.setAttributeNullWithType(attr_name, fme_attr_type)
    else:
        if is_list:
            value = attr_value if type(attr_value) is list else [attr_value]
            old_list: list = fme_feature.getAttribute(attr_name)  # type: ignore
            if old_list:
                old_list.extend(value)
                fme_feature.setAttribute(attr_name, old_list)
            else:
                fme_feature.setAttribute(attr_name, value)
        else:
            fme_feature.setAttribute(attr_name, attr_value)


def set_feature_list_attribute(
    fme_feature: FMEFeature,
    attr_name: str,
    attr_value,  # type: ignore
    prop_name: str = "",
) -> None:
    """Sets the attribute of the feature as a list.

    Args:
        fme_feature (FMEFeature): The feature to set the attribute on.
        attr_name (str): The name of the attribute to set.
        attr_value (object): The value of the attribute to set.
        prop_name (str): (Optional) The name of the property to set. Defaults to "".
    """
    value = attr_value if type(attr_value) is list else [attr_value]

    list_attribute = fme_feature.getAttribute(attr_name)

    new_list = list_attribute if type(list_attribute) is list else []
    new_list.extend(value)

    fme_feature.setAttribute(attr_name, new_list)

    # TODO propName is not used - need to test the setting of a dict to a fme list attribute


def set_speckle_feature_type(fme_feature: FMEFeature, feature_type: str = "Base") -> None:
    """Set the Speckle feature type."""
    fme_feature.setFeatureType(feature_type)
    fme_feature.setAttribute(kFMEFeatureTypeAttr, feature_type)
