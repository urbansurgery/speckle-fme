# This is the default content of the PythonCaller transformer in FME.
# Replace this with the pointer to the external implementation:
#
# e.g. from fme_speckle.readers import StreamReader
#
# and replace FeatureProcessor class name with whatever you rename that class as.

import fme
import fmeobjects

class FeatureProcessor(object):
    """Template Class Interface:
    When using this class, make sure its name is set as the value of the 'Class
    to Process Features' transformer parameter.
    """

    def __init__(self):
        """Base constructor for class members."""
        pass

    def input(self, feature):
        """This method is called for each FME Feature entering the 
        PythonCaller. If knowledge of all input Features is not required for 
        processing, then the processed Feature can be emitted from this method 
        through self.pyoutput(). Otherwise, the input FME Feature should be 
        cached to a list class member and processed in process_group() when 
        'Group by' attributes(s) are specified, or the close() method.

        :param fmeobjects.FMEFeature feature: FME Feature entering the 
            transformer.
        """
        self.pyoutput(feature)

    def close(self):
        """This method is called once all the FME Features have been processed
        from input().
        """
        pass

    def process_group(self):
        """When 'Group By' attribute(s) are specified, this method is called 
        once all the FME Features in a current group have been sent to input().

        FME Features sent to input() should generally be cached for group-by 
        processing in this method when knowledge of all Features is required. 
        The resulting Feature(s) from the group-by processing should be emitted 
        through self.pyoutput().

        FME will continue calling input() a number of times followed
        by process_group() for each 'Group By' attribute, so this 
        implementation should reset any class members for the next group.
        """
        pass
