"""
Entities are sprites that will be able to move within the world. They will have a position
(which uses a different unit to tile position) and a velocity. The position determines where
to render the entity and the velocity determines how the position should change in the next
frame
"""

import pygame as p
from typing import Any, Literal, Callable
from collections import defaultdict
from copy import deepcopy

from . import TOP, BOTTOM, LEFT, RIGHT, NEGLEGIBE_VELOCITY, DEFUALT_GRAVITY, scale_game_object

from .world import FRICTION_MULTIPLIER, Tile, Ramp, loaded_chunk_dict

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import FloatRect, Coordinate
from custom_types.animation import Animation, SpriteAnimation, AnimController
from custom_types.file_representation import EntityData

from math_functions import clamp, sign

from debug import log, STATE_INFO
from errors import InitialisationError





class Entity(p.sprite.Sprite, BasicGameElement):
    """
    This is the base Entity class. This class contains methods use to control the movement
    of the entity and 
    """

    MAX_VELOCITY = (5000, 5000)
    # This is the maximum x and y velocity an entity can 

    hitbox: tuple[int, int]
    group = None
    gravity = None
    collision_chunks = None

    kill_when_out_of_range = False
    always_update = False
    # Settings this to True means that the entity will always be updated dispite being out of
    # render distance

    draw_level = 0

    ATTRIBUTES_TO_SAVE = []
    # These are the names of changed attributes that need to be stored in the EntityData object
    # when  an entity is saved into a save file.

    camerashake: Callable[[float, float, p.Vector2], None]

    @classmethod
    def init_class(
        cls,
        group,
        collision_chunks: loaded_chunk_dict,
        gravity_multiplier: float,
        entity_assets: dict[str, dict]
        ) -> None:
        """
        Initialses the Entity class and assigned values to class atrributes. This method
        must be called before any Entity instances are created. Otherwise it will raise
        an InitialisationError.

        This method also loads any assets required by any entity class.
        """
        
        cls.gravity = gravity_multiplier
        # a float value that will be multiplied by the DEFAULT_GRAVITY to control
        # the amount of gravity experianced by the entities.

        cls.collision_chunks = collision_chunks
        # The same dictionary that is within the ChunkManager object that provide
        # collision for certain entities

        cls.group: EntityManager = group
        # The EntityManager all the entities are currently using.

        # The Entity class is initialized every time a new region is loaded to update
        # any of these attributes.
        
        cls.load_assets(entity_assets)
        # Loads the assets for any subclasses that require them.
        super().init_class()


    @classmethod
    def from_save(cls, entity_data: EntityData) -> "Entity":
        "Creates an entity from the given EntityData object. This entity is added to the entity group."

        entity_class = cls.find_class_by_name(entity_data.class_name)
        # Finds the entity class from the name
        obj: Entity = entity_class(*entity_data.init_args)
        # Creates an instance of the class with the init arguments

        for name, value in entity_data.changed_attributes.items():
            if isinstance(value, EntityData):
                value = cls.from_save(value)
                # If the value to add is itself another EntityData it will first be convert to an entity
                # before being assigned to the attribute.

            setattr(obj, name, deepcopy(value))
            # Changes the attribute value to the one stored in the EntityData object

        return obj


    def get_entity_data(self) -> EntityData:
        """
        Gets the entity data for the current entity. The returned EntityData object can be saved
        to a save file.
        """
        
        # Since Entity is a base class an instance should not be created without also being an instance of a child class
        # Therefore there will be no need to create an EntityData object from this class
        raise NotImplementedError(f"Cannot get entity data from base class '{type(self).__name__}'.")
    


    def attr_to_file_repr(self, attr) -> Any | EntityData:
        """
        A method that converts an attribute from an Entity class to a suitable format to be pickled. This will
        be used when creating EntityData objects.
        """

        if isinstance(attr, Entity):
            return attr.get_entity_data()
        
        return deepcopy(attr)
    

    def __init__(
            self,
            x: int,
            y: int,
            hitbox: tuple[int, int],
            texture: p.Surface,
            *,
            velocity = p.Vector2(0, 0)
        ) -> None:

        if self.group is None:
            raise InitialisationError("Entity instance created before class initialisation.")
        
        if not self.assets_loaded:
            raise InitialisationError("Entity instance created before class assets were loaded.")
        
        super().__init__(self.group)
        # When an instance is created it is immideatly added to the EntityManager group.

        self.texture = texture

        self.rect = FloatRect(0, 0, *hitbox)
        self.rect.center = x, y
        self.velocity = p.Vector2(velocity)

        log(STATE_INFO, f"Summoned {self} at {self.rect.topleft}")





    
    @property
    def position(self) -> p.Vector2:
        "The position of the entity from its center."
        return p.Vector2(self.rect.center)
    

    @position.setter
    def position(self, value: Coordinate) -> None:
        self.rect.center = value



    def snap_to_tile(self, tile_pos: Coordinate) -> None:
        "Moves the entity to the middle of a tile with the bottom of the entity in contact with the top of the tile."

        self.rect.centerx = (tile_pos[0]+0.5)*Tile.SIZE
        self.rect.bottom = (tile_pos[1]+1)*Tile.SIZE


    def get_occupying_tile(self) -> tuple[int, int]:
        "Returns the position of the current tile the entity occupies."

        return self.rect.centerx//Tile.SIZE, (self.rect.bottom-1)//Tile.SIZE


    
    def get_colliding_entities(self, rect: p.Rect | FloatRect = None) -> list["Entity"]:
        """
        Returns all other entities in the group that collide with a Rect or FloatRect object.
        If no Rect or FloatRect is given the rect for the entity's hitbox is used.
        """

        if rect is None:
            rect = self.rect

        entities: list[Entity] = []
        
        for entity in self.group:
            if entity is not self and entity.rect.colliderect(rect):
                entities.append(entity)
        
        return entities
    



    def update(self, delta_time: float) -> None:
        "Processes the movement and behaviour of the entity in one frame."

        self.move(self.velocity, delta_time)



    def draw(self, surface: p.surface.Surface, offset: Coordinate = (0, 0), alpha=255) -> None:
        "Draws the entity on a surface at its position."

        blit_texture = scale_game_object(self.texture)
        blit_pos = self.rect.center - p.Vector2(blit_texture.get_size())/2
        
        self.texture.set_alpha(alpha)
        surface.blit(blit_texture, blit_pos + offset)


    
    def accelerate(self, value: Coordinate, delta_time: float = 1.0) -> None:
        "Increment the velocity of the entity."

        self.velocity += p.Vector2(value)*delta_time
        self.velocity.x = clamp(self.velocity.x, -self.MAX_VELOCITY[0], self.MAX_VELOCITY[0])
        self.velocity.y = clamp(self.velocity.y, -self.MAX_VELOCITY[1], self.MAX_VELOCITY[1])
        



    def move(self, value: Coordinate, delta_time: float = 1.0) -> None:
        "Increment the position of the entity."

        self.rect.topleft = self.rect.topleft + p.Vector2(value)*delta_time


    def teleport(self, position: Coordinate) -> None:
        "Teleports the entity to a location and sets it's velocity to zero."
        # As of now this method is only used in debugging mode.
        self.position = position
        self.velocity *= 0



    def kill(self) -> None:
        """
        Removes the entity from the entity group.

        Child classes can modify this method to perform certain actions such as summon more entities
        or play an animation before actually being removed from the group.
        """

        super().kill()
        log(STATE_INFO, f"Killed {self}")


    def instant_kill(self) -> None:
        """
        This functions the same as the kill method. The intention is that even if the main kill method is
        modified this method stays largely the same so that it can be used when the entity needs to be
        removed instantly without creating more entities or performing other actions that may not be needed.
        """
        
        super().kill()
        log(STATE_INFO, f"Killed {self}")

    

         
    def __str__(self) -> str:
        return type(self).__name__
    


    def __repr__(self) -> str:
        return f"{type(self).__name__}(x: {self.rect.x}, y: {self.rect.y})"
    



    def add(self, group) -> None:
        "Adds an entity to a group if it wasn't added in the first place."
        super().add(group)

        if group.camerashake_callback is not None:
            self.camerashake = group.camerashake_callback
            # This allows entities to control the shaking of the camera directly
    



class CollisionEntity(Entity):
    """
    This type of entity can process collision between tiles.
    """

    def __init__(
            self,
            x: int,
            y: int,
            hitbox: tuple[int, int],
            texture: p.Surface,
            *,
            velocity=p.Vector2(0, 0)
        ) -> None:
        
        super().__init__(x, y, hitbox, texture, velocity=velocity)

        self.tile_contacts: dict[str, set[Tile]] = {
            TOP: set(),
            BOTTOM: set(),
            LEFT: set(),
            RIGHT: set(),
            "any": set()
        }
        # All the tiles that are in contact with the entity's hitbox and on what side.
    


    def update(self, delta_time: float) -> None:
        self.update_motion_variables(delta_time)
        super().update(delta_time)
        self.process_collision()
        self.process_tile_friction(delta_time)
    


    
    def update_motion_variables(self, delta_time: float) -> None:
        "Udates all variables related to motion for one frame that is not the position."
        if not self.tile_contacts[BOTTOM]:
            self.accelerate((0, self.gravity*DEFUALT_GRAVITY), delta_time)





    def move(self, value: Coordinate, delta_time: float = 1.0) -> None:
        "Increment the position of the entity with collision."

        x_move, y_move = p.Vector2(value)*delta_time


        for side in self.tile_contacts.values():
            side.clear()
            


        self.rect.y += y_move
        for chunk in self.collision_chunks.values():
            chunk.entity_y_collision(self.rect, y_move, self.tile_contacts)
            
        self.rect.x += x_move
        for chunk in self.collision_chunks.values():
            chunk.entity_x_collision(self.rect, x_move, self.tile_contacts)
        





    def process_collision(self) -> None:
        "Updates the velocity based on collision."
        
        if self.tile_contacts[TOP]:
            self.velocity.y = max(self.velocity.y, 0)
        if self.tile_contacts[BOTTOM]:
            self.velocity.y = min(self.velocity.y, 0)
        
        if self.tile_contacts[LEFT]:
            self.velocity.x = max(self.velocity.x, 0)
        if self.tile_contacts[RIGHT]:
            self.velocity.x = min(self.velocity.x, 0)





    def get_tile_friction(self, side: Literal["top", "bottom", "left", "right"] = BOTTOM) -> float:
        "Returns the friction caused by any tiles."
        friction = 0.0
        for tile in self.tile_contacts[side]:
            friction = max(friction, tile.friction)


        return friction

            

    def process_tile_friction(self, delta_time: float) -> None:
        """
        Changes the velocity based friction caused by tiles.
        """

        if self.velocity.magnitude() > NEGLEGIBE_VELOCITY:
            direction = -sign(self.velocity.x)
            self.velocity.x += min(FRICTION_MULTIPLIER*self.get_tile_friction()*delta_time, abs(self.velocity.x))*direction
        else:
            self.velocity *= 0

        

    


class AnimatedEntity(Entity):
    """
    This entity type can display an animated texture using the Animation and AnimController
    objects. The AnimController object is created when the object is initialized when a
    frame needs to be drawn a texture map is passed in.
    """

    texture_map: dict[str, p.Surface]
    animation_data: dict
    anim_controller_data: dict | None = None




    def __init__(
            self,
            x: int,
            y: int,
            hitbox: tuple[int, int],
            frames: dict[str, p.Surface],
            animation_data: dict[str, str | dict],
            controller_data: dict | None,
            *,
            velocity = p.Vector2(0, 0)
        ) -> None:


        self.texture_map = frames.copy()

        if controller_data is not None:
            self.animation = AnimController(controller_data, self.__get_animations(animation_data))
        else:
            self.animation = Animation(*list(animation_data["animations"].items())[0])

        super().__init__(
            x=x,
            y=y,
            hitbox=hitbox,
            texture=p.Surface((10, 10)),
            velocity=velocity
        )

        del self.texture



    def __get_animations(self, animation_data: dict[str, str | dict]) -> dict[str, SpriteAnimation]:
        "Returns a dictionary containing the name and animations using the animation_data asset prpvided."
        return {name: SpriteAnimation(name, anim_data) for name, anim_data in animation_data["animations"].items()}


    

    def update(self, delta_time) -> None:
        "Processes the movement, behaviour and animation of the entity in one frame."

        super().update(delta_time)

        self.animation.update(delta_time, self)
        





    def _get_current_frame(self) -> p.Surface:
        "Gets the current frame to be drawn onto the surface."
        return self.animation.get_frame(self.texture_map).copy()




    def draw(self, surface, offset=(0, 0), alpha=255) -> None:
        "Draws the entity on a surface at its position with the current animation frame."

        blit_texture = scale_game_object(self._get_current_frame())
        blit_pos = (self.rect.centerx - blit_texture.get_width()/2, self.rect.top - blit_texture.get_height() + self.rect.height)
        blit_texture.set_alpha(alpha)
        surface.blit(blit_texture, blit_pos + p.Vector2(offset))









class EntityManager(p.sprite.AbstractGroup[Entity | AnimatedEntity | CollisionEntity]):
    "Controls the updating and drawing of entities."
    def __init__(self, process_distance: int = 900, kill_depth: int = 50000, camerashake_callback: Callable = None) -> None:
        super().__init__()
        self.process_distance = process_distance
        self.kill_depth = kill_depth
        self.camerashake_callback = camerashake_callback


    def update(self, delta_time: float, process_point: Coordinate) -> int:
        "Process all entities in the group that are within processing range. Returns the number of entities updated."

        updated_entities = 0

        for entity in self.spritedict.copy():
            if entity.rect.y > self.kill_depth:
                log(STATE_INFO, f"{entity} fell out of world.")
                entity.instant_kill()
            elif entity.always_update or (abs(entity.position.x-process_point[0]) <= self.process_distance and abs(entity.position.y-process_point[1]) <= self.process_distance/2):
                entity.update(delta_time)
                updated_entities += 1
            elif entity.kill_when_out_of_range:
                entity.instant_kill()
        

        return updated_entities



    def draw(
            self,
            surface: p.Surface,
            offset = p.Vector2(0, 0),
            alpha = 255,
            *,
            exclude_types: list[Entity] = []
        ) -> None:

        "Draw all entities on a surface at their positions."

        exclude_types = tuple(exclude_types)

        draw_level_dict = defaultdict(set[Entity])
        for entity in self.spritedict.copy():
            if not isinstance(entity, exclude_types): # Doesn't draw entities of any type that is excluded
                draw_level_dict[entity.draw_level].add(entity)
        
        draw_order = sorted(draw_level_dict.items())

        for _, level in draw_order:
            for entity in level:
                entity.draw(surface, offset, alpha)
            
    
    def accelerate(self, value: p.Vector2, delta_time: float) -> None:
        "Increment the velocity of all entities."

        for entity in self.spritedict.copy():
            entity.accelerate(value, delta_time)


    
    def move(self, value: Coordinate, delta_time: float) -> None:
        "Increment the position of all entities."
        
        for entity in self.spritedict.copy():
            entity.move(value, delta_time)



    
    def get_entity_data(self, exclude_types: list[type[Entity]] = []) -> list[EntityData]:
        """
        Gets the EntityData from all entities that support it. The returned list will be used
        in the SaveFile object.
        """

        from .creature_types import Creature
        data_list = []
        exclude_types = tuple(exclude_types)
        for entity in self:
            if not (isinstance(entity, exclude_types) or (isinstance(entity, Creature) and not entity.alive)):
                try:
                    data_list.append(entity.get_entity_data())
                except NotImplementedError: pass
                # Ignore entities that don't support EntityData
        
        return data_list
    

    def add(self, *sprites: Entity | CollisionEntity | AnimatedEntity) -> None:
        "Adds entities to the EntityManager if they weren't already in it."
        
        super().add(*sprites)

        if self.camerashake_callback is not None:
            for sprite in sprites:
                sprite.camerashake = self.camerashake_callback



    
    def __repr__(self) -> str:
        return f"{self.sprites()}"