"""Generic Client class for FME Speckle."""

from fmeobjects import FMEFeature, kFMEFeatureTypeAttr
from specklepy.api import operations
from specklepy.api.client import SpeckleClient, SpeckleException
from specklepy.api.credentials import get_default_account
from specklepy.api.models import Stream
from specklepy.transports.server import ServerTransport

from fme_speckle import FMEObject


class DefaultClient(FMEObject):
    """Generic Client class for FME Speckle."""

    def __init__(self, *args):
        """Constructor."""
        account = get_default_account()
        client = SpeckleClient()
        client.authenticate(token=account.token)

        self.client = client
        self.account = account

        pass

    def input(self, feature):
        """Process each feature."""
        client = FMEFeature()
        client.setAttribute(kFMEFeatureTypeAttr, "SpeckleClient")
        client.setFeatureType("SpeckleClient")

        client.setAttribute("_token", self.account.token)
        client.setAttribute("_refreshToken", self.account.refreshToken)

        client.setAttribute("host", self.client.url)
        client.setAttribute("authenticated", self.client.me is not None)
        client.setAttribute("userId", self.account.userInfo.id)
        client.setAttribute("name", self.account.userInfo.name)
        client.setAttribute("email", self.account.userInfo.email)

        self.pyoutput(client)

        pass
