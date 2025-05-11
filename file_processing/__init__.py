"""
This package contains a modules used to load files from the assets and data folders.
"""

import json


def load_json(path: str) -> dict:
    "Loads a json file using the path and returns it as a dictionary."

    with open(path, "r") as f:
        return json.load(f)