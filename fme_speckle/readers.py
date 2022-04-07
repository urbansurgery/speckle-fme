import fmeobjects
import traceback
import pprint
import json

logger = fmeobjects.FMELogFile()
pp = pprint.PrettyPrinter(indent=2)

from specklepy.api.credentials import StreamWrapper
from specklepy.api.resources.commit import Resource
from specklepy.api.client import SpeckleException
from specklepy.transports.memory import MemoryTransport
from specklepy.api import operations
from specklepy.objects.base import Base

from .streams import explore_commit, get_objects_collections


class StreamReader(object):
    def __init__(self):
        pass

    def input(self, feature):

        stream_url = feature.getAttribute("stream_url")

        if stream_url is None:
            return

        # print ("Stream URL: " + stream_url)

        wrapper = StreamWrapper(stream_url)

        account = wrapper.get_account()
        client = wrapper.get_client()
        transport = wrapper.get_transport()

        # logger.logMessageString(str(transport),3)
        # logger.logMessageString(str(account),3)
        # logger.logMessageString(str(client),3)

        stream_id = wrapper.stream_id
        commit_id = wrapper.commit_id
        branch_name = wrapper.branch_name
        object_id = wrapper.object_id

        # logger.logMessageString(str(wrapper.type),2)

        # print ("Stream ID: " + (stream_id if stream_id else "No Stream"))
        # print ("Commit ID: " + (commit_id if commit_id else "No Commit"))
        # print ("Object ID: " + (object_id if object_id else "No Object"))
        # print ("Branch Name: " + (branch_name if branch_name else "No Branch"))

        wrapper_type = wrapper.type

        if stream_id:
            streamFeature = fmeobjects.FMEFeature()
            streamFeature.setFeatureType("SpeckleStream")
            streamFeature.setAttribute(fmeobjects.kFMEFeatureTypeAttr, "SpeckleStream")
            streamFeature.setAttribute("speckle_type", "stream")

            streamFeature.setAttribute("stream_id", stream_id)

            try:
                stream = client.stream.get(stream_id)

                streamFeature.setAttribute("stream_name", stream.name)
                streamFeature.setAttribute("description", stream.description)
                streamFeature.setAttribute("is_public", stream.isPublic)

            except SpeckleException as e:
                logger.logMessageString(str(e.message), 2)
                logger.logMessageString(str(traceback.print_tb(e.__traceback__)), 2)

                streamFeature.setAttribute("RejectedReason", e.message)

            self.pyoutput(streamFeature)

        if commit_id:
            commitFeature = fmeobjects.FMEFeature()
            commitFeature.setFeatureType("SpeckleCommit")
            commitFeature.setAttribute(fmeobjects.kFMEFeatureTypeAttr, "SpeckleCommit")
            commitFeature.setAttribute("speckle_type", "commit")
            commitFeature.setAttribute("commit_id", commit_id)

            try:
                commit = client.commit.get(stream_id, commit_id)

                commitFeature.setAttribute("commit_message", commit.message)
                commitFeature.setAttribute("commit_referenced_object", commit.referencedObject)
                commitFeature.setAttribute("commit_source_application", commit.sourceApplication)
                commitFeature.setAttribute("commit_total_children_count", commit.totalChildrenCount)
                commitFeature.setAttribute("commit_author_name", commit.authorName)
                commitFeature.setAttribute("commit_author_id", commit.authorId)
                commitFeature.setAttribute("commit_branch_name", commit.branchName)
                commitFeature.setAttribute("commit_created_at", commit.createdAt)
                commitFeature.setAttribute("commit_author_avatar", commit.authorAvatar)

                stream_data = operations.receive(commit.referencedObject, transport, MemoryTransport())
                # speckle_objects = get_objects_collections(stream_data)

                speckle_objects = explore_commit(stream_data)

                for f in speckle_objects:
                    self.pyoutput(f)

            except SpeckleException as e:
                logger.logMessageString(str(e.message), 2)
                logger.logMessageString(str(traceback.print_tb(e.__traceback__)), 2)

                commitFeature.setAttribute("RejectedReason", e.message)

            self.pyoutput(commitFeature)

        if branch_name:
            branchFeature = fmeobjects.FMEFeature()
            branchFeature.setFeatureType("SpeckleBranch")
            branchFeature.setAttribute(fmeobjects.kFMEFeatureTypeAttr, "SpeckleBranch")
            branchFeature.setAttribute("speckle_type", "branch")

            branchFeature.setAttribute("branch_name", branch_name)
            try:
                branch = client.branch.get(stream_id, branch_name, commits_limit=1)

                branchFeature.setAttribute("branch_id", branch.id)
                branchFeature.setAttribute("branch_description", branch.description)
                branchFeature.setAttribute("commit_count", branch.commits.totalCount)
                branchFeature.setAttribute("last_commit", branch.commits.cursor)

            except SpeckleException as e:
                logger.logMessageString(str(e.message), 2)
                logger.logMessageString(str(traceback.print_tb(e.__traceback__)), 2)

                branchFeature.setAttribute("RejectedReason", e.message)

            self.pyoutput(branchFeature)

        if object_id:
            objectFeature = fmeobjects.FMEFeature()
            objectFeature.setFeatureType("SpeckleObject")
            objectFeature.setAttribute(fmeobjects.kFMEFeatureTypeAttr, "SpeckleObject")
            objectFeature.setAttribute("speckle_type", "object")

            objectFeature.setAttribute("object_id", object_id)

            try:
                object_stream = operations.receive(object_id, transport, MemoryTransport())
                # object = client.object.get(stream_id, object_id)

                # {
                # 'speckle_type': 'Objects.BuiltElements.Wall:Objects.BuiltElements.Revit.RevitWall',
                # 'totalChildrenCount': 3,
                # 'id': '10ccf0ccdb46f79a24400319a71685b5',
                # 'type': 'Wall - Timber Clad',
                # 'level': Base(id: 4e306457698c6086b59c9a81922b6b10, speckle_type: Objects.BuiltElements.Level:Objects.BuiltElements.Revit.RevitLevel, totalChildrenCount: 0),
                # '_units': 'mm',
                # 'family': 'Basic Wall',
                # 'height': 3900.0000000002296,
                # 'flipped': True,
                # 'baseLine': Line(id: 2aa97c812ef7ddf8be7b61a123b67927, speckle_type: Objects.Geometry.Line, totalChildrenCount: 0),
                # 'elements': None,
                # 'topLevel': Base(id: a1166cf67c977ebf1e638252debb4bc2, speckle_type: Objects.BuiltElements.Level:Objects.BuiltElements.Revit.RevitLevel, totalChildrenCount: 0),
                # 'elementId': '849032',
                # 'topOffset': -299.99999999977047,
                # 'baseOffset': -1200,
                # 'parameters': Base(id: 55504a70fe9fefc786b277705a6889fd, speckle_type: Base, totalChildrenCount: 0),
                # 'structural': False,
                # 'displayMesh': Mesh(id: 8db5520560fb1ef8682b447b98ba1b7c, speckle_type: Objects.Geometry.Mesh, totalChildrenCount: 0),
                # 'applicationId': '98e2f96c-ccbd-4abb-a697-e7e5136106ee-000cf488',
                # 'renderMaterial': RenderMaterial(id: b6b8998f448a97c85c188ecc617dd453, speckle_type: Objects.Other.RenderMaterial, totalChildrenCount: 0)
                # }

                # print (object.__dict__)

                """
        To begin with lets just get all the objects in the stream and see what we can do with them.
        """

                print(object_stream)
                # speckle_objects = get_flattened_objects(object_stream)

                # list_of_types = ['str','float','int','bool']

                # print (object.speckle_type)

                # for attribute in object.__dict__:
                #   print (attribute, type(object[attribute]), object[attribute])
                #   # objectFeature.setAttribute('attribute', object[attribute])

            except SpeckleException as e:
                logger.logMessageString(str(e.message), 2)
                logger.logMessageString(str(traceback.print_tb(e.__traceback__)), 2)

                objectFeature.setAttribute("RejectedReason", e.message)

            self.pyoutput(objectFeature)
        pass
