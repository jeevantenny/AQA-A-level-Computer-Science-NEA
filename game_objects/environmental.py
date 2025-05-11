"""
A catagory of mini entities that add vidual elements ti gameplay or
complement the functionality of other entities.
"""

import pygame as p
from typing import Self, Callable

from . import scale_game_object
from .entities import Entity, CollisionEntity, AnimatedEntity
from .creature_types import Creature

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import Timer, Coordinate
from custom_types.animation import Animation
from custom_types.file_representation import EntityData

from file_processing import load_json
from settings import video
from math_functions import unit_vector




class Environmental(BasicGameElement):
    "Contains attributes and functionality that all Environmental entities will need."

    texture_map: dict[str, p.Surface]

    # Environmental entities can have presets which are stores in json files.
    presets: dict[str, dict]
    preset_file_path: str
    # The relative path of the preset json file for the type of entity
    # The files are stored at data/object_presets/

    kill_when_out_of_range = True

    @classmethod
    def __assets__(cls, asset_data) -> None:
        cls.presets = load_json(f"data/object_presets/{cls.preset_file_path}")
        cls.assets["presets"] = cls.presets
        super().__assets__(asset_data)






class Projectile(CollisionEntity, Environmental):
    """
    An entity that can be used by entities to shoot targets. They deal damage to
    the target upon collision.
    """

    kill_when_out_of_range = True
    preset_file_path = "projectiles.json"
    can_attack: Callable[[Creature], bool]

    def __init__(
            self,
            start_pos: Coordinate,
            preset_name: str,
            direction: p.Vector2,
            shooter: Creature | None = None
        ) -> None:

        self.preset_name = preset_name
        current_preset = self.presets[preset_name]
        velocity = unit_vector(direction)*current_preset["speed"] + (shooter.velocity.x, 0)

        super().__init__(*start_pos, current_preset["hitbox"], self.texture_map[current_preset["texture"]], velocity=velocity)

        if not current_preset.get("gravity", False):
            self.gravity = 0

        self.lifetime_timer = Timer(current_preset["lifetime"], False, self.kill)
        # The time before the projectile is removed

        # If the duration is 0.0 it means the projectile doesn't have a time limit for how long
        # it can exist
        if self.lifetime_timer.duration >= 0:
            self.lifetime_timer.start()
        

        self.damage = current_preset["damage"]
        # The amount of damage the projectile deals
        if shooter is not None:
            self.can_attack = shooter.can_attack
        else:
            self.can_attack = lambda x: isinstance(x, Creature)

        self.kill_on_contact = current_preset.get("kill_on_tile_contact", True)
        # Weather the entity should be removed upon contact with a tile

        self.summon_entity = Entity.find_class_by_name(current_preset.get("summon_entity", None))
        # Any entity the projectile should summon when it collides with a target.

        if not current_preset.get("rotate_sprite", True):
            self.draw = super().draw



    def update(self, delta_time) -> None:
        super().update(delta_time)

        self.lifetime_timer.update(delta_time)


        for entity in p.sprite.spritecollide(self, self.group, False):
            if self.can_attack(entity):
                entity.damage(self.damage, "ranged", p.Vector2(self.velocity.x, self.velocity.y-10))
                self.kill()
                break
        
        if self.kill_on_contact and self.tile_contacts["any"]:
            self.kill()
        
    
    def kill(self) -> None:
        if self.summon_entity is not None:
            self.summon_entity(*self.position)
        super().kill()


    
    def draw(self, surface, offset=(0, 0), alpha=255) -> None:
        blit_texture = p.transform.rotate(self.texture, self.velocity.angle_to((1, 0)))
        blit_texture = scale_game_object(blit_texture)
        # Rotates the texture based on the direction of the projectile before being scaled.
        # This maintains the pixel art asthetic as no pixels appear to be rotated.

        blit_texture.set_alpha(alpha)

        blit_pos = self.rect.center - p.Vector2(blit_texture.get_size())*0.5

        surface.blit(blit_texture, blit_pos+offset)


    def __str__(self) -> str:
        return f"{type(self).__name__}('{self.preset_name}')"





# This class is unused
# There were initially going to be particle effects in the game but
# this couldn't be done due to time constraints
class Particle(AnimatedEntity, Environmental):
    preset_file_path = "particles.json"

    def __new__(cls) -> None | Self:
        if not video.draw_particles:
            return None
        return super().__new__(cls)

    def __init__(self, start_pos: tuple[int, int], preset_name: str) -> None:
        current_preset = self.presets[preset_name]
        self.preset_name = preset_name
        x, y = start_pos - p.Vector2(current_preset["hitbox"])*0.5

        super().__init__(x, y, (3, 3))