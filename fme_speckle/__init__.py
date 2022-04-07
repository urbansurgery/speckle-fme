import fmeobjects
from fme_speckle.utilities.logging import warn, error, log

# stub the FME Python object types
class object(object):
    """The FME Python Caller augmented base object"""

    def pyoutput(self, pyoutput) -> None:
        """The Default output function"""


error("Speckle Initializing...")
