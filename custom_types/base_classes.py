"Contains the BasicGameElement class."

import pygame as p
from typing import Self
from debug import log, GAME_INFO

from .gameplay import Coordinate, actions_dict, holds_dict


class BasicGameElement:
    """
    This class provides functionality for classes that require initialization or
    assets to be loaded before any objects are created.

    The class contains various blank methods. These are methods that are commonly
    used by many classes in the game.
    """
    assets_loaded = False

    assets: dict[str, p.Surface]
    
    @classmethod
    def init_class(cls) -> None:
        "Sets up base class attributes."

        # initialization code

        log(GAME_INFO, f"Initialized {cls.__name__}")

    
    @classmethod
    def load_assets(cls, asset_data: dict[str, dict]) -> None:
        "Loads assets required by the class and all it's subclasses."

        cls.__assets__(asset_data)

        for subcls in cls.__subclasses__():
            if not subcls.assets_loaded:
                subcls.load_assets(asset_data)
        
        cls.assets_loaded = True


    @classmethod
    def __assets__(cls, asset_data: dict[str, dict]) -> None:
        "Method used for loading any assets when the 'load_assets' method is called."

        cls.assets = {}

        for name, value in asset_data.get(cls.__name__, {}).items():
            setattr(cls, name, value)
            cls.assets[name] = value


    @classmethod
    def find_class_by_name(cls, class_name: str) -> type[Self] | None:
        "Returns the current class or subclass that matches the name provided. Returns None if a match can't be found"

        if cls.__name__ == class_name:
            return cls
        else:
            for subcls in cls.__subclasses__():
                value = subcls.find_class_by_name(class_name)
                if value is not None:
                    return value
        
        return None

    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict) -> None:
        "Performs relevant actions based on user input."

    def update(self, delta_time: float) -> None:
        "Processes information for one frame."
    
    def draw(self, surface: p.Surface) -> None:
        "Draws onto the surface provided."