import fmeobjects

logger = fmeobjects.FMELogFile()

from specklepy.objects.other import *
from specklepy.objects.geometry import *

SUPPORTED_CURVES = ()

CONVERSION_TYPES_FROM_SPECKLE_TO_FME = (
    Mesh,
    *SUPPORTED_CURVES,
)


def can_convert_to_native(speckle_object):
    if type(speckle_object) in CONVERSION_TYPES_FROM_SPECKLE_TO_FME:
        return True
    display = getattr(speckle_object, "displayMesh", getattr(speckle_object, "displayValue", None))
    if display:
        return True

    logger.logMessageString(f"Could not convert unsupported Speckle object: {speckle_object}")
    return False


def convert_to_native(speckle_object, name=None, fme_object=None):
    speckle_type = type(speckle_object)
    speckle_name = (
        name or getattr(speckle_object, "name", None) or speckle_object.speckle_type + f" -- {speckle_object.id}"
    )
    if speckle_type not in CONVERSION_TYPES_FROM_SPECKLE_TO_FME:
        display = getattr(speckle_object, "displayMesh", getattr(speckle_object, "displayValue", None))
        if not display:
            logger.logMessageString(f"Could not convert unsupported Speckle object: {speckle_object}")
            return

        if isinstance(display, list):
            for item in display:
                item.parent_speckle_type = speckle_object.speckle_type
                convert_to_native(item)
        else:
            display.parent_speckle_type = speckle_object.speckle_type
            return convert_to_native(display, speckle_name)

    try:
        if speckle_type is Mesh:
            obj_data = mesh_to_native(speckle_object, name=speckle_name)

        elif speckle_type in SUPPORTED_CURVES:
            obj_data = curve_to_native(speckle_object, name=speckle_name)

        else:
            logger.LogMessage(f"Unsupported type {speckle_type}")
            return None

    except Exception as ex:  # conversion error
        logger.LogMessage(f"Error converting {speckle_object} \n{ex}")
        return None

    fme_object.speckle.object_id = str(speckle_object.id)
    fme_object.speckle.enabled = True

    return fme_object


def mesh_to_native(speckle_mesh, name, scale=1.0):

    logger.LogMessage("Converting mesh", 1)
    print(speckle_mesh)

    fme_mesh = fmeobjects.FMEMesh()

    return fme_mesh


def curve_to_native(speckle_curve, blender_curve, scale=1.0):
    curve_type = type(speckle_curve)
    if curve_type is Line:
        return line_to_native(speckle_curve, blender_curve, scale)
    if curve_type is Polyline:
        return polyline_to_native(speckle_curve, blender_curve, scale)
    if curve_type is Arc:
        return arc_to_native(speckle_curve, blender_curve, scale)


def line_to_native(speckle_curve, name, scale=1.0):

    fme_line = fmeobjects.FMELine()

    return fme_line


def polyline_to_native(speckle_curve, name, scale=1.0):

    fme_polyline = fmeobjects.FMEPolyLine()

    return fme_polyline


def arc_to_native(rcurve, bcurve, scale):

    fme_oriented_arc = fmeobjects.FMEOrientedArc()
    fme_arc = fmeobjects.FMEArc()

    return fme_oriented_arc
