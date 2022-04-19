"""Testing stream processing functions."""

from functools import reduce
import string
import fmeobjects
from fmeobjects import FMEMesh, FMEFeature, FMEGeometry

"""
Stream operators
"""
from itertools import chain
from typing import Dict, List

from specklepy.objects.geometry import Base

from .converters.to_native import can_convert_to_native

OBJECTS_BY_TYPE = {}  # type: Dict[str, List[Base]]


def explore_commit(base: Base) -> List:
    """Process a base commit object and explore its dynamic data.

    Args:
        base (Base): The base commit object.

    Returns:
        List: A list of objects.
    """
    objects = []
    counter = 0

    for type_name in base.get_dynamic_member_names():
        value = base[type_name]

        if isinstance(value, list):
            for item in value:
                if isinstance(item, Base):

                    feature = fmeobjects.FMEFeature()

                    feature.setAttribute(fmeobjects.kFMEFeatureTypeAttr, item.speckle_type)
                    feature.setAttribute("speckle_type", item.speckle_type)
                    feature.setAttribute("speckle.id", item.id)
                    feature.setAttribute("commit.hierarchy_id", counter)

                    for prop in item.get_member_names():
                        value = item.__getattribute__(prop)

                        if value is not None:
                            # TODO: handle lists of properties
                            feature.setAttribute("prop." + prop, str(value))
                        elif prop not in ("displayMesh", "displayValue"):
                            # adds a null value for the prop
                            feature.setAttributeNullWithType(prop, fmeobjects.FME_ATTR_STRING)

                        if prop in ("displayMesh", "displayValue"):

                            # is a mesh
                            # is a list of meshes
                            # is an empty list
                            meshes = process_display(prop, value)

                            geometry = reduce(merge_meshes, meshes, fmeobjects.FMEMesh())

                            feature.setGeometry(geometry)

                            # faces = value.__getattribute__("faces")
                            # vertices = value.__getattribute__("vertices")

                            # for v in range(int(len(vertices) / 3)):
                            #     mesh.appendVertex(vertices[v * 3], vertices[v * 3 + 1], vertices[v * 3 + 2])

                            # for f in range(int(len(faces) / 4)):
                            #     mesh.addMeshPart(0, [faces[f * 4 + 1], faces[f * 4 + 2], faces[f * 4 + 3]], None, None)

                            # feature.setGeometry(mesh)

                    if can_convert_to_native:
                        objects.append(feature)
                    counter += 1

    return objects


def process_display(p: str, v: any) -> List:  # type: ignore
    """New API Display property should be a list of display values."""
    if isinstance(v, List):
        return v
    if p == "displayMesh":
        return [v]
    if v is None:
        return []


def merge_meshes(a: FMEMesh, b) -> FMEMesh:
    """Merge two meshes."""
    mesh = construct_mesh(b)
    a.appendMesh(mesh)
    return a


def construct_mesh(meshValue) -> FMEMesh:
    """Construct a FME mesh from a Speckle mesh."""
    mesh = FMEMesh()
    mesh = add_vertices(mesh, meshValue)
    mesh = add_faces(mesh, meshValue)
    pass


def add_vertices(fme_mesh: FMEMesh, speckle_mesh) -> FMEMesh:
    """Add vertices to a FME mesh."""
    s_vertices = speckle_mesh.__getattribute__("vertices")

    if s_vertices and len(s_vertices) > 0:
        for i in range(0, len(s_vertices), 3):
            fme_mesh.appendVertex(s_vertices[i], s_vertices[i + 1], s_vertices[i + 2])


def add_faces(fme_mesh: FMEMesh, speckle_mesh) -> FMEMesh:
    """Add faces to a FME mesh."""

    s_faces = speckle_mesh.__getattribute__("faces")

    if s_faces and len(s_faces) > 0:
        i = 0
        while i < len(s_faces):
            n = s_faces[i]
            if n < 3:
                n += 3  # 0 -> 3, 1 -> 4

            i += 1
            try:
                fme_mesh.addMeshPart(0, s_faces[i : i + n], None, None)
            except Exception as e:
                print(e)

            i += 1


def get_objects_collections(base) -> Dict:
    """Populate a dictionary of objects by member types of a commit."""
    member_type_collections = OBJECTS_BY_TYPE

    for type_name in base.get_dynamic_member_names():

        value = base[type_name]
        collection = create_collection(type_name)

        if isinstance(value, list):
            member_type_collections[type_name] = get_objects_nested_lists(value, collection)

        if isinstance(value, Base):
            member_type_collections[type_name] = get_objects_collections_recursive(value, collection)

    return member_type_collections


def create_collection(name):
    """Stub function to populate a new list in the global collection."""
    if name in OBJECTS_BY_TYPE:
        collection = OBJECTS_BY_TYPE[name]
    else:
        collection = OBJECTS_BY_TYPE[name] = []

    return collection


def get_objects_nested_lists(items, parent_collection=None) -> List:
    """Returns the Lists from within nested list."""
    objects = []

    if isinstance(items[0], list):
        items = list(chain.from_iterable(items))
        objects.extend(get_objects_nested_lists(items, parent_collection))
    else:
        objects = [
            get_objects_collections_recursive(item, parent_collection) for item in items if isinstance(item, Base)
        ]

    return objects


def get_objects_collections_recursive(base, parent_collection=None) -> List:
    """Returns a list of objects within the Base object's dynamic data."""
    if can_convert_to_native(base):
        return [base]

    objects = []

    for name in base.get_dynamic_member_names():
        value = base[name]

        if isinstance(value, list):
            for item in value:
                if isinstance(item, Base):
                    objects.append(item)
        if isinstance(value, Base):
            collection = OBJECTS_BY_TYPE.get(name)
            if not collection:
                collection = create_collection(name)

            objects.append({name: get_objects_collections_recursive(value, collection)})

    return objects
