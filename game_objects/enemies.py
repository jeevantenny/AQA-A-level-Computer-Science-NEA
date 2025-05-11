"This module contains classes for all enemies in the game."

import pygame as p
from random import randint

from . import TOP, BOTTOM, LEFT, RIGHT, items
from .world import Tile
from .creature_types import Creature, Walker, Flier
from .player import Player

from .environmental import Projectile

from custom_types.gameplay import Timer, Coordinate
from math_functions import sign, unit_vector, random_error




class Enemy:
    """
    The Enemey class provides functionality for enemies to track targets within the game. It isn't a subclass of Creature so when creating
    a new Enemy class it needs to inherit from Enemy and either Walker or Flyer.
    """

    stalk_area = (64, 32)
    attack_delay = 0.3
    position: p.Vector2

    def __init__(self, x, y, facing = RIGHT, *, velocity = p.Vector2(0, 0)) -> None:
        self.attack_delay = Timer(type(self).attack_delay, False, self.attack)
        self.target = None

        super().__init__(x, y, facing, velocity=velocity)
    
    

    @property
    def stalk_rect(self) -> p.Rect:
        "The area in which a target has to be in order for the enemy to try and track it down."
        rect = p.Rect(0, 0, *p.Vector2(self.stalk_area)*Tile.SIZE)
        rect.center = self.position
        return rect
    


    @property
    def ready_to_attack(self) -> bool:
        "Returns True if the enemy is ready to attack the player when they come into attacking range"

        return self.attack_cooldown.complete and self.attack_duration.complete and self.attack_delay.complete
    


    def update(self, delta_time: float) -> None:
        if self.target is None:
            self.target = self._find_target()
        elif not self._is_target_valid(self.target):
            self.target = None

        super().update(delta_time)


    def _find_target(self) -> Creature | None:
        "Trys to find a valid target"

        for entity in self.group:
            if self._is_target_valid(entity):
                return entity
            
    def _is_target_valid(self, target: Creature) -> bool:
        "Weather the enemy should try and track down the target."

        return self.can_attack(target) and target.alive and target.rect.colliderect(self.stalk_rect)
    

    def _target_displacement(self) -> p.Vector2:
        """
        Returns the displacement of between the Enemy and it's target. This method should not be called
        if the enemy does not have a target.
        """

        return self.target.position-self.position
    


    def can_attack(self, entity: Creature) -> bool:
        return super().can_attack(entity) and isinstance(entity, Player)


    def kill(self) -> None:
        items.HealthOrb.summon_collectable(self.get_occupying_tile())
        # Summons a health orb as a reward for killing the enemy
        super().kill()
    






class Slime(Enemy, Walker):
    "A type of enemy that jumps towards the player. It deals damage by bouncing on the player."

    hitbox = (70, 70)

    walk_speed = 500
    jump_interval_values = (1.5, 0.4)
    # Two possible values for jump interval
    # One for when there is no target
    # One for when there is a target

    jump_duration = 0.3
    jump_speed = 800

    jump_interval_difference = 0.3
    # The Random difference in jump intervals

    immune_damage_types = {"spike": True}
    
    attack_damage = 3
    attack_rect_size = (50, 50)
    knockback_strength = 500

    gravity_ratio = 1/2


    def __init__(self, x, y, *, velocity=p.Vector2(0, 0)) -> None:
        super().__init__(x, y, velocity=velocity)

        self.jump_interval = Timer(self.jump_interval_values[0], execute_after=self.jump).start()


    @property
    def attack_rect(self) -> p.Rect:
        rect = p.Rect(0, 0, *self.attack_rect_size)
        rect.center = self.position
        return rect


    def update(self, delta_time) -> None:
        super().update(delta_time)

        if not self.alive:
            return None
        
        if self.tile_contacts[BOTTOM] and self.jump_interval.complete and self.attack_cooldown.complete:
            self.jump_interval.duration = random_error(self.jump_interval_values[bool(self.target is not None)], self.jump_interval_difference)
            self.jump_interval.start()

        if self.target is not None and self.attack_cooldown.complete:
            self.navigate_to(self.target.position)
            
            if self.target.rect.colliderect(self.attack_rect):
                self.attack_tick(self.attack_damage)
                self.velocity = unit_vector(p.Vector2(sign(self._target_displacement().x), 2))*-800
                self.attack_cooldown.start()
                # Deals damage whenever the player collides with the slime

        
        self.attack_delay.update(delta_time)
        self.jump_interval.update(delta_time)



    def navigate_to(self, position: Coordinate) -> None:
        if not self.tile_contacts[BOTTOM]:
            displacement = p.Vector2(position) - self.position
            if displacement.y < 0:
                self.jump()
            self.walk(displacement.x)


    def process_tile_friction(self, delta_time) -> None:
        if self.tile_contacts[BOTTOM]:
            self.velocity *= 0

        else:
            super().process_tile_friction(delta_time)





class Stalacsprite(Enemy, Flier):
    "A Flying bug like enemy that shoots projectiles at the player."

    hitbox = (100, 100) # Larger hitbox to make it easier for the player to hit
    health = 8
    fly_speed = 500

    stalk_area = (20, 48)

    attack_damage = 3
    attack_rect_size = (52, 52)
    attack_interval = 3.2

    shoot_range = 200

    knockback_strength = 200

    immune_damage_types = {"spike": False}

    def __init__(self, x, y, facing=RIGHT, *, velocity=p.Vector2(0, 0)) -> None:
        super().__init__(x, y, facing, velocity=velocity)

        self.stroll_direction = p.Vector2(1, 0)
        # The direction to move in when not persuiing enemy

        self.direction_change_timer = Timer(0.5, True, self.__change_stroll_direction).start()
        # controls the change stroll direction

        self.attack_interval = Timer(type(self).attack_interval)
        # Time interval between attacks


    def __change_stroll_direction(self) -> None:
        "Changes the direction the creature is moving in by rotating the direction vector by a random amount."

        self.stroll_direction.rotate_ip(randint(-100, 100))
    
    def update(self, delta_time) -> None:
        super().update(delta_time)
        if not self.alive:
            self.gravity = 1
            return None

        
        if self.tile_contacts["any"]:
            self.__change_stroll_direction()
            self.direction_change_timer.start()
        # Change direction when colliding with a tile


        if self.target is not None and self._is_target_valid(self.target):
            if self.attack_interval.complete: # Will only navigatw to player when the attack interval is complete
                self.navigate_to(self.target.position)
                if self._target_displacement().magnitude() < self.shoot_range:
                    self.shoot(unit_vector(self.target.position-self.position))
                    # Only shoots when the target is within the shoot_range
         
        
        self.navigate_to(self.position+self.stroll_direction)
        # Provides random movement to the Stalacsprite
        
        self.direction_change_timer.update(delta_time)
        self.attack_interval.update(delta_time)


    def shoot(self, direction: p.Vector2) -> None:
        if self.ready_to_attack:
            Projectile(
                self.position,
                "sprite_quill",
                direction,
                self
            )

            self.attack_cooldown.start()
            self.attack_interval.start()
            # The attack_delay timer is not started because shooting a projectile doesn't take any amount of time