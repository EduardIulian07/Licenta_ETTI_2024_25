import sys
import os

# Adaugă 'utils/' în sys.path
utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..')
sys.path.insert(0, utils_path)

from dependencies.dependencies import *