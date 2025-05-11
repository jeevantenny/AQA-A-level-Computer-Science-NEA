"""
Contains settings related to keybinds. Kibinds control what key
performs what action during gameplay.
"""

from pygame.locals import *
from typing import Any


left: int | str = K_a
right: int | str = K_d
jump: int | str = K_SPACE
crouch: int | str = K_s
attack: int | str = K_RSHIFT
interact: int | str = K_e

swap_weapon: int | str = K_RETURN
select_weapon: int | str = K_HASH
toggle_map: int | str = K_TAB


def all_settings() -> dict[str, Any]:
    "Returns a dictionary conntaining all of the module's settings."

    from . import _get_all_settings
    return _get_all_settings(globals())


def set(keybind_data: dict) -> None:
    "Sets all the settings for the module."

    from . import _set_settings
    _set_settings(keybind_data, globals())


def set_keybind(action_name: str, key: int | str) -> None:
    "Sets the value for a keybind by refrencing the variable name."
    
    globals()[action_name] = key