import os
import sys

# Ensure this script can be run from anywhere (double-click in Explorer)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ussurochki.main import main  # noqa: E402

if __name__ == "__main__":
    main()