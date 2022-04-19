"""Reading from a Speckle Server."""

from typing import Dict, List, Union, Tuple
from fmeobjects import (
    FMEFeature,
    FMEGeometryTools,
    FMEGeometry,
    FMEMesh,
    FMEAggregate,
    FMELibrary,
    FMEAppearance,
    FMEPath,
)
from fme_speckle.converters.properties import rgba_from_argb_int

from fme_speckle.utilities.logging import error, trace, warn, log
from fme_speckle.features import (
    set_feature_attribute,
    set_feature_list_attribute,
    set_feature_rejection,
    set_speckle_feature_type,
)
from fme_speckle import FMEObject

from specklepy.api.credentials import StreamWrapper
from specklepy.api.client import SpeckleException
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations
from specklepy.objects.base import Base
from specklepy.objects.geometry import Mesh, Polyline, Point
from specklepy.objects.other import RenderMaterial

fme_appearance_library = FMELibrary()
fme_geometry_tools = FMEGeometryTools()
appearance_dictionary: Dict[str, int] = {}


class StreamReader(FMEObject):
    """Speckle Stream Reader.

    For each feature with an 'speckle_url' attribute will return FME features found
    at that URL. In addition to a Feature for every object in the stream, a feature
    will be added for any stream branch or commit referenced in the url.
    """

    def input(self, fme_inbound_feature: FMEFeature):
        """Process each incoming feature."""
        # if the stream_url is not set, return a rejected feature
        if fme_inbound_feature.isAttributeNull("speckle_url") or fme_inbound_feature.isAttributeMissing("speckle_url"):
            warn("No stream_url attribute found")
            set_feature_rejection(fme_inbound_feature, "No stream_url attribute")
            self.pyoutput(fme_inbound_feature)
            return

        stream_url = "{url}".format(url=fme_inbound_feature.getAttribute("speckle_url", str))

        stream_wrapper = StreamWrapper(stream_url)

        if stream_wrapper.stream_id:
            fme_stream_features = process_stream(stream_wrapper)

            if fme_stream_features:
                warn(f"Stream: {stream_wrapper.stream_id}")
                for fme_feature in fme_stream_features:
                    self.pyoutput(fme_feature)

        if stream_wrapper.commit_id:
            fme_commit_features = process_commit(stream_wrapper)

            if fme_commit_features:
                warn(f"Commit: {stream_wrapper.commit_id}")
                for fme_feature in fme_commit_features:
                    self.pyoutput(fme_feature)

        if stream_wrapper.branch_name:
            fme_branch_features = process_branch(stream_wrapper)

            if fme_branch_features:
                warn(f"Branch: {stream_wrapper.branch_name}")
                for fme_feature in fme_branch_features:
                    self.pyoutput(fme_feature)

        if stream_wrapper.object_id:
            fme_object_features = process_object_stream(stream_wrapper)

            if fme_object_features:
                warn(f"Object: {stream_wrapper.object_id}")
                for fme_feature in fme_object_features:
                    self.pyoutput(fme_feature)


def process_stream(stream_wrapper: StreamWrapper, resolve_branches: bool = False) -> Union[List[FMEFeature], None]:
    """Processes a Speckle stream and populates an FMEFeature."""
    # TODO: resolve_branches is not implemented
    # TODO: In general a process for cascading to all objects from a parent stream should be implemented

    fme_stream_feature = FMEFeature()

    set_speckle_feature_type(fme_stream_feature, "Speckle.Stream")
    set_feature_attribute(fme_stream_feature, "speckle_type", "stream")
    set_feature_attribute(fme_stream_feature, "id", stream_wrapper.stream_id)

    try:
        speckle_client = stream_wrapper.get_client()
        stream = speckle_client.stream.get(stream_wrapper.stream_id)

        set_feature_attribute(fme_stream_feature, "name", stream.name)
        set_feature_attribute(fme_stream_feature, "description", stream.description)
        set_feature_attribute(fme_stream_feature, "is_public", stream.isPublic)

    except SpeckleException as exception:
        error(exception.message)
        trace(exception.__traceback__)

        set_feature_rejection(fme_stream_feature, exception.message)

    return [fme_stream_feature]


def process_branch(stream_wrapper: StreamWrapper, resolve_commits: bool = False) -> Union[List[FMEFeature], None]:
    """Processes a Speckle branch and populates a list of FMEFeature.

    If getChildObjects is True, will also return a list of FMEFeatures for each
    object in the laatest commit for the branch.

    Args:
        wrapper (`StreamWrapper`): The wrapper object
        getChildObjects (bool, optional): Whether to get the child objects of the
            branch. Defaults to False.

    Returns:
        list[FMEFeature]: A list of FMEFeatures
    """
    feature_collection: list[FMEFeature] = []
    fme_branch_feature = FMEFeature()

    set_speckle_feature_type(fme_branch_feature, "Speckle.Branch")
    set_feature_attribute(fme_branch_feature, "speckle_type", "branch")

    branch_name = stream_wrapper.branch_name

    try:
        speckle_client = stream_wrapper.get_client()
        branch = speckle_client.branch.get(stream_wrapper.stream_id, branch_name, commits_limit=1)

        set_feature_attribute(fme_branch_feature, "name", branch.__getattribute__("name"))
        set_feature_attribute(fme_branch_feature, "commit_count", branch.__getattribute__("commits").totalCount, int)
        set_feature_attribute(fme_branch_feature, "id", branch.__getattribute__("id"))
        set_feature_attribute(fme_branch_feature, "description", branch.__getattribute__("description"))
        set_feature_attribute(fme_branch_feature, "last_commit", branch.__getattribute__("commits").cursor)

        if resolve_commits:
            for commit in branch.__getattribute__("commits").items:
                commitFeature = process_commit(
                    stream_wrapper, commit
                )  # ! This is wrong, process_commit will need an amended stream_wrapper
                feature_collection.extend(commitFeature)

    except SpeckleException as exception:
        error(exception.message)
        trace(exception.__traceback__)

        set_feature_rejection(fme_branch_feature, exception.message)

    feature_collection.append(fme_branch_feature)

    return feature_collection


def process_commit(stream_wrapper: StreamWrapper, process_child_objects: bool = True) -> List[FMEFeature]:
    """Processes a Speckle commit and populates an FMEFeature.

    If getChildObjects is True, will also return a list of FMEFeatures within the commit
    """
    feature_collection: list[FMEFeature] = []

    fme_commit_feature = FMEFeature()

    set_speckle_feature_type(fme_commit_feature, "Speckle.Commit")
    set_feature_attribute(fme_commit_feature, "speckle_type", "commit")
    set_feature_attribute(fme_commit_feature, "id", stream_wrapper.commit_id)

    try:
        client = stream_wrapper.get_client()
        commit = client.commit.get(stream_wrapper.stream_id, stream_wrapper.commit_id)

        set_feature_attribute(fme_commit_feature, "commit.message", commit.message)
        set_feature_attribute(fme_commit_feature, "commit.referenced_object", commit.referencedObject)
        set_feature_attribute(fme_commit_feature, "commit.source_application", commit.sourceApplication)
        set_feature_attribute(fme_commit_feature, "commit.total_children_count", commit.totalChildrenCount, int)
        set_feature_attribute(fme_commit_feature, "commit.author_name", commit.authorName)
        set_feature_attribute(fme_commit_feature, "commit.author_id", commit.authorId)
        set_feature_attribute(fme_commit_feature, "commit.branch_name", commit.branchName)
        set_feature_attribute(fme_commit_feature, "commit.created_at", commit.createdAt)
        set_feature_attribute(fme_commit_feature, "commit.author_avatar", commit.authorAvatar)

        if process_child_objects and commit.referencedObject:
            transport = stream_wrapper.get_transport()
            stream_data = operations.receive(commit.referencedObject, transport, MemoryTransport())
            child_object_features = flatten_objects(stream_data)

            if child_object_features:
                feature_collection.extend(child_object_features)

    except SpeckleException as exception:
        error(exception.message)
        trace(exception.__traceback__)

        set_feature_rejection(fme_commit_feature, exception.message)

    feature_collection.append(fme_commit_feature)

    return feature_collection


def process_object_stream(stream_wrapper: StreamWrapper) -> Union[List[FMEFeature], None]:
    """Processes a Speckle object stream and populates a list of FMEFeatures.

    Args:
        stream_wrapper (StreamWrapper): The wrapper object

    Returns:
        list[FMEFeature]: A list of FMEFeatures
    """
    feature_collection: list[FMEFeature] = []

    try:
        transport = stream_wrapper.get_transport()

        stream_base = operations.receive(stream_wrapper.object_id, transport, MemoryTransport())

        """
        To begin with lets just get all the objects in the stream and see what we can do with them.
        """

        nested_features = flatten_objects(stream_base)

        if nested_features is not None:
            feature_collection.extend(nested_features)

    except SpeckleException as exception:
        error(exception.message)
        trace(exception.__traceback__)

    return feature_collection


def process_attribute(
    attr_name: str,
    base_object: Base,
    fme_feature: FMEFeature,
    hierarchical_attr: str = "",
    feature_collection: List[FMEFeature] = [],
) -> None:
    """Processes an attribute of an object.

    Args:
        attr_name (str): The attribute to process.
        base_object (Base): The object to process the attribute of.
        fme_feature (FMEFeature): The feature to set the attribute on.
        hierarchical_attr (str): (Optional) The attribute name hierarchy to set. Defaults to "".
        feature_collection (list): (Optional) The collection to add the object to. Defaults to [].
    """
    label = attr_name if hierarchical_attr == "" else f"{hierarchical_attr}.{attr_name}"

    try:
        attr_value = base_object[attr_name]
        value_type = type(attr_value)

        if "displayMesh" in attr_name or "displayValue" in attr_name or isinstance(base_object, (Mesh, Polyline)):
            # special case attribute
            renderMaterial = getattr(base_object, "renderMaterial", None)
            build_display_eometry(
                base_object if isinstance(base_object, (Mesh, Polyline)) else attr_value, fme_feature, renderMaterial
            )

        elif isinstance(attr_value, Base):
            attributes = attr_value.get_member_names()
            for attr_name in attributes:
                process_attribute(attr_name, attr_value, fme_feature, label, feature_collection)

        elif value_type == list:

            for idx, element in enumerate(attr_value):  # ? idx is not used

                if element is None:
                    pass
                elif "displayMesh" in label or "renderMaterial" in label:
                    # Handling older streams display structure
                    pass
                elif isinstance(element, (Mesh, Polyline)):  # TODO Expand to can_convert to FMEFeature vs just Mesh
                    create_object(element, feature_collection, base_object)
                    set_feature_list_attribute(fme_feature, label, element.id)
                    pass

                elif isinstance(element, Base):
                    """Create a new feature, add parent reference and store child reference list variable"""

                    set_feature_list_attribute(fme_feature, label, element.id)
                    flatten_objects(element, feature_collection, base_object.id)

                elif isinstance(element, object):
                    log(f"{element} is an object")
                    # TODO: handle object list elements
                elif isinstance(element, list):
                    log(f"{element} is an list")
                    # TODO: handle list elements
                else:
                    set_feature_list_attribute(fme_feature, label, element)
        else:
            if "displayMesh" not in label and "displayValue" not in label and "renderMaterial" not in label:
                set_feature_attribute(fme_feature, label, attr_value, value_type)

    except KeyError:
        # Attribute not found despite being a member of the object
        pass

    except TypeError:
        warn("Unable to set attribute: " + label)
        set_feature_attribute(fme_feature, label, "...")


def create_object(
    base_object: Base, feature_collection: List[FMEFeature] = [], parent_base_object: Union[Base, None] = None
) -> Union[List[FMEFeature], None]:
    """Maps an incoming Speckle object to a FMEFeature.

    Args:
        base_object (Base): The object to map.
        feature_collection (list): The collection to add the object to. Defaults to [].
        parent_base_object (Base, optional): The parent object. Defaults to None.

    Returns:
        list[FMEFeature]: A list of FMEFeatures
    """
    if isinstance(base_object, Base):
        fme_feature = FMEFeature()

        set_feature_attribute(fme_feature, "speckle_type", base_object.speckle_type)
        set_feature_attribute(fme_feature, "id", base_object.id)
        set_speckle_feature_type(fme_feature, base_object.speckle_type)

        if isinstance(base_object, (Polyline, Mesh)):
            build_display_eometry(base_object, fme_feature)

        if isinstance(parent_base_object, Base):
            set_feature_attribute(fme_feature, "parent_id", parent_base_object.id)

        feature_collection.append(fme_feature)


def flatten_objects(
    base_object: Base, feature_collection: List[FMEFeature] = [], fme_parent_id: Union[str, None] = None
) -> Union[List[FMEFeature], None]:
    """Recursively maps an incoming Speckle object to FMEFeatures.

    Args:
        base_object (Base): The object to map.
        feature_collection (list): The collection to add the object to. Defaults to [].
        fme_parent_id (str, None, optional): The parent object. Defaults to None.
    """
    if isinstance(base_object, Base):

        feature = FMEFeature()

        set_feature_attribute(feature, "speckle_type", base_object.speckle_type)
        set_feature_attribute(feature, "id", base_object.id)
        set_speckle_feature_type(feature, base_object.speckle_type)

        attributes = base_object.get_member_names()

        if fme_parent_id is not None:
            set_feature_attribute(feature, "parent_id", fme_parent_id)

        for attr_name in attributes:
            process_attribute(attr_name, base_object, feature, "", feature_collection)

        feature_collection.append(feature)

    return feature_collection


def map_geometry(display_geometry: Union[Polyline, Mesh]) -> Union[FMEMesh, FMEPath, None]:
    """Return the correct FMEGeometry type for the display geometry.

    Args:
        display (Union[Polyline, Mesh]): _description_

    Returns:
        FMEGeometry: Any of the supported FMEGeometry types.

    Raises:
        TypeError: The fallback of FMEGeometry is an abstract class only and cant be instantiated.
    """
    if isinstance(display_geometry, Mesh):
        fme_geometry = FMEMesh()
        build_mesh(display_geometry, fme_geometry)
    elif isinstance(display_geometry, Polyline):
        fme_geometry = FMEPath()
        build_path(display_geometry, fme_geometry)

    display_params_to_geometry(display_geometry, fme_geometry)

    return fme_geometry


def display_params_to_geometry(display_geometry: Base, fme_geometry: FMEGeometry) -> None:
    """Adds any attributes adjacent to the displayValue of a speckle object to the geometry as traits.

    Args:
        display_geometry (Display): The display to convert.
        fme_geometry (FMEGeometry): The geometry to set the display parameters on.
    """
    if isinstance(display_geometry, Base) and isinstance(fme_geometry, FMEGeometry):
        attributes = display_geometry.get_member_names()
        for attr_name in attributes:
            attr_value = getattr(display_geometry, attr_name)
            if isinstance(attr_value, (float, int, str, bool)):
                fme_geometry.setTrait(attr_name, attr_value)


def apply_render_raterial(display_geometry: Base, render_material: RenderMaterial) -> None:
    """Handles the different attributes that carryt the render material."""
    if not hasattr(display_geometry, "renderMaterial") or getattr(display_geometry, "renderMaterial", None) is None:
        if render_material:
            display_geometry.renderMaterial = render_material


def build_display_eometry(
    display_geometry: Union[Polyline, List[Polyline], Mesh, List[Mesh]],
    fme_feature: FMEFeature,
    renderMaterial: Union[RenderMaterial, None] = None,
) -> None:
    """Converts the displayValue from speckle Base object to an FME geometry and adds it to the feature.

    Args:
        display_geometry (Union[Polyline, List[Polyline], Mesh, List[Mesh]]): Speckle has either a single Value
            or a list of values. Values discovered so far are Polyline and Mesh.
        fme_feature (FMEFeature): The FME feature to add the geometry to.
        renderMaterial (Union[RenderMaterial, None], optional): The render material to apply to the geometry.
    """
    if not isinstance(display_geometry, list):
        if renderMaterial:
            apply_render_raterial(display_geometry, renderMaterial)
        fme_geometry = map_geometry(display_geometry)
        if fme_geometry:
            fme_feature.setGeometry(fme_geometry)

    elif isinstance(display_geometry, list):
        if len(display_geometry) == 0:
            return

        elif len(display_geometry) == 1:
            if renderMaterial:
                apply_render_raterial(display_geometry[0], renderMaterial)
            fme_geometry = map_geometry(display_geometry[0])
            if fme_geometry:
                fme_feature.setGeometry(fme_geometry)

        elif len(display_geometry) > 1:
            fme_aggregate = FMEAggregate()
            for part in display_geometry:
                if renderMaterial:
                    apply_render_raterial(part, renderMaterial)
                fme_geometry = map_geometry(part)
                if fme_geometry:
                    fme_aggregate.appendPart(fme_geometry)
            if fme_aggregate.numParts() > 0:
                fme_feature.setGeometry(fme_aggregate)


def points_to_tuple(point: Point) -> Tuple[float, float, float]:
    """Converts a speckle Point to a tuple.

    Args:
        point (Point): The point to convert.

    Returns:
        (float, float, float): The converted point. The tuple is (x, y, z).
    """
    return (point.x, point.y, point.z)


def build_path(path: Polyline, fme_path: FMEPath) -> None:
    """With a speckle Polyline object, build an FME Path object.

    Assumes 3D coordinates.

    Args:
        path (Polyline): _description_
        geom (FMEPath): _description_
    """

    points_list = list(map(points_to_tuple, path.as_points()))

    fme_path.extendToPointsXYZ(points_list)

    if path.closed:
        first_point = points_list[0]
        fme_path.extendToPointXYZ(first_point[0], first_point[1], first_point[2])


def build_mesh(mesh: Mesh, fme_mesh: FMEMesh) -> None:
    """Builds the mesh geometry.

    Any found material is added to the appearance library. Assumes no duplicate
    material id from speckle.

    Args:
        mesh (Mesh): The mesh to build the geometry from.
        geom (FMEMesh): The FMEMesh to add the geometry to.
    """

    mesh_faces = getattr(mesh, "faces")
    mesh_vertices = getattr(mesh, "vertices")
    render_material = getattr(mesh, "renderMaterial", None)

    appearance_reference = 0

    if render_material and render_material.id:
        if render_material.id in appearance_dictionary:
            appearance_reference = appearance_dictionary[render_material.id]
            fme_mesh.setAppearanceReference(appearance_reference, True)

        elif isinstance(render_material, RenderMaterial):
            fme_appearance = FMEAppearance()

            if render_material.name:
                fme_appearance.setName(render_material.name)

            diffuse = rgba_from_argb_int(render_material.diffuse)
            emmisive = rgba_from_argb_int(render_material.emissive)

            fme_appearance.setAlpha(render_material.opacity)
            fme_appearance.setColorDiffuse(diffuse["r"], diffuse["g"], diffuse["b"])
            fme_appearance.setColorAmbient(diffuse["r"] / 2, diffuse["g"] / 2, diffuse["b"] / 2)
            fme_appearance.setColorEmissive(emmisive["r"], emmisive["g"], emmisive["b"])
            fme_appearance.setShininess(render_material.metalness)

            appearance_reference = fme_appearance_library.addAppearance(fme_appearance)
            appearance_dictionary[render_material.id] = appearance_reference

            fme_mesh.setAppearanceReference(appearance_reference, True)
            fme_mesh.setAppearanceReference(appearance_reference, False)

    for vertex in range(int(len(mesh_vertices) / 3)):
        fme_mesh.appendVertex(mesh_vertices[vertex * 3], mesh_vertices[vertex * 3 + 1], mesh_vertices[vertex * 3 + 2])

    for face in range(int(len(mesh_faces) / 4)):
        fme_mesh.addMeshPart(
            appearance_reference,
            [mesh_faces[face * 4 + 1], mesh_faces[face * 4 + 2], mesh_faces[face * 4 + 3]],
            None,
            None,
        )

    fme_mesh.optimizeVertexPool
    fme_mesh.resolvePartDefaults
