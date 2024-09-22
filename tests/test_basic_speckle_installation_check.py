import sys
import os
from .logger import TestLogger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fme_speckle.utils import basic_speckle_installation_check

def test_basic_speckle_installation_check():
  test_logger = TestLogger()

  # Call the function with the test logger
  basic_speckle_installation_check(test_logger)

  # Verify the log messages
  assert "Python version" in test_logger.get_messages()[0]
