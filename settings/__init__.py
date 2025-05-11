"""
This package contains variables for game settings such as key binds and volume levels.
load() must be called before using any functionality.

For each module in the package I have assigned variables to hold each setting. This
makes it a bit easier to find a perticular setting rather than looking through a
dictionary.
"""

import json
from typing import Any

from . import keybinds

from debug import log, GAME_INFO


USER_SETTINGS_DIR = "user_data/user_settings.json"


def load() -> None:
    "Loads the setting data stores in the user settings json file."

    from . import audio, video

    with open(USER_SETTINGS_DIR, "r") as f:
        settings_data: dict = json.load(f)

    keybinds.set(settings_data.get("key_binds", {}))
    audio.set(settings_data.get("audio", {}))
    video.set(settings_data.get("video", {}))
    # If the settings file is empty or a catagory is missing an empty
    # dictionary is passed which will keep the default settings
    # of that catagory

    log(GAME_INFO, "Loaded user settings")





def save() -> None:
    "Updates the user settings json file with the current settings."

    from . import audio, video

    settings_data = {
        "key_binds": keybinds.all_settings(),
        "audio": audio.all_settings(),
        "video": video.all_settings()
    }

    with open(USER_SETTINGS_DIR, "w") as f:
        settings_data = json.dump(settings_data, f)

    log(GAME_INFO, "Saved user settings")



def _get_all_settings(g: dict) -> dict[str, Any]:
    """
    Returns a dictionary holding the name and value of all the settings
    in a module.
    """

    return {
        name: value

        for name, value, in g.items()
        if name in g["__annotations__"]
        # The variables that are used for the settings will have type anotations.
        and name != "all_settings"
        # This is to avoid including the all_settings function that will be there
        # in each module.
    }


def _set_settings(setting_data: dict, g: dict) -> None:
    """
    Assigns the value of all settings in settings_data to the corresponding
    variable in a module.
    """

    for name, value in setting_data.items():
        g[name] = value
        # Assigns the value to the variable that goes by the name.