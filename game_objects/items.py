"""
This module contains classes for items the player can collect and posses. Some items
can give the player special abilities or that can help with mobility or combat.
"""

import pygame as p
from math import sin, pi
from time import perf_counter

from . import TOP, BOTTOM, LEFT, RIGHT, NEGLEGIBE_VELOCITY
from .world import FRICTION_MULTIPLIER, Tile, Chunk
from .entities import Entity, AnimatedEntity
from .environmental import Projectile

from states.gameplay_effects import SlowMotion

from custom_types.base_classes import BasicGameElement
from custom_types.file_representation import EntityData
from custom_types.gameplay import actions_dict, holds_dict, Timer

from settings import keybinds
from math_functions import unit_vector

from settings import keybinds

from debug import log, STATE_INFO




class Item(BasicGameElement):
    "Items objects the player can acquire and store. The player collects these via Collectables."


    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict, player) -> None:
        pass


    def update(self, delta_time: float, player) -> None:
        pass

    @classmethod
    def summon_collectable(cls, tile_pos, id: tuple[int, str]) -> "Collectable":
        "Summons a Collectable entity that will provide the player with the powerup."
        
        return Collectable(tile_pos, cls.__name__, cls, id)
        


    def __repr__(self) -> str:
        return type(self).__name__
    



class HealthOrb(Item):
    "Heals the player by a certain amount when collected."

    heal_amount = (5, 10)

    @classmethod
    def summon_collectable(cls, tile_pos) -> "Collectable":
        return super().summon_collectable(tile_pos, (0, "no_id"))


class PowerUp(Item):
    "An item that gives the player an ability when collected."



class Weapon(Item):
    "An item that can be used by the player to attack enemies."

    attack_cooldown = 0.5
    # Minimum interval between attacks

    def __init__(self) -> None:
        self.attack_cooldown = Timer(type(self).attack_cooldown)
    
    def update(self, delta_time, player) -> None:
        self.attack_cooldown.update(delta_time)




class MeleeWeapon(Weapon):
    "A weapon that does damage to creatures in a certain raduis when attacking."

    attack_damage = 5
    attack_rect_size = (60, 100)
    attack_duration = 0.25


    def __init__(self) -> None:
        super().__init__()
        self.attack_duration = Timer(type(self).attack_duration)



    def userinput(self, action_keys, hold_keys, player) -> None:
        if action_keys[keybinds.attack]:
            self.attack()


    def update(self, delta_time, player) -> None:
        if not self.attack_duration.complete:
            player.attack_tick(self.attack_damage)
        
        self.attack_cooldown.update(delta_time)
        self.attack_duration.update(delta_time)
        super().update(delta_time, player)



    def attack(self) -> None:
        if self.attack_cooldown.complete:
            self.attack_cooldown.start()
            self.attack_duration.start()



class RangedWeapon(Weapon):
    "A weapon that shoots projectiles to damage entities."
    
    LAUNCH_OFFSET = (30, -10)
    projectile: str = "test_bullet"



    def __init__(self) -> None:
        super().__init__()
    
    def userinput(self, action_keys, hold_keys, player) -> None:
        self.vertical = 0
        if action_keys[keybinds.attack]:
            if hold_keys[p.K_PAGEDOWN]:
                self.vertical = -1
            elif hold_keys[p.K_END]:
                self.vertical = 1

            start_pos = player.position + (self.LAUNCH_OFFSET[0]*player.facing, self.LAUNCH_OFFSET[1]*(1-self.vertical))
            
            Projectile(start_pos, self.projectile, p.Vector2(player.facing, self.vertical), player)






class PowerTank(Item):
    "Allows the player to perform new actions."



    



class WallJump(PowerUp):
    "Allowes the player to jump off walls and slide down them."

    slide_speed = 300
    horizontal_speed = 700

    def __init__(self) -> None:
        self.input_timer = Timer(0.2)
        self.direction = 0
        self.wall_slide = False


    def userinput(self, action_keys: actions_dict, hold_keys: actions_dict, player) -> None:

        if (
            not (player.tile_contacts[TOP] or player.tile_contacts[BOTTOM])
        ):
            wall_side = None
            if action_keys[keybinds.right]:
                wall_side = LEFT
            
            if action_keys[keybinds.left]:
                wall_side = RIGHT

            
            if wall_side is not None:
                for tile in player.tile_contacts[wall_side]:
                    if tile.wall_jump: # If the player can wall jump off the tile
                        self.direction = 1 if wall_side == LEFT else -1
                        self.input_timer.start()


        if hold_keys[keybinds.jump] and not self.input_timer.complete:
            player.velocity.x = 0.0
            player.accelerate(
                (self.horizontal_speed*self.direction, player.jump_speed)
            )

            self.input_timer.countdown = 0.0
            player.jump_timer.start()

            log(STATE_INFO, "Wall Jump!")
        
        if self.input_timer.complete:
            self.direction = 0

        

        if self.__can_slide_on_side(player.tile_contacts[LEFT]) and hold_keys[keybinds.left] or self.__can_slide_on_side(player.tile_contacts[RIGHT]) and hold_keys[keybinds.right]:
            self.wall_slide = True
        else:
            self.wall_slide = False

    
    def __can_slide_on_side(self, side_tiles: set[Tile]) -> bool:
        for tile in side_tiles:
            if tile.wall_jump:
                return True
        
        return False

    
    def update(self, delta_time: float, player) -> None:
        self.input_timer.update(delta_time)

        # Allows the player to slide down walls slowly when they move towards a wall they are
        # in contact with
        if self.wall_slide:
            if player.velocity.y > self.slide_speed + NEGLEGIBE_VELOCITY:
                friction = (player.get_tile_friction(LEFT) + player.get_tile_friction(RIGHT))/2
                
                player.velocity.y -= min(friction*FRICTION_MULTIPLIER*delta_time, player.velocity.y - self.slide_speed)
            else:
                player.velocity.y = min(player.velocity.y, self.slide_speed)





class DoubleJump(PowerUp):
    "Allows the player to jump in mid air once."

    horizontal_speed = 400

    def __init__(self) -> None:
        self.can_jump = True


    def userinput(self, action_keys: actions_dict, hold_keys: actions_dict, player) -> None:
        conditions = [
            action_keys[keybinds.jump],
            self.can_jump,
            player.jump_timer.complete,
            player.jump_delay.complete,
            not (player.tile_contacts[TOP] or player.tile_contacts[BOTTOM]),

            (not player.has_item(WallJump)) or (player.powerups.get(WallJump).input_timer.complete)

            # not (player.tile_contacts[LEFT] or player.tile_contacts[RIGHT])
            # or (not player.has_item(WallJump)) or (player.powerups.get(WallJump).input_timer.complete)
        ]


        if all(conditions):
            player.velocity.y = -player.jump_speed
            if hold_keys[keybinds.left]:
                player.velocity.x = min(player.velocity.x, -self.horizontal_speed)

            if hold_keys[keybinds.right]:
                player.velocity.x = max(player.velocity.x, self.horizontal_speed)
            
            player.jump_timer.start()

            self.can_jump = False

            log(STATE_INFO, "Double Jump!")

    

    def update(self, delta_time: float, player) -> None:
        if player.tile_contacts[BOTTOM]:
            self.can_jump = True




class GroundPound(PowerUp):
    "Allows the player to dash towards the ground and break tiles beneath them if they are breakable."

    pound_speed = 2000

    def __init__(self) -> None:
        self.can_pound = True
        self.pounding = False

    

    def userinput(self, action_keys: actions_dict, hold_keys: actions_dict, player) -> None:
        if (
            action_keys[keybinds.crouch]
            and not player.tile_contacts[BOTTOM]
            and self.can_pound
        ):
            player.velocity.x = 0 # Stops the player from moving horizontally
            player.velocity.y = self.pound_speed
            player.jump_timer.countdown = 0.0 # Stops the the player from moving up due to holding down jump
            
            self.pounding = True
            self.can_pound = False

            log(STATE_INFO, "Ground Pound!")

    

    def update(self, delta_time: float, player) -> None:
        if player.tile_contacts[BOTTOM]:
            self.can_pound = True
            if self.pounding:
                self.pounding = False
                if self.__break_tiles(player.tile_contacts[BOTTOM]):
                    SlowMotion(0.4, 0.05).add_to_stack()
                player.velocity.y = self.pound_speed*0.5

    
    def __break_tiles(self, tiles: set[Tile]) -> bool:
        "Breaks the tiles beneath the player if they are breakable."

        for tile in tiles:
            if not tile.breakable:
                return False
        
        tile.break_tile(break_surroundings=True)
        return True



class GravitonCleaver(MeleeWeapon):
    """
    Another melee weapon that can create a shockwave when used in combination
    with GroundPound.
    """

    SHOCKWAVE_AREA = (24, 20)
    SHOCKWAVE_REQUIRED_SPEED = 2000

    attack_rect_size = (100, 100)
    attack_cooldown = 0.8
    shockwave_delay_amount = 0.2
    attack_duration = 0.2
    attack_damage = 20
    shockwave_damage = 15


    def __init__(self) -> None:
        super().__init__()

        self.do_shockwave = False
        self.shockwave_delay = Timer(self.shockwave_delay_amount)


    def userinput(self, action_keys, hold_keys, player) -> None:
        if action_keys[keybinds.attack]:
            if self.shockwave_delay.complete:
                self.attack()

            else:
                self.__shockwave(player)
                self.shockwave_delay.stop()


    def update(self, delta_time, player) -> None:
        super().update(delta_time, player)
        self.shockwave_delay.update(delta_time)

        if player.velocity.y >= self.SHOCKWAVE_REQUIRED_SPEED:
            self.do_shockwave = True

        if self.do_shockwave and player.tile_contacts[BOTTOM]:
            self.shockwave_delay.start()
            self.do_shockwave = False

    
    def __get_shockwave_rect(self, focus: p.Vector2) -> p.Rect:
        rect = p.Rect(0, 0, *p.Vector2(self.SHOCKWAVE_AREA)*Tile.SIZE)
        rect.center = focus

        return rect
    

    def __shockwave(self, player) -> None:
        focus = player.rect.centerx, player.rect.bottom
        rect = self.__get_shockwave_rect(focus)
        chunks: list[Chunk] = player.collision_chunks.values()

        for chunk in chunks:
            if rect.colliderect(chunk.rect):
                for tile in chunk.midground_tiles.copy():
                    if rect.colliderect(tile.rect):
                        tile.break_tile()
        

        for entity in player.group:
            if player.can_attack(entity):
                entity.accelerate((0, 2000))
                entity.damage(self.shockwave_damage, "shockwave", unit_vector(entity.position-player.position))
        
        player.camerashake(0.5, 10, p.Vector2(0, 1))





class Eclipser(MeleeWeapon):
    "The final melee weapon the player will find. It deals the most damage and is to defeat the final boss."
    # There wan't enough time to implement this

class IonBlaster(RangedWeapon):
    "The first ranged weapon the player finds. This allows the player to shoot small projectiles at enemies."

    projectile = "ion_pellet"

class PlasmaCannon(RangedWeapon):
    "The second ranged weapon the player finds. This player needs to charge the attack before shooting."
    # There wan't enough time to implement this properly



        




class ClassUniqueList(list):
    "A list where an object of element type can only appear once. Unlike a set the order of elements is retained."

    def __init__(self, elements: list = []) -> None:
        for element in elements:
            self.append(element)

    
    def append(self, obj) -> None:
        for element in self:
            if type(element) is type(obj):
                return None
        
        super().append(obj)


    def remove_by_class(self, item_class) -> None:
        "Removes the element that is of the type specified."
        for element in self:
            if type(element) is item_class:
                super().remove(element)
                break
        
        raise ValueError(f"{type(self).__name__}.remove({item_class.__name__}): there is not element in list of type[{item_class.__name__}].")


    
    def get(self, item_class: type[object]) -> object | None:
        "Gets the elment that is of the type specified."
        for element in self:
            if type(element) is item_class:
                return element
        

        return None



class WeaponGroup(ClassUniqueList):
    "A ClassUniqueList of Weapon objects that the player can cycle through."
    current_weapon: Weapon | MeleeWeapon | None
    
    def __init__(self, weapons: list[Weapon] | None = None) -> None:
        if weapons is None:
            weapons = []
        
        if weapons:
            self.current_weapon = weapons[0]
        else:
            self.current_weapon = None

        super().__init__(weapons)


    def choose(self, index: int) -> None:
        "Make the weapon at the index the current weapon."
        self.current_weapon = self[index]


    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict, player) -> None:
        "Processes userinput for the current weapon."
        self.current_weapon.userinput(action_keys, hold_keys, player)
    

    def update(self, delta_time: float, player) -> None:
        "Updates the current weapon."
        self.current_weapon.update(delta_time, player)


    def append(self, obj) -> None:
        if not isinstance(obj, Weapon):
            raise ValueError("Weapon to add is not of type Weapon")
        
        super().append(obj)

        if self.current_weapon is None:
            self.current_weapon = obj
            # Sets the current weapon as the one appended






class PowerUpGroup(ClassUniqueList):
    "Collection of powerups the player has acquired."

    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict, player) -> None:
        "Processes userinput for all powerups."
        for powerup in self:
            powerup.userinput(action_keys, hold_keys, player)

    
    def update(self, delta_time: float, player) -> None:
        "Updates all powerups in the group."
        for powerup in self:
            powerup.update(delta_time, player)











class Collectable(AnimatedEntity):
    "Collectables are entities that give the player an Item when coming into contact."
    
    SUMMON_OFFSET = (0, -10)
    hitbox = (48, 48)
    bob_offset = 5
    BOB_PERIOD = 4
    collect_anim_delay_amount = 1.0

    draw_level = 1
    # Collectables will be drawn over regular entities.




    def __init__(self, tile_pos: tuple[int, int], texture_name: str, collect_item: type[Item], id: tuple[str, int]) -> None:
        self.collect_item = collect_item

        x, y = (p.Vector2(tile_pos)*Tile.SIZE+p.Vector2(self.hitbox)*0.5) + self.SUMMON_OFFSET

        self.id = id
        self.collected = False

        self.collect_anim_delay = Timer(self.collect_anim_delay_amount, False, self.instant_kill)

        self.texture_map = self.texture_map.copy()
        self.texture_name = texture_name
        self.texture_map["frame1"] = self.texture_map[self.texture_name]
        # Sets the texture of the current item to 'frame1' in the texture map.
        # This frame will be used by the Animation objects

        
        super().__init__(x, y, self.hitbox, self.texture_map, self.animation_data, self.anim_controller_data)

    
    def update(self, delta_time: float) -> None:
        if not self.collected:
            from .player import Player
            for entity in p.sprite.spritecollide(self, self.group, False):
                if isinstance(entity, Player):
                    self.__acquired(entity)
                    # Makes the Player object acquire the item it collides with
                    # the Collectable's hitbox.
                    break
        
        else:
            self.collect_anim_delay.update(delta_time)
            super().update(delta_time)





    def kill(self) -> None:
        self.collected = True
        self.collect_anim_delay.start()

    
    def __acquired(self, player) -> None:
        "Makes the player acquire the item of the collectbale."

        if issubclass(self.collect_item, HealthOrb):
            self.instant_kill()
            # The HealthOrb shouldn't play a collect animation or open a
            # menu describing what the item is as it should be quite self
            # explanitory

        else:
            from states.gameplay_menus import ItemMenu
            ItemMenu(self).add_to_stack()
            
            self.kill()


        player.acquire_item(self.collect_item, self.id)


    def get_entity_data(self) -> EntityData:
        return EntityData(
            type(self).__name__,
            [self.get_occupying_tile(), self.texture_name, self.collect_item, self.id],
            {}
        )

    

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.collect_item.__name__})"
    

    def draw(self, surface, offset=(0, 0), alpha=255) -> None:
        time = perf_counter()%self.BOB_PERIOD
        bob_offset = self.bob_offset*sin(2*pi*time/self.BOB_PERIOD)
        super().draw(surface, (offset[0], offset[1]+bob_offset), alpha)
        # Makes the sprite move up and down in a sinusoidal pattern