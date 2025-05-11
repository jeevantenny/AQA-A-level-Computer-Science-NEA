"""
This package contains objects which are sprites that
are drawn to the screen during gameplay. 
"""

import pygame as p


GAME_OBJECT_SCALE = 3


AIR = "0"

TOP = "top"
BOTTOM = "bottom"
LEFT = "left"
RIGHT = "right"


NEGLEGIBE_VELOCITY = 10
DEFUALT_GRAVITY = 2000
# There was initially a plan to add variable gravity between regions but this feature was not implemented
# due to time constraints.


def init(entity_group, collision_chunks, gravity_multiplier=1) -> None:
    from file_processing.assets import load_class_assets
    from .entities import Entity

    entity_assets = load_class_assets("entity_assets.json")

    Entity.init_class(entity_group, collision_chunks, gravity_multiplier, entity_assets)
    # Assigns assets and other variables to class attributes







def scale_game_object(texture: p.Surface, scale_value = GAME_OBJECT_SCALE) -> p.Surface:
    "Scales a texture by GAME_OBJECT_SCALE by default."
    
    return p.transform.scale_by(texture, scale_value)