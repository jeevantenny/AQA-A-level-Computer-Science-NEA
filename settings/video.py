"Contains settings related to video."

from typing import Any

fps: int = 60
camerashake: bool = True
draw_particles: bool = True


def all_settings() -> dict[str, Any]:
    "Returns a dictionary conntaining all of the module's settings."

    from . import _get_all_settings
    return _get_all_settings(globals())



def set(video_data: dict) -> None:
    "Sets all the settings for the module."
    
    from . import _set_settings
    _set_settings(video_data, globals())