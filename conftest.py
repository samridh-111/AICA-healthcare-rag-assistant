import sys
import os

# Ensure the project root is on sys.path so `from backend.x import y` works
# when running pytest from the repo root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
