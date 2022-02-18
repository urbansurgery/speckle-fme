import fmeobjects

from fme_speckle.functions import get_scale_length, _report

from specklepy.objects.other import *
from specklepy.objects.geometry import *

SUPPORTED_CURVES = (Line, Polyline, Arc)

CAN_CONVERT_TO_NATIVE = (
    Mesh,
    *SUPPORTED_CURVES,
)

def can_convert_to_native(speckle_object):
    if type(speckle_object) in CAN_CONVERT_TO_NATIVE:
        return True
    display = getattr(
        speckle_object, "displayMesh", getattr(speckle_object, "displayValue", None)
    )
    if display:
        return True

    _report(f"Could not convert unsupported Speckle object: {speckle_object}")
    return False


def convert_to_native(speckle_object, name=None, fme_object=None):
    speckle_type = type(speckle_object)
    speckle_name = (
        name
        or getattr(speckle_object, "name", None)
        or speckle_object.speckle_type + f" -- {speckle_object.id}"
    )
    if speckle_type not in CAN_CONVERT_TO_NATIVE:
        display = getattr(
            speckle_object, "displayMesh", getattr(speckle_object, "displayValue", None)
        )
        if not display:
            _report(f"Could not convert unsupported Speckle object: {speckle_object}")
            return

        if isinstance(display, list):
            for item in display:
                item.parent_speckle_type = speckle_object.speckle_type
                convert_to_native(item)
        else:
            display.parent_speckle_type = speckle_object.speckle_type
            return convert_to_native(display, speckle_name)

    units = getattr(speckle_object, "units", None)
    if units:
        scale = get_scale_length(units)

    try:
        if speckle_type is Mesh:
            obj_data = mesh_to_native(speckle_object, name=speckle_name, scale=scale)
       
        elif speckle_type in SUPPORTED_CURVES:
            obj_data = curve_to_native(speckle_object, name=speckle_name, scale=scale)
       
        else:
            _report(f"Unsupported type {speckle_type}")
            return None
    except Exception as ex:  # conversion error
        _report(f"Error converting {speckle_object} \n{ex}")
        return None

    fme_object.speckle.object_id = str(speckle_object.id)
    fme_object.speckle.enabled = True
    
    return fme_object
  
  
def mesh_to_native(speckle_mesh, name, scale=1.0):

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