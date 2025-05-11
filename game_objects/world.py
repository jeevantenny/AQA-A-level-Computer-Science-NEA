"""
This module includes object types used to generate the world and maintain it.

The 'x' and 'y' position arguments for these objects should be relative positions. Actual positions can be found
in the rect attribute.
"""

import pygame as p
from functools import partial
from typing import Any, Generator, Literal, Self, Callable

from custom_types.gameplay import FloatRect, Coordinate
from custom_types.file_representation import TileData

from . import TOP, BOTTOM, LEFT, RIGHT, AIR, scale_game_object







FRICTION_MULTIPLIER = 10000
BACKGROUND_TILE_DIM_AMOUNT = 140

class Tile:
    """
    The smallest building blocks of a region. Tiled are used to design the terrian
    and provide collision for entities. There are a few different types of tile that
    have different sizsed hitboxes.

    Tiles are grouped together into 16x16 grids using chunks.

    A Tile is uniquely identified by a single string character called a tile code.
    """

    SIZE: int = 48
    COLLISION_TOLERANCE = 15
    # This is the maximum distance an entity can be from the corner of
    # a tile for it to not register an x collsion.
    # This is done to avoid the entity's hitbox catching the corner of a
    # tile's hitbox

    all_tile_data: dict[str, TileData]
    def __new__(cls, chunk, x, y, tile_code: str, break_tile_callback) -> Self:
        if cls.all_tile_data[tile_code].type in ["full", "top_slab", "bottom_slab"]:
            return super().__new__(cls)
        else:
            return Ramp(chunk, x, y, tile_code, break_tile_callback)
    


    def __init__(self, chunk, x: int, y: int, tile_code: str, break_tile_callback: Callable[[bool], None]) -> None:
        self.chunk: Chunk = chunk
        self.x, self.y = x, y
        self.code = tile_code

        self._set_rect(self.chunk.rect.topleft)

        self.break_tile = break_tile_callback

    @property
    def tile_data(self) -> TileData:
        return self.all_tile_data[self.code]
    
    @property
    def name(self) -> str:
        return self.tile_data.name

    @property
    def type(self) -> str:
        return self.tile_data.type

    @property
    def texture(self) -> p.Surface:
        return self.tile_data.texture[0]
    
    @property
    def collision(self) -> bool:
        return self.tile_data.collision
    
    @property
    def breakable(self) -> bool:
        return self.tile_data.breakable
    
    @property
    def friction(self) -> float:
        return self.tile_data.friction
    
    @property
    def wall_jump(self) -> bool:
        return self.tile_data.wall_jump
    
    @property
    def damage_sides(self) -> dict[str, tuple[int, str]]:
        return self.tile_data.damage_sides


    def break_tile(self, break_surroundings=False) -> None:
        "Removes the tile from the world."
        ...
        
        # The code for this function will be implemented when an instance is created. 
    


    def get_neighbour(self, offset: Coordinate) -> (Self | None):
        for tile in self.chunk.midground_tiles:
            if (tile.x, tile.y) == (self.x+offset[0], self.y+offset[1]):
                return tile
        
        return None


    def _set_rect(self, chunk_pos: tuple[int, int]) -> None:
        "Sets the hitbox for the tile."

        self.rect = p.Rect(chunk_pos[0]+self.x*self.SIZE, chunk_pos[1]+self.y*self.SIZE, self.SIZE, self.SIZE)

        match self.type:
            case "full":
                self.rect = p.Rect(chunk_pos[0]+self.x*self.SIZE, chunk_pos[1]+self.y*self.SIZE, self.SIZE, self.SIZE)

            case "top_slab":
                self.rect.height = self.SIZE/2

            case "bottom_slab":
                self.rect = p.Rect(chunk_pos[0]+self.x*self.SIZE, chunk_pos[1]+(self.y+0.5)*self.SIZE, self.SIZE, self.SIZE/2)



    
    def entity_x_collision(self, entity_rect: FloatRect, x_move: float) -> (None | Literal["left", "right"]):
        """
        Processes the x collision for an entity and returns the side of entity
        that collides with the tile.
        """

        if entity_rect.colliderect(self.rect):
            if (entity_rect.bottom - self.rect.top) < self.COLLISION_TOLERANCE:
                return None
            
            if x_move > 0:
                entity_rect.right = self.rect.left
            elif x_move < 0:
                entity_rect.left = self.rect.right

        return entity_rect.contact_with(self.rect)




    def entity_y_collision(self, entity_rect: FloatRect, y_move: float) -> (None | Literal["top", "bottom"]):
        """
        Processes the y collision for an entity and returns the side of entity
        that collides with the tile.
        """

        if entity_rect.colliderect(self.rect):
            if y_move > 0 and self.rect.bottom-entity_rect.top > self.COLLISION_TOLERANCE:
                entity_rect.bottom = self.rect.top
            elif y_move < 0 and entity_rect.bottom-self.rect.top > self.COLLISION_TOLERANCE:
                entity_rect.top = self.rect.bottom

        return entity_rect.contact_with(self.rect)
    


    
    def draw(self, surface: p.Surface, offset: p.Vector2, alpha = 255) -> None:
        "Draws the tile at it's position."
        
        blit_texture = scale_game_object(self.texture)
        blit_texture.set_alpha(alpha)

        blit_pos = self.chunk.rect.topleft + p.Vector2(self.x, self.y)*self.SIZE

        surface.blit(blit_texture, blit_pos+offset)

    
    def __str__(self) -> str:
        return f"{type(self).__name__}('{self.name}')"
    

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name: '{self.name}', x: {self.x}, y: {self.y}, surrounded: {self.surrounded})"









class Ramp(Tile):
    """
    A type of tile that has a triangular hitbox. It allows the player and
    other entities to walk up them without having to jump.
    """

    ramp_types = {
        "topleft_ramp": (TOP, LEFT),
        "topright_ramp": (TOP, RIGHT),
        "bottomleft_ramp": (BOTTOM, LEFT),
        "bottomright_ramp": (BOTTOM, RIGHT)
    }
    # These are the four ramp types
    
    def __new__(cls, *args) -> Self:
        return object().__new__(cls)
        # Overides the __new__ method of Tile to prevent it from infinately recurring.
        

    @property
    def type(self) -> tuple[str, str]:
        return self.ramp_types[self.all_tile_data[self.code].type]


    
    def _set_rect(self, chunk_pos) -> None:
        self.rect = p.Rect(chunk_pos[0]+self.x*self.SIZE, chunk_pos[1]+self.y*self.SIZE, self.SIZE, self.SIZE)


    
    def __get_collision_height(self, entity_rect: FloatRect) -> float:
        if self.type[1] == LEFT:
            height_offset = min((self.rect.right - entity_rect.left), self.rect.height)
        else:
            height_offset = min((entity_rect.right - self.rect.left), self.rect.height)


        if self.type[0] == TOP:
            return self.rect.top + height_offset
        else:
            return self.rect.bottom - height_offset
            

    

    def entity_x_collision(self, entity_rect: FloatRect, x_move: float) -> None:
        if self.type[0] == BOTTOM:
            if entity_rect.top < self.rect.bottom < entity_rect.bottom:
                super().entity_x_collision(entity_rect, x_move)
        elif self.type[0] == TOP:
            if entity_rect.top < self.rect.top < entity_rect.bottom:
                super().entity_x_collision(entity_rect, x_move)



    
    def entity_y_collision(self, entity_rect: FloatRect, y_move: float) -> None | Literal["top", "bottom"]:
        if entity_rect.colliderect(self.rect):
            collision_height = self.__get_collision_height(entity_rect)
            if y_move < 0 and self.type[0] == TOP:
                if entity_rect.top <= collision_height:
                    entity_rect.top = collision_height
                    return TOP
            


            elif y_move > 0 and self.type[0] == BOTTOM:
                if self.type == (BOTTOM , LEFT):
                    collision_height = self.rect.bottom - min((self.rect.right - entity_rect.left), self.rect.height)
                elif self.type == (BOTTOM , RIGHT):
                    collision_height = self.rect.bottom - min((entity_rect.right - self.rect.left), self.rect.height)
                
                if entity_rect.bottom >= collision_height:
                    entity_rect.bottom = collision_height
                    return BOTTOM
                


    
    def get_outline(self, offset: Coordinate = (0, 0)) -> list[tuple[float, float]]:
        """
        Gets the hitbox outline as a list of vertex positions. This will be used when debugging
        to show the shape of the ramp's hitbox.
        """

        offset = p.Vector2(offset)
        corners = set()

        if self.type[0] == TOP:
            corners.add(tuple(self.rect.topleft+offset))
            corners.add(tuple(self.rect.topright+offset))
        else:
            corners.add(tuple(self.rect.bottomleft+offset))
            corners.add(tuple(self.rect.bottomright+offset))
        
        

        if self.type[1] == LEFT:
            corners.add(tuple(self.rect.topleft+offset))
            corners.add(tuple(self.rect.bottomleft+offset))
        else:
            corners.add(tuple(self.rect.topright+offset))
            corners.add(tuple(self.rect.bottomright+offset))

        return list(corners)

    
                





class Chunk:
    """
    A Chunk is a 16x16 grid of tiles. It can show tiles in the foreground, middle-ground
    and background. These are represented in the region file by 3 seperate strings of tile
    code characters. The Chunk interprets them creates 3 sets for each layer.
    """
    TILES_PER_SIDE = 16
    SIZE = Tile.SIZE*TILES_PER_SIDE
    def __init__(self, x: int, y: int, break_tile_callback: Callable[[tuple[int, int]], None], tile_codes: dict[str, str] | None, broken_tiles: set[tuple[int, int]] = set()) -> None:
        self.x, self.y = x, y
        self.rect = p.Rect(self.x*self.SIZE, self.y*self.SIZE, self.SIZE, self.SIZE)

        self.background_tiles: set[tuple[int, int, p.Surface, str]] = set()
        self.midground_tiles: set[Tile | Ramp] = set()
        self.foreground_tiles: set[tuple[int, int, p.Surface, str]] = set()
        # The three layers of tiles. Only the middle-ground uses actual Tile objects.

        
        self.break_tile = break_tile_callback

        if tile_codes is not None:
            if tile_codes.get("B") is not None:
                self.set_background(tile_codes["B"])
                
            if tile_codes.get("M") is not None:
                self.set_middle_ground(tile_codes["M"], broken_tiles)
                
            if tile_codes.get("F") is not None:
                self.set_foreground(tile_codes["F"])
    


    @property
    def all_tiles(self) -> set[Tile | Ramp]:
        return self.midground_tiles
        # The other chunk layers used to use Tile objects before I changed
        # it to use just the tile textures. So instead of changing code
        # elsewhere to account for this change i changed this property to
        # only return the middleground tiles.
    


    def set_background(self, tile_codes: str) -> None:
        self.background_tiles.clear()

        for i, code in enumerate(tile_codes):
            if code != AIR:
                self.background_tiles.add((
                    *index_to_tile_coordinates(i),
                    Tile.all_tile_data[code].texture[1],
                    code
                ))
    

    def set_middle_ground(self, tile_codes: str, broken_tiles: set[tuple[int, int]]) -> None:
        self.midground_tiles.clear()
        # input(tile_codes)

        for i, code in enumerate(tile_codes):
            if code != AIR and index_to_tile_coordinates(i) not in broken_tiles:
                x, y = index_to_tile_coordinates(i)
                self.add_tile(x, y, code)

                
    def set_foreground(self, tile_codes: str) -> None:
        self.foreground_tiles.clear()

        for i, code in enumerate(tile_codes):
            if code != AIR:
                self.foreground_tiles.add((
                    *index_to_tile_coordinates(i),
                    Tile.all_tile_data[code].texture[0],
                    code
                ))

    

    def draw_background(
            self,
            surface: p.Surface,
            visible_area: FloatRect,
            offset = p.Vector2(0, 0),
            alpha = 255
        ) -> None:
        self.__draw_lightweight_tiles(surface, self.background_tiles, visible_area, offset, alpha)


    def draw_midground(
            self,
            surface: p.Surface,
            visible_area: FloatRect,
            offset = p.Vector2(0, 0),
            alpha = 255
        ) -> None:
        for tile in self.midground_tiles:
            if visible_area.colliderect(tile.rect):
                tile.draw(surface, offset, alpha)


    def draw_foreground(
            self,
            surface: p.Surface,
            visible_area: FloatRect,
            offset = p.Vector2(0, 0),
            alpha = 255
        ) -> None:
        self.__draw_lightweight_tiles(surface, self.foreground_tiles, visible_area, offset, alpha)



    def __draw_lightweight_tiles(
            self,
            surface: p.Surface,
            tiles: set[tuple[int, int, p.Surface, str]],
            visible_area: FloatRect,
            offset = p.Vector2(0, 0),
            alpha = 255
        ) -> None:
        "Draws the textures for a layer of tiles represented by textures instead of Tile objects."

        for x, y, tile, _ in tiles:
            tile_pos = self.rect.topleft + p.Vector2(x, y)*Tile.SIZE
            if visible_area.colliderect(p.Rect(*tile_pos, Tile.SIZE, Tile.SIZE)):
                blit_tile = tile.copy()
                blit_tile.set_alpha(alpha)
                surface.blit(scale_game_object(blit_tile), tile_pos + offset)
    

    
    def entity_x_collision(self, entity_rect: FloatRect, x_move: float, side_contacts: dict[str, set]) -> None:
        "Processes the entity x collsision for all the tiles in the chunk."

        for tile in self.midground_tiles:
            if tile.collision:
                contact_side = tile.entity_x_collision(entity_rect, x_move)
                if contact_side is not None:
                    side_contacts[contact_side].add(tile)
                    side_contacts["any"].add(tile)





    def entity_y_collision(self, entity_rect: FloatRect, y_move: float, side_contacts: dict[str, set]) -> None:
        "Processes the entity y collsision for all the tiles in the chunk."
        
        for tile in self.midground_tiles:
            if tile.collision:
                contact_side = tile.entity_y_collision(entity_rect, y_move)
                if contact_side is not None:
                    side_contacts[contact_side].add(tile)
                    side_contacts["any"].add(tile)


    def add_tile(self, x: int, y: int, code: str) -> None:
        "Adds a tile to the middle ground of the chunk."

        self.midground_tiles.add(Tile(self, x, y, code, partial(self.break_tile, (x, y))))


    def break_tile(self, tile_pos: tuple[int, int], break_surroundings=False) -> None:
        """
        Breaks a tile in the middle ground at the position in the chunk specified, if it's breakable property is set to True.
        """
        # This method is implemented when an instance is created



    def __iter__(self) -> Generator[Tile | Ramp, Any, None]:
        for tile in self.all_tiles:
            yield tile
            


    def __str__(self) -> str:
        return type(self).__name__
    


    def __repr__(self) -> str:
        return f"{Self.__class__.__name__}(x: {self.x}, y: {self.y})"
    

### Code only works in python 3.12
# type loaded_chunk_dict = dict[tuple[int, int], Chunk]
# type raw_chunk_dict = dict[tuple[int, int], dict[str, str]]
    
class loaded_chunk_dict(dict[tuple[int, int], Chunk]): pass
class raw_chunk_dict(dict[tuple[int, int], dict[str, list[str] | None]]): pass



class ChunkManager:
    """
    Manages the loading and unloading of chunks. Chunks are loaded using their raw chunk
    data 
    """

    def __init__(
            self,
            loaded_chunks: loaded_chunk_dict,
            raw_chunks: raw_chunk_dict,
            tile_data: dict[str, TileData],
            chunk_render_distance: int = 5
        ) -> None:

        self.loaded_chunks = loaded_chunks
        self.raw_chunks = raw_chunks
        Tile.all_tile_data = tile_data
        # Sets the tile data the Tiles will use to gain their properties

        self.chunk_distance = chunk_render_distance
        # How many chunks away from the player will be loaded in

        self._broken_tiles: dict[tuple[int, int], set[tuple[int, int]]] = {}
        # Stores the list of all the tiles that were broke during gameplay.
        # Tiles in this list will be ignored when generating new chunks
    

    @property
    def broken_tiles(self) -> dict[tuple[int, int], set[tuple[int, int]]]:
        """
        Returns all the tiles that have been broken during gameplay for each chunk. This
        information will be stored into the save file to ensure tiles remain broken between
        play sessions.
        """
        return self._broken_tiles
    
    @broken_tiles.setter
    def broken_tiles(self, value: dict[tuple[int, int], set[tuple[int, int]]]) -> None:
        "Sets the broken tiles."

        self._broken_tiles = value.copy()



    def update(self, load_pos: p.Vector2) -> None:
        chunks_to_load = self.__get_allowed_chunk_locations(load_pos)

        for pos in self.loaded_chunks.copy():
            if pos in chunks_to_load:
                chunks_to_load.remove(pos)
                # Removes the position from the list if the chunk is already loaded in.
            else:
                self.loaded_chunks.pop(pos)
                # Unloads the loaded chunk if it no longer needs to be loaded.

        
        for pos in chunks_to_load:
            if pos in self.raw_chunks:
                tile_codes = self.raw_chunks[pos]
                self.loaded_chunks[pos] = Chunk(
                    *pos,
                    partial(self.break_tile, pos),
                    tile_codes,
                    self.broken_tiles.get(pos, set())
                )
                # Loads any chunks that need to be loaded.




    def __get_allowed_chunk_locations(self, load_pos: p.Vector2) -> set[tuple[int, int]]:
        "Gets the location of all the chunks that should be loaded in."

        current_chunk = (load_pos.x//Chunk.SIZE, load_pos.y//Chunk.SIZE)
        locations = set()

        for y in range(-self.chunk_distance, self.chunk_distance+1):
            x_variance = self.chunk_distance - abs(y)
            for x in range(-x_variance, x_variance+1):
                locations.add((current_chunk[0]+x, current_chunk[1]+y))
        

        return locations
    

    

    def draw_background(self, surface: p.Surface, visible_area: FloatRect, offset = p.Vector2(0, 0), alpha = 255) -> None:
        "Draws the background tiles of loaded chunks."
        for chunk in self.loaded_chunks.values():
            if visible_area.colliderect(chunk.rect):
                chunk.draw_background(surface, visible_area, offset, alpha)



    def draw_middleground(self, surface: p.Surface, visible_area: FloatRect, offset = p.Vector2(0, 0), alpha = 255) -> None:
        "Draws the middle-ground tiles of loaded chunks."
        for chunk in self.loaded_chunks.values():
            if visible_area.colliderect(chunk.rect):
                chunk.draw_midground(surface, visible_area, offset, alpha)


    def draw_foreground(self, surface: p.Surface, visible_area: FloatRect, offset = p.Vector2(0, 0), alpha = 255) -> None:
        "Draws theforeground tiles of loaded chunks."
        for chunk in self.loaded_chunks.values():
            if visible_area.colliderect(chunk.rect):
                chunk.draw_foreground(surface, visible_area, offset, alpha)



    def break_tile(self, chunk_pos: tuple[int, int], tile_pos: tuple[int, int], break_surroundings=False) -> None:
        """
        Breaks a tile in the middle ground at the position specified, if it's breakable property is set to True.
        The 'force' argument ensures the tile is broken regardless of the property.
        """

        try:
            chunk = self.loaded_chunks[chunk_pos]
            
            for tile in chunk.midground_tiles:
                if tile.breakable and (tile.x, tile.y) == tile_pos:
                    chunk.midground_tiles.remove(tile)
                    self._broken_tiles.setdefault(chunk_pos, set())
                    self._broken_tiles[chunk_pos].add(tile_pos)
                    if break_surroundings:
                        neighbours = [
                            (-1, 0), (1, 0), (0, -1), (0, 1)
                        ]

                        for n in neighbours:
                            self.break_tile(chunk_pos, tuple(p.Vector2(tile_pos)+n), True)
                    
                    return None
                        
        
        except KeyError:
            raise ValueError(f"No chunk exists at tile position {tile_pos} or the chunk is unloaded.")
        


    def add_tile(self, chunk_pos: Coordinate, tile_pos: Coordinate, code: str) -> None:
        "Adds a tile to the middle ground."

        if (chunk := self.loaded_chunks.get(tuple(chunk_pos))) is not None:
            chunk.add_tile(*tile_pos, code)
        
        elif (chunk_tile_codes := self.raw_chunks.get(tuple(chunk_pos))) is not None:
            if chunk_tile_codes['M'] is None:
                chunk_tile_codes['M'] = ['0' for _ in range(Chunk.TILES_PER_SIDE**2)]

            chunk_tile_codes['M'][tile_coordinates_to_index(*tile_pos)] = code

        else:
            raise ValueError(f"Cannot place tile in chunk that does not exist {chunk_pos}")
        
        


    
    def refresh(self) -> None:
        "Reloads all chunks."
        self.loaded_chunks.clear()







def index_to_tile_coordinates(index: int) -> tuple[int, int]:
    """
    Convert a tile index of a tile code from a raw chunk to tile coordinates
    that can be used in the Chunk object.
    """
    return index%Chunk.TILES_PER_SIDE, index//Chunk.TILES_PER_SIDE




def tile_coordinates_to_index(x: int, y: int) -> int:
    """
    Converts the tile coordinates of tile in the Chunk object into a tile index
    used in raw chunks.
    """
    return int(x + y*Chunk.TILES_PER_SIDE)