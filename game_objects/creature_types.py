"""
This module contains base classes for entities that can move around on their won and navigate the world

The player class and all enemy classes inherit from ones within this module.
"""

import pygame as p
from typing import Self, Literal, TypeGuard
from random import randint

from . import TOP, BOTTOM, LEFT, RIGHT, DEFUALT_GRAVITY
from .world import Tile, Ramp
from .entities import Entity, CollisionEntity, AnimatedEntity

from custom_types.gameplay import Timer, Coordinate
from custom_types.file_representation import EntityData
from math_functions import sign, unit_vector


# A Creature will need the functionality of both a CollisionEntity and an AnimatedEntity
class Creature(AnimatedEntity, CollisionEntity):
    ATTACK_FRAME_DURATION = 0.4
    health = 10
    damage_reduction = 0
    # A value ranging from 0 to 1 where 0 means no reduction in damage dealt and 1 means no damage is dealt
    damage_cooldown = 0.5
    # The time period in which the entity does not dealt damage or knowkcback after being damaged.
    # This is to prevent the entity from being damaged every frame it is in an another entity's attack rect

    air_friction = 0.1

    immune_damage_types: dict[str, bool] = {}
    # This dictionary stores what damage types a creature is immune from and if they should still deal knockback
    # This specified what damage types the entity is immune to.
    # The key is the damage type and the value dictates if the entity should experiance knockback

    knockback_reduction = 0
    # Value from 0 to 1 where 0 is no reduction and 1 is no knockback is dealt.

    attack_damage: int
    attack_rect_size: tuple[int, int]
    # The area in which the entity can attack other entities.
    # The attack rect property uses this value for it's size

    attack_duration = 0.2
    # How long the entity will check for other entities that intersect the attack rect to damage
    attack_cooldown = 1.0
    # How long the entity has to wait before attacking again
    attack_type = "melee"
    # The type of damage the entity deals
    knockback_strength = 1000
    # The strength of knockback in the entity's damage

    do_not_attack: tuple[type[Self], ...] = ()
    # A list of all entity types the current entity should not try to attack.
    
    die_time = 0.5
    # The time between when the kill method is called and when the enemy actually dies

    def __init__(
            self,
            x: int,
            y: int,
            facing: Literal["left", "right"] = RIGHT,
            *, velocity=p.Vector2(0, 0)
        ) -> None:
        
        super().__init__(x, y, self.hitbox, self.texture_map, self.animation_data, self.anim_controller_data, velocity=velocity)

        self.facing = 1 if facing == RIGHT else -1
        self.damage_cooldown: Timer = Timer(type(self).damage_cooldown)
        self.attack_cooldown = Timer(type(self).attack_cooldown)
        self.attack_duration = Timer(type(self).attack_duration)

        self.die_timer = Timer(self.die_time, execute_after=self.instant_kill)
        # This timer will be used to control the time between the kill method call and
        # when the entity is removed from the group.
        # I called the start method to prevent reoving the entity immediatly after being
        # summoned.


    @property
    def alive(self) -> bool:
        "Weather the entity has any health left."

        return self.health > 0.0
    

    @property
    def attack_rect(self) -> p.Rect:
        "The area in which the entity's attack can damage other entities."

        pos = self.position - p.Vector2(self.attack_rect_size)/2
        return p.Rect(*pos, *self.attack_rect_size)



    def update(self, delta_time: float) -> None:
        super().update(delta_time)

        if not self.alive:
            self.die_timer.update(delta_time)
            # Start a death animation if there is any
            return None

        if not self.attack_duration.complete:
            self.attack_tick(self.attack_damage)
            # Damage is applied to all attackable entities in the attack
            # rect full the full duration of the attack


        self.damage_cooldown.update(delta_time)
        self.attack_cooldown.update(delta_time)
        self.attack_duration.update(delta_time)

        self.process_tile_damage()


    def process_tile_damage(self) -> None:
        "Process damage caused by tiles that can do damage."

        for side, tiles in self.tile_contacts.items():
            for tile in tiles:
                if side in tile.damage_sides:
                    self.damage(*tile.damage_sides[side], p.Vector2(sign(self.rect.centerx-tile.rect.centerx)*2, sign(self.rect.centery-tile.rect.centery))*300)


    def _get_current_frame(self) -> p.Surface:
        # This method was modified to give the frame a red tint when the entity
        # gets damaged or dies.
        frame = super()._get_current_frame()

        if self.damage_cooldown.time_elapsed < self.ATTACK_FRAME_DURATION or not self.alive:
            frame.fill((100, 0, 0), special_flags=p.BLEND_RGB_ADD)
        
        return frame

        

    def damage(self, amount: int, type="melee", knockback = p.Vector2(0, 0)) -> None:
        "Decrements the health of the entity and applied knockback."

        if self.damage_cooldown.complete:
            if type not in self.immune_damage_types:
                self.health -= min(self.health, int(amount*(1-self.damage_reduction)))
                self.damage_cooldown.start()

            if self.immune_damage_types.get(type, True):
                self.accelerate(knockback)
        
        if not self.alive and self.die_timer.complete:
            self.kill()



    def heal(self, amount: int) -> None:
        "Increments the entity's health."
        self.health += min(type(self).health - self.health, amount)

    def restore_health(self) -> None:
        "Restore the entity's health to the full amount."
        self.health = type(self).health
        # The class attribute health stays the same when the instance attribute changes.
        # This can be used to remeber what the entity's maximum health is

    def attack(self) -> None:
        "Starts the attack process."
        if self.attack_cooldown.complete:
            self.attack_cooldown.start()
            self.attack_duration.start()

    
    def attack_tick(self, damage: int) -> None:
        "Damages all attackable entities in the attack rect."
        
        for entity in self.get_colliding_entities(self.attack_rect):
            if self.can_attack(entity):
                knockback = unit_vector(entity.position - self.position + (0, -60))*self.knockback_strength
                knockback.rotate_ip(randint(-15, 15)) # Adds random variation to the knockback
                knockback += (self.velocity.x/2, min(0, self.velocity.y)/2)
                # Knockback strength increases based on attacker entity velocity

                entity.damage(damage, self.attack_type, knockback)


    def kill(self) -> None:
        "Starts the die timer which creates a delay for when the entity actually dies."
        self.health = 0
        self.die_timer.start()


    def instant_kill(self) -> None:
        self.health = 0
        super().instant_kill()


    def can_attack(self, entity: Self) -> TypeGuard[Self]: # This essentually just returns a boolean
        "Determins if the current entity can attack another entity."
        return entity is not self and isinstance(entity, Creature)
    


    def navigate_to(self, position: p.Vector2) -> None:
        "This method is called every frame to allow the entity to navigate to a location in the world."
        # The functionality for this method will be implemented by subclass based
        # how they can move in the world




    def get_entity_data(self) -> EntityData:
        return EntityData(
            type(self).__name__,
            [*self.position],
            {
                name: self.attr_to_file_repr(attr)

                for name, attr in self.__dict__.items()
                if not isinstance(attr, p.Surface)
                and name in self.ATTRIBUTES_TO_SAVE
            }
        )





class Walker(Creature):
    "A type of creature that naviagtes the world by walking over tiles."

    walk_speed: int
    walk_acceleration = 4000
    # In units per second squared
    jump_speed: int
    jump_duration: float

    # Subclasses will assign what the values of these attributes should be.

    gravity_ratio = 4/5
    # Changes the strength of the gravity based weather the entity is
    # jumping up or falling down.
    # This creates a slightly more satisfying jump arc.


    def __init__(
            self,
            x: int,
            y: int,
            facing: Literal["left", "right"] = RIGHT,
            *,
            velocity=p.Vector2(0, 0)
        ) -> None:
        
        super().__init__(x, y, facing, velocity=velocity)

        self.walk_direction = 0
        self.jump_timer = Timer(self.jump_duration*(2 - self.gravity))


    @property
    def attack_rect(self) -> p.Rect:
        # The position of the attack rect changes based on the direction the entity
        # is facing
        pos = self.position - (0, self.attack_rect_size[1]/2)
        if self.facing == -1:
            pos.x -= self.attack_rect_size[0]
        
        return p.Rect(*pos, *self.attack_rect_size)
    


    def update(self, delta_time: float) -> None:
        super().update(delta_time)

        if self.walk_direction != 0:
            self.facing = self.walk_direction
            # Makes the facing direction match the direction the
            # entity was last walking in

        self.walk_direction = 0



    


    def update_motion_variables(self, delta_time: float) -> None:
        if self.jump_timer.complete:
            g = DEFUALT_GRAVITY*(self.gravity/self.gravity_ratio)
        else:
            g = DEFUALT_GRAVITY*(self.gravity*self.gravity_ratio)
        # Changes garvity strength based on if the entity is jumping up or falling down
        self.accelerate((0, g), delta_time)
        # Applies the gravity

        max_speed = self.max_movement_speed()

        # Conditions that need to be satisfied in order for the entity to accelerate in the walk direction
        walk_conditions = [
            abs(self.velocity.x) < max_speed or sign(self.velocity.x) != self.walk_direction,
            (self.walk_direction == 1 and not self.tile_contacts[RIGHT]) or (self.walk_direction == -1 and not self.tile_contacts[LEFT])
        ]

        if all(walk_conditions):
            acceleration_value = self.walk_acceleration*max(self.get_tile_friction()*self.gravity, 0.2)
            # acceleration_value = min(acceleration_value, abs(max_speed - self.velocity.x)/delta_time)
            acceleration_value *= self.walk_direction

            acceleration_vector = p.Vector2(acceleration_value, 0)
            for tile in self.tile_contacts[BOTTOM]:
                if isinstance(tile, Ramp) and tile.type[0] == BOTTOM:
                    if tile.type[1] == LEFT:
                        acceleration_vector.rotate_ip(45)
                        break
                        
                    elif tile.type[1] == RIGHT:
                        acceleration_vector.rotate_ip(-45)
                        break
            
            
            self.accelerate(acceleration_vector, delta_time)


        self.jump_timer.update(delta_time)


    def max_movement_speed(self) -> float:
        "Gets the speed the entity should be walking at."
        return self.walk_speed if self.tile_contacts[BOTTOM] else self.walk_speed/2



    def process_tile_friction(self, delta_time: float) -> None:
        if self.walk_direction != sign(self.velocity.x):
            super().process_tile_friction(delta_time)


    def get_tile_friction(self, side: Literal["top", "bottom", "left", "right"] = BOTTOM) -> float:
        if self.tile_contacts[side]:
            return super().get_tile_friction(side)
        elif self.walk_direction == 0:
            return 0.1
        else:
            return self.air_friction


    def walk(self, direction: Literal[1, -1]) -> None:
        "Called every frame to allow the entity to walk in a certain direction."

        self.walk_direction = sign(self.walk_direction + direction)


    def jump(self) -> None:
        "Used to start a jump. The longer it is called for the higher the entity jumps."

        if self.tile_contacts[TOP]:
            self.jump_timer.countdown = 0.0
        else:
            if self.tile_contacts[BOTTOM]:
                self.jump_timer.start()
            if self.jump_timer.countdown:
                self.velocity.y = -self.jump_speed*(self.gravity*0.6 + 0.4)


    
    def navigate_to(self, position) -> None:
        displacement = position - self.position
        self.walk(sign(displacement.x))

        if (
            (abs(displacement.x) < self.jump_speed*self.jump_duration and displacement.y < -50)
            or (displacement.x > 0 and self.tile_contacts[RIGHT])
            or (displacement.x < 0 and self.tile_contacts[LEFT])
            ):
            self.jump()
            # Makes the entity jump if they walk into a tile


    






class Flier(Creature):
    hitbox = (32, 32)
    gravity = 0
    fly_speed: int

    air_friction = 1.0
    
    def __init__(self, x, y, facing = RIGHT, *, velocity=p.Vector2(0, 0)) -> None:
        super().__init__(x, y, facing, velocity=velocity)

        self.fly_direction = p.Vector2(0, 0)



    def update(self, delta_time) -> None:
        super().update(delta_time)

        self.move(self.fly_direction , delta_time)

        if self.fly_direction.magnitude() != 0:
            self.facing = sign(self.fly_direction.x)

        self.fly_direction = p.Vector2(0, 0)

    
    def navigate_to(self, position) -> None:
        self.fly_direction = unit_vector(position-self.position)*self.fly_speed


    def get_tile_friction(self, side=BOTTOM) -> float:
        # This should just return the air priction as the entity won't be walking
        # on tiles.
        return self.air_friction