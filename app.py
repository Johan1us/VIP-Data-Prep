import os
import sys

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.app import main

if __name__ == "__main__":
    main()
