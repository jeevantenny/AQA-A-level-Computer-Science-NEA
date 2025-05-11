"Contains the player class."

import pygame as p
from typing import Literal
from random import randint

from . import TOP, BOTTOM, LEFT, RIGHT, items
from .entities import Entity
from .world import Tile, Ramp, Chunk, loaded_chunk_dict
from .creature_types import Walker
from .props import Interactable

from audio import SoundFX

from file_processing.assets import load_texture, load_texture_map
from custom_types.gameplay import actions_dict, holds_dict, Timer
from custom_types.file_representation import EntityData
from settings import keybinds

from debug import log, DEBUGGING, STATE_INFO




class Player(Walker):
    """
    This represents the player character which the the player controls. This is the class through which
    the player explores the world.

    It is the only entity with a userinput method which allows it to process the userinputs directly.
    """
    hitbox = (46, 130)
    health = 100
    walk_speed = 650
    sprint_speed = 900
    walk_acceleration = 4000
    jump_speed = 700
    jump_duration = 0.2
    jump_delay = 0.1

    air_friction = 0.6

    attack_cooldown = 0.2
    attack_rect_size = (90, 180)

    die_time = 1.5
    # I increased the die time so the player will still be visible as
    # when the GameOverScreen is called

    ATTRIBUTES_TO_SAVE = [
        "velocity",
        "health",
        "jump_timer",
        "facing",
        "powerups",
        "weapons",
        "weapon_mode",
        "collected_powertanks"
    ]






    def __init__(self, x: int, y: int, facing: Literal["left", "right"] = RIGHT, *, velocity = p.Vector2(0, 0)) -> None:

        super().__init__(
            x,
            y,
            facing,
            velocity=velocity
        )

        self.powerups = items.PowerUpGroup()
        self.weapons = [
            items.WeaponGroup([items.MeleeWeapon()]),
            items.WeaponGroup()
        ]

        self.collected_powertanks: set[tuple[str, int]] = set()

        self.jump_delay = Timer(type(self).jump_delay)
        self.weapon_mode: Literal[0, 1] = 0
        self.sprinting = False

   
    @property
    def attack_rect(self) -> p.Rect:
        area = self.weapons[0].current_weapon.attack_rect_size
        pos = self.position - (0, area[1]/2)
        if self.facing == -1:
            pos.x -= area[0]
        
        return p.Rect(*pos, *area)



    @property
    def current_weapon(self) -> items.Weapon | items.MeleeWeapon | None:
        return self.weapons[self.weapon_mode].current_weapon




    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict) -> None:
        self.powerups.userinput(action_keys, hold_keys, self)

        if hold_keys[keybinds.left]:
            self.walk(-1)
        if hold_keys[keybinds.right]:
            self.walk(1)

        self.sprinting = hold_keys[p.K_j]
        
        if action_keys[keybinds.jump] or (hold_keys[keybinds.jump] and not self.jump_timer.complete):
            self.jump()
        else:
            if not self.jump_timer.complete:
                self.velocity.y *= 0.5
            self.jump_timer.countdown = 0.0


        if action_keys[keybinds.swap_weapon]:
            self.cycle_weapon()

        self.weapons[self.weapon_mode].userinput(action_keys, hold_keys, self)



        if action_keys[keybinds.interact]:
            self.interact()




    def update(self, delta_time: float) -> None:
        self.powerups.update(delta_time, self)
        self.weapons[self.weapon_mode].update(delta_time, self)

        if self.tile_contacts[BOTTOM]:
            self.jump_delay.start()
        else:
            self.jump_delay.update(delta_time)
        
        super().update(delta_time)



    def process_collision(self) -> None:
        if self.tile_contacts[BOTTOM] and self.velocity.y > 2000:
            self.camerashake(0.4, max(self.velocity.y - 1200, 0)/300)
            
        super().process_collision()


    def max_movement_speed(self) -> int | float:
        # The movement speed will be higher if the player is sprinting
        if self.sprinting and self.tile_contacts[BOTTOM]:
            return self.sprint_speed
        
        else:
            return super().max_movement_speed()



    def damage(self, amount, type="melee", knockback = p.Vector2(0, 0)) -> None:
        if self.damage_cooldown.complete:
            self.camerashake(0.3, 2, knockback)
            super().damage(amount, type, knockback)


    def jump(self) -> None:
        if self.tile_contacts[TOP]:
            self.jump_timer.countdown = 0.0
        else:
            if self.tile_contacts[BOTTOM] or not self.jump_delay.complete:
                self.jump_timer.start()
                self.jump_delay.countdown = 0.0
            if self.jump_timer.countdown:
                self.velocity.y = -self.jump_speed*(self.gravity*0.6 + 0.4)


    
    def acquire_item(self, item_class: type[items.Item], id: tuple[str, int]) -> None:
        """
        Acquired the item type by creating an instance of the class (if needed) and adding it to the
        correct list of items.
        """
        if issubclass(item_class, items.Item):

            if issubclass(item_class, items.HealthOrb):
                self.heal(randint(*items.HealthOrb.heal_amount))
            
            elif issubclass(item_class, items.PowerTank):
                self.collected_powertanks.add(id)
            else:
                item_list = self.__get_item_list(item_class)
                item_list.append(item_class())

                if isinstance(item_list, items.WeaponGroup):
                    item_list.choose(-1)
                log(STATE_INFO, f"{self} has acquired {item_class.__name__}")

        else:
            raise ValueError(f"Invalid item class '{item_class.__name__}.")



    def has_item(self, item_class: type[items.PowerUp]) -> bool:
        "Return True if the player currently has an item that is an instance of the 'item_class'."

        if issubclass(item_class, items.PowerTank):
            return bool(self.collected_powertanks)
        else:
            return self.__get_item_list(item_class).get(item_class) is not None



    def __get_item_list(self, item_class: type[items.Item]) -> items.PowerUpGroup | items.WeaponGroup:
        "Gets the list the provided items should be added to."

        if issubclass(item_class, items.PowerUp):
            return self.powerups
        elif issubclass(item_class, items.MeleeWeapon):
            return self.weapons[0]
        elif issubclass(item_class, items.RangedWeapon):
            return self.weapons[1]
        
        else:
            raise ValueError("Invalid item class.")



    
    def interact(self) -> None:
        "Makes the player interact with a nearby interactable entity."
        
        # I have used the attack rect to check for interactable entities
        # as it is of a good size and position.
        for entity in self.get_colliding_entities(self.attack_rect):
            if isinstance(entity, Interactable):
                entity.player_interact()
                break
    


    def cycle_weapon(self) -> None:
        """
        Cycles the weapon mode between melee and ranged.
        """

        self.weapon_mode = (self.weapon_mode+1)%len(self.weapons)

        if not self.weapons[self.weapon_mode]:
            if self.weapon_mode == 0:
                raise ValueError("Player does not have initial weapon.")
            
            self.cycle_weapon()
            # If the player has not acquired any ranged weapons it switches back to melee.