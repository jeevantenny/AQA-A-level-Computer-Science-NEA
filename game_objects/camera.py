"Contains the Camera class."

import pygame as p
from typing import Iterable
from math import sin, cos, pi

from . import TOP, BOTTOM, LEFT, RIGHT, NEGLEGIBE_VELOCITY
from .world import Chunk, ChunkManager, Ramp
from .entities import Entity, EntityManager
from .creature_types import Creature

from file_processing.assets import DebugFont
from custom_types.gameplay import FloatRect, Timer
from settings import video

from math_functions import clamp, vector_min, unit_vector
from debug import log, STATE_INFO











class Camera:
    """
    Captures an area of the world on every frame and is used to follow the player around an area. It
    dictates what part of the world is visible to the player.
    """

    SNAP_TO_DISTANCE = 5000
    # The distance the target position should be for the camera to just snap to
    # the position without moving towards it.
    MAX_SPEED = 7000
    # The maximum speed the camera can move at
    MOTION_CURVE_POWER = 1.7

    SHAKE_FREQ = 12
    # Frequency of the camerashake

    def __init__(self, surface: p.Surface, position: p.Vector2 | tuple[2], *, max_target_offset: tuple[int, int] = None, area_size=600) -> None:
        self.surface = surface
        self.target_pos = p.Vector2(0, 0)
        self.position = p.Vector2(position)
        self.velocity = p.Vector2(0, 0)
        self._target_offset_value = max_target_offset

        self._recentre = True

        self.area_size = area_size
        
        self.shake_timer = Timer(0).start()
        self.shake_intensity: p.Vector2 = None

        self.debug_font = DebugFont(12)



    
    @property
    def scale_value(self) -> float:
        "How much the game objects should be scaled by depending on the size of the game window."
        
        return min(*self.surface.get_size())/self.area_size
    

    @property
    def visible_area(self) -> FloatRect:
        "The position and area of the world that whould be visible on screen."
        area = FloatRect(0, 0, *p.Vector2(self.surface.get_size())/self.scale_value)
        area.center = self.position + self._shake_offset
        return area
    
    

    @property
    def _shake_offset(self) -> p.Vector2:
        """
        Returns visible offset of the camera when it is shaken at a point in time. The offset
        caused by shaking should not effect the actual position of the camera and is just for
        visual purposes.
        """
        if not video.camerashake or self.shake_intensity is None:
            return p.Vector2(0, 0)
            # If the camerashake setting is turned off or the camera isn't currently shaking the
            # shake offset should be (0, 0).
        
        return self.shake_intensity*sin(self.shake_timer.countdown*self.SHAKE_FREQ*2*pi)*cos(self.shake_timer.completion_amount*pi/2)


    def update(self, target: p.Vector2, delta_time: float, boundary: p.Rect | None = None) -> None:
        "Updates the position of the camera."

        self.__prep_camera(target.copy(), boundary)
            
        displacement = self.target_pos - self.position
        distance = displacement.magnitude()
        

        
        if 1 <= distance <= self.SNAP_TO_DISTANCE:
            self._recentre = True
            direction = displacement/distance
            
            self.velocity: p.Vector2 = direction*((self.MAX_SPEED-NEGLEGIBE_VELOCITY)*(min(distance, self.area_size)/self.area_size)**self.MOTION_CURVE_POWER + NEGLEGIBE_VELOCITY)

            self.position += vector_min(self.velocity*delta_time, displacement)
        else:
            self.snap_to(self.target_pos)
            self.velocity *= 0
            self._recentre = False


        self.shake_timer.update(delta_time)
        



    def snap_to(self, position: p.Vector2) -> None:
        "Snaps the camera to a position."

        self.position = position.copy()
        self._recentre = False
        self.velocity *= 0



        
        
    def __prep_camera(self, target: p.Vector2, boundary: p.Rect | None = None) -> None:
        """
        Sets the target position so that the visible area of the camera stays within the
        camera boundary.
        """

        self.target_pos = target

        if boundary is not None:
            w, h = p.Vector2(self.surface.get_size())/(self.scale_value)
            screen_boundary = boundary.inflate(-w, -h)
            # The area the target_pos has to be in so that the visible areas stays in the
            # camera boundary

            self.__keep_position_in_boundary(self.position, screen_boundary)
            self.__keep_position_in_boundary(self.target_pos, screen_boundary)
        

        
    




    def __keep_position_in_boundary(self, position: p.Vector2, boundary: p.Rect) -> None:
        "Clamps a position to be within a boundary represented by a Rect."

        if boundary.width:
            position.x = clamp(position.x, boundary.left, boundary.right)

        if boundary.height:
            position.y = clamp(position.y, boundary.top, boundary.bottom)
    




        
    def capture(
            self,
            chunk_manager: ChunkManager,
            entity_manager: EntityManager,
            background: p.Color,
            *,
            other_rects: Iterable[p.Rect] = [],
            show_rects = False,
            show_health = False,
            exclude_entity_types: list[type[Entity]] = []
        ) -> None:
        "Captures a scene in the world by using the draw functions of all the game objects."

        blit_surface = p.Surface(self.visible_area.size)
        blit_surface.fill(background)
        # The surface to draw all the game objects onto
        blit_offset = -p.Vector2(self.visible_area.topleft)
        # How much the objects should be offser by
            

        chunk_manager.draw_background(blit_surface, self.visible_area, blit_offset)
        chunk_manager.draw_middleground(blit_surface, self.visible_area, blit_offset)

        entity_manager.draw(blit_surface, blit_offset, exclude_types=exclude_entity_types)

        chunk_manager.draw_foreground(blit_surface, self.visible_area, blit_offset)
        # The background and middle-ground tiles are drawn behind the entities while the forground
        # tiles are drawn infront
        

        if show_rects: # Only True when debugging
            self.__draw_tile_and_chunk_hitboxes(chunk_manager, blit_surface, blit_offset)
            self.__draw_entity_hitboxes(entity_manager, blit_surface, blit_offset)

            for rect in other_rects:
                if self.visible_area.colliderect(rect):
                    FloatRect(*rect.topleft, *rect.size).draw(blit_surface, blit_offset, 1, "orange")

            self.__draw_crosshair(blit_surface, blit_offset)
            
        
        if show_health: # Only True when debugging
            self.__show_entity_health(entity_manager, blit_surface, blit_offset)
            


        blit_surface = p.transform.scale_by(blit_surface, self.scale_value)
        self.surface.blit(blit_surface, (0, 0))



    def __draw_tile_and_chunk_hitboxes(
            self,
            chunk_manager: ChunkManager,
            blit_surface: p.Surface,
            blit_offset: p.Vector2
        ) -> None:
        "Draws the hitboxes of middle-ground tiles and loaded chunks."
        
        # I have converted the hitboxes to FloatRects first as they provide a more accurate position

        for chunk in chunk_manager.loaded_chunks.values():
            if self.visible_area.colliderect(chunk.rect):
                for tile in chunk:
                    if tile.collision and self.visible_area.colliderect(tile.rect):
                        if isinstance(tile, Ramp):
                            p.draw.polygon(blit_surface, "green", tile.get_outline(blit_offset), 1)
                        else:
                            FloatRect(*tile.rect.topleft, *tile.rect.size).draw(blit_surface, blit_offset, 1, "green")
                
                FloatRect(*chunk.rect.topleft, *chunk.rect.size).draw(blit_surface, blit_offset, 1, "blue")



    def __draw_entity_hitboxes(
            self,
            entity_manager: EntityManager,
            blit_surface: p.Surface,
            blit_offset: p.Vector2
        ) -> None:
        "Draws the hitboxes of entities."
                    
        for entity in entity_manager:
            entity.rect.draw(blit_surface, blit_offset, 1, "red")




    def __draw_crosshair(self, blit_surface: p.Surface, blit_offset: p.Vector2) -> None:
        "Draws a crosshair which represents the camera's target position."
            
        blit_target_pos = self.target_pos + blit_offset
        p.draw.line(blit_surface, "black", blit_target_pos - (11, 0), blit_target_pos + (11, 0), 3)
        p.draw.line(blit_surface, "black", blit_target_pos - (0, 11), blit_target_pos + (0, 11), 3)

        p.draw.line(blit_surface, "white", blit_target_pos - (10, 0), blit_target_pos + (10, 0))
        p.draw.line(blit_surface, "white", blit_target_pos - (0, 10), blit_target_pos + (0, 10))




    def __show_entity_health(
            self,
            entity_manager: EntityManager,
            blit_surface: p.Surface,
            blit_offset: p.Vector2
        ) -> None:
        "Displays the health of all Creature type entities."

        for entity in entity_manager:
            if isinstance(entity, Creature):
                text = self.debug_font.render(f"{entity.health}/{entity.__class__.health}", True, "white", "black")
                blit_pos = (entity.rect.centerx, entity.rect.y - 20) - p.Vector2(text.get_size())*0.5 + blit_offset
                blit_surface.blit(text, blit_pos)





    def camerashake(self, duration=1.0, intensity=3.0, direction=p.Vector2(0, 1)) -> None:
        "Triggers the camera to shake."

        log(STATE_INFO, "Camera Shaken")
        self.shake_intensity = unit_vector(direction)*intensity
        self.shake_timer.duration = duration
        self.shake_timer.start()