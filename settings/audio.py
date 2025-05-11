"Contains settings related to audio."

from typing import Any

music_volume: float = 0.7
gameplay_volume: float = 0.7


def all_settings() -> dict[str, Any]:
    "Returns a dictionary conntaining all of the module's settings."

    from . import _get_all_settings
    return _get_all_settings(globals())



def set(sound_data: dict[str, float]) -> None:
    "Sets all the settings for the module."
    
    from . import _set_settings
    _set_settings(sound_data, globals())