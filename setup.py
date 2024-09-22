import sys
import subprocess
import importlib

def install_and_import(package):
  try:
    # Try to import the package
    return importlib.import_module(package)
  except ModuleNotFoundError:
    print(f"{package} not found, attempting to install...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    return importlib.import_module(package)

def setup_dependencies():
  # List of packages to check and install if missing
  dependencies = ["specklepy"]  # Add other dependencies as needed

  for package in dependencies:
    install_and_import(package)

if __name__ == "__main__":
  setup_dependencies()
  print("All dependencies are installed.")
