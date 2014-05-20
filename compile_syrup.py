import json
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
from pysyrup import Syrup

def main(settings_path):
    with open(settings_path) as f:
        settings = json.loads(f.read())
    syrup_settings = settings["syrup"]
    #sys.path.append(syrup_settings["syrup_path"])
    #sys.path.append('..')

    syrup = Syrup(syrup_settings)
    syrup.read()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit("ERROR: Usage: python compile_syrup.py settings.json")
