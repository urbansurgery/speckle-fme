
from devtools import debug

# the speckle.objects module exposes all speckle provided classes
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_local_accounts, get_default_account

account = get_default_account()

# initialise the client
client = SpeckleClient(host=account.serverInfo.url, use_ssl=True)
client.authenticate(token=account.token)

debug(client)
