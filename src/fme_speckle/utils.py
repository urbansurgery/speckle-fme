import sys
from importlib.metadata import version, PackageNotFoundError
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_default_account

def basic_speckle_installation_check(logger):
  logger.logMessageString(f"Python version: {sys.version}")

  try:
    specklepy_version = version("specklepy")
    logger.logMessageString(f"Specklepy version: {specklepy_version}")
  except PackageNotFoundError:
    logger.logMessageString("Specklepy is not installed or version information is unavailable.")

  try:
    account = get_default_account()
    if account:
      logger.logMessageString(f"Default account found: {account.serverInfo.name}")
    else:
      logger.logMessageString("No default account found. You may need to add an account using speckle-cli.")

    client = SpeckleClient(host=account.serverInfo.host)
    logger.logMessageString("SpeckleClient initialized successfully.")

    logger.logMessageString("Installation test passed.")
  except Exception as e:
    logger.logMessageString(f"An error occurred: {str(e)}")
    logger.logMessageString("Installation test failed.")