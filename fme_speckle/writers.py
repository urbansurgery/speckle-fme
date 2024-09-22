"""Writing to a Speckle Server."""

from typing import List
from fmeobjects import FMEFeature, kFMEFeatureTypeAttr

from specklepy.api.credentials import StreamWrapper
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
from specklepy.objects.base import Base

from fme_speckle.converters.to_speckle import convert_features_to_speckle, feature_to_speckle

from fme_speckle.utilities.logging import error, warn, log, trace

from fme_speckle.features import set_feature_attribute, set_feature_rejection

from fme_speckle import FMEObject


class StreamWriter(FMEObject):
    """Python Caller class."""

    def __init__(self):
        """Constructor.

        feature_list keeps track of the cumulative features received by the writer.
        commits is a list of features representing the commits sent to the server.
        """
        self.feature_list: List[Base] = []
        self.commits: List[FMEFeature] = []
        pass

    def input(self, fme_inbound_feature: FMEFeature):
        """Add a feature to the list of features to be sent to the server.

        This will be partitioned by the Grouping policy of the host PythonCaller.
        This policy should ideally be set to Group by Speckle URL. If it is not,
        then the features will be sent to the stream specified by the first feature.

        Features will be added to the list if they have a speckle_url attribute.
        """
        if fme_inbound_feature.isAttributeNull("speckle_url") or fme_inbound_feature.isAttributeMissing("speckle_url"):
            warn("No stream_url attribute found")
            set_feature_rejection(fme_inbound_feature, "No stream_url attribute")
            self.pyoutput(fme_inbound_feature)
            return

        try:
            converted = feature_to_speckle(fme_inbound_feature)
            if converted is None:
                set_feature_rejection(fme_inbound_feature, "Failed to convert")
                warn("Failed to convert")
                raise Exception("Failed to convert")
            else:
                converted.speckle_url = fme_inbound_feature.getAttribute("speckle_url")
                set_feature_attribute(fme_inbound_feature, "converted", True)
                self.feature_list.append(converted)
        except Exception as ex:

            if fme_inbound_feature.isAttributeNull("speckle_url") or fme_inbound_feature.isAttributeMissing(
                "speckle_url"
            ):
                set_feature_rejection(fme_inbound_feature, "Failed to convert")

        self.pyoutput(fme_inbound_feature)

    def process_group(self):
        """For each feature group as divided at the Caller level, send a speckle commit.

        Resets the feature list ready for the next group.

        Outputs a feature representing the commit per group with success details.
        """
        commit = FMEFeature()
        commit.setAttribute(kFMEFeatureTypeAttr, "SpeckleCommit")

        if len(self.feature_list) == 0:
            set_feature_rejection(commit, "No features converted, so no commit to send.")
            self.pyoutput(commit)
            return

        label = f"commit {len(self.commits) + 1}: {len(self.feature_list)} features \
            committed to {getattr(self.feature_list[0],'speckle_url',None)}"

        set_feature_attribute(commit, "message", label)
        set_feature_attribute(commit, "features", len(self.feature_list))

        speckle_url = getattr(self.feature_list[0], "speckle_url", None)

        if speckle_url is None:
            # No Url found, so no commit to send.
            set_feature_rejection(commit, "No Url found, so no commit to send.")
            self.commits.append(commit)
            self.pyoutput(commit)
            return

        stream_wrapper = StreamWrapper(speckle_url)
        stream_id = stream_wrapper.stream_id

        self.speckle_client = stream_wrapper.get_client()

        base_obj = Base()
        features = self.feature_list
        base_obj["@fruit"] = "banana"
        base_obj["@features"] = features

        transport = ServerTransport(stream_id=stream_id, client=self.speckle_client, url=speckle_url)

        warn(str(vars(stream_wrapper)))

        object_id = ""

        # warn(str(base_obj["features"]))

        # error(str(dir(base_obj.id)))

        warn(str(self.speckle_client))

        try:
            object_id = operations.send(base=base_obj, transports=[transport])
        except Exception as e:
            set_feature_rejection(commit, "Failed")
            trace(e.__traceback__)
            error(str(e))

        if object_id != "":
            try:

                # you can now create a commit on your stream with this object
                commit_id = self.speckle_client.commit.create(
                    stream_id=stream_id,
                    object_id=object_id,
                    branch_name=stream_wrapper.branch_name,
                    message=f"{len(features)} features committed to {stream_wrapper.branch_name}",
                    source_application="FME",
                )
                set_feature_attribute(commit, "status", "Success")
                set_feature_attribute(commit, "commit", commit_id)
                log("Successfully sent data to stream: " + stream_id)
            except:
                set_feature_attribute(commit, "status", "Fail")
                set_feature_rejection(commit, "Failed")
                error("Error creating commit")

        self.commits.append(commit)

        warn(label)

        self.pyoutput(commit)
        self.feature_list = []

    def close(self):
        """Report the number of commits."""
        error(f"{len(self.commits)} commits sent.")
        pass
