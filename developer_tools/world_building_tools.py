import pygame as p
from typing import Callable, Tuple
from copy import deepcopy

from game_objects import scale_game_object
from game_objects.world import Tile, Chunk, AIR, index_to_tile_coordinates, tile_coordinates_to_index
from game_objects.entities import Entity, EntityManager

from custom_types.gameplay import actions_dict, holds_dict, Timer
from custom_types.file_representation import TileData, RegionConnection


from file_processing.world import CHUNK_LEVELS


from math_functions import sign




class EditingTool:
    target_pos: p.Vector2 = None

    @classmethod
    def init_class(cls, target_pos: p.Vector2):
        cls.target_pos = target_pos


    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict, mouse_pos: p.Vector2):
        pass


    def update(self, delta_time: float):
        pass


    def draw(self, surface: p.Surface):
        pass


    def __str__(self):
        return type(self).__name__






class TileEditor(EditingTool):
    def __init__(self, raw_chunks: dict[tuple[int, int], dict[str, list]], tile_data: dict[str, TileData], refresh_callback: Callable[[], None]):
        self.version_history = [raw_chunks]
        self.current_vi = 0

        self.tile_outline = p.Rect(0, 0, Tile.SIZE, Tile.SIZE)

        self.tile_info = [(code, data.texture[0]) for code, data in tile_data.items()]
        self.code_index = 0

        self.current_change = None
        self.drawing = False
        self.draw_level = "M"

        self.tile_pallete = p.Surface((Tile.SIZE*8 + 10, Tile.SIZE*8 + 10))
        self.pallete_rect = self.tile_pallete.get_rect()
        
        self.block_select_timer = Timer(0.05)
        self.refresh_callback = refresh_callback


    @property
    def mouse_block(self):
        return
    
    @property
    def current_version(self):
        if self.current_change is not None:
            return self.current_change

        return self.version_history[self.current_vi]

    @property
    def pallete_width(self):
        return self.pallete_rect.width//Tile.SIZE
    

    @property
    def current_tile_code(self):
        return self.tile_info[self.code_index][0]
    
    
    def get_filled_chunk(self, tile_code=AIR):
        return [tile_code]*(Chunk.TILES_PER_SIDE**2)


    def userinput(self, action_keys, hold_keys, mouse_pos):
        selected_tile_pos = mouse_pos//Tile.SIZE
        self.tile_outline.topleft = selected_tile_pos*Tile.SIZE - self.target_pos

        if hold_keys[p.K_LCTRL]:
            if action_keys[p.K_z] or hold_keys[p.K_z] > 0.6:
                self.undo()
            
            if action_keys[p.K_y] or hold_keys[p.K_y] > 0.6:
                self.redo()

        else:
            if action_keys[p.K_b]:
                i = CHUNK_LEVELS.index(self.draw_level)
                self.draw_level = CHUNK_LEVELS[(i+1)%len(CHUNK_LEVELS)]



        if self.__is_arrow_pressed(action_keys, hold_keys, p.K_LEFT):
            self.code_index = (self.code_index - 1)%len(self.tile_info)
            self.block_select_timer.start()
        
        if self.__is_arrow_pressed(action_keys, hold_keys, p.K_RIGHT):
            self.code_index = (self.code_index + 1)%len(self.tile_info)
            self.block_select_timer.start()

        if self.__is_arrow_pressed(action_keys, hold_keys, p.K_UP):
            self.code_index = (self.code_index - self.pallete_width)%len(self.tile_info)
            self.block_select_timer.start()

        if self.__is_arrow_pressed(action_keys, hold_keys, p.K_DOWN):
            self.code_index = (self.code_index + self.pallete_width)%len(self.tile_info)
            self.block_select_timer.start()



        if hold_keys["mouse_left"] and not self.pallete_rect.collidepoint(p.mouse.get_pos()):
            if hold_keys[p.K_LSHIFT]:
                self.flood_fill(*selected_tile_pos, self.current_tile_code)
            else:
                self.set_block(*selected_tile_pos, self.current_tile_code)
            self.drawing = True
        elif hold_keys["mouse_right"] and not self.pallete_rect.collidepoint(p.mouse.get_pos()):
            if hold_keys[p.K_LSHIFT]:
                self.flood_fill(*selected_tile_pos, AIR)
            else:
                self.set_block(*selected_tile_pos, AIR)
            self.drawing = True
        
        elif self.drawing:
            if self.current_change is not None:
                self.version_history.append(self.current_change)
                self.current_vi += 1
            self.current_change = None
            self.drawing = False



    def __is_arrow_pressed(self, action_keys: actions_dict, hold_keys: holds_dict, key: int):
        return action_keys[key] or hold_keys[key] > 0.5 and self.block_select_timer.complete

            


    def update(self, delta_time):
        self.block_select_timer.update(delta_time)



    def draw(self, surface):
        if not self.pallete_rect.collidepoint(p.mouse.get_pos()):
            p.draw.rect(surface, "red", self.tile_outline, 3)
        
        self.__draw_tile_pallete(surface)




    def __draw_tile_pallete(self, surface: p.Surface):
        self.tile_pallete.fill("darkgrey")
        for i, (_, texture) in enumerate(self.tile_info):
            blit_pos = (5, 5) + p.Vector2(i%self.pallete_width, i//self.pallete_width)*Tile.SIZE
            self.tile_pallete.blit(scale_game_object(texture), blit_pos)
            if i == self.code_index:
                p.draw.rect(self.tile_pallete, "blue", (*blit_pos, *self.tile_outline.size), 3)
        
        blit_pos = (0, surface.get_height() - self.pallete_rect.height)
        surface.blit(self.tile_pallete, blit_pos)
        self.pallete_rect.topleft = blit_pos
        p.draw.rect(surface, "black", self.pallete_rect.inflate(2, 2), 3)



    def __edit_chunk(self, x: int, y: int):
        chunk_pos = int(x//Chunk.TILES_PER_SIDE), int(y//Chunk.TILES_PER_SIDE)

        if self.current_change is None:
            self.current_change: dict[tuple[int, int], dict[str, list]] = deepcopy(self.current_version)
            for _ in range(len(self.version_history)-self.current_vi-1):
                self.version_history.pop()
        
        self.current_change.setdefault(chunk_pos, {})
        if self.current_change[chunk_pos].get(self.draw_level) is None:
            self.current_change[chunk_pos][self.draw_level] = self.get_filled_chunk()
        
        block_x = x - chunk_pos[0]*Chunk.TILES_PER_SIDE
        block_y = y - chunk_pos[1]*Chunk.TILES_PER_SIDE
        tile_index = tile_coordinates_to_index(block_x, block_y)

        tile_codes = self.current_change[chunk_pos][self.draw_level]

        return tile_codes, tile_index
            


    def set_block(self, x: int, y: int, code: str):
        tile_codes, tile_index = self.__edit_chunk(x, y)

        if tile_codes[tile_index] != code:
            tile_codes[tile_index] = code
            
            self.refresh_callback()
        


    
    def flood_fill(self, x: int, y: int, code: str):
        tile_codes, tile_index = self.__edit_chunk(x, y)

        replace_code = tile_codes[tile_index]

        if replace_code != code:
            fill_queue = [tile_index]
            max_index = Chunk.TILES_PER_SIDE**2

            while fill_queue:
                tile_index = fill_queue.pop(0)
                if 0 <= tile_index < max_index and tile_codes[tile_index] == replace_code:
                    tile_codes[tile_index] = code
                    fill_queue.extend([tile_index+1, tile_index-1, tile_index+Chunk.TILES_PER_SIDE, tile_index-Chunk.TILES_PER_SIDE])
            

            self.refresh_callback()
                





    def undo(self):
        self.current_vi = max(self.current_vi - 1, 0)
        self.refresh_callback()

    def redo(self):
        self.current_vi = min(self.current_vi + 1, len(self.version_history) - 1)
        self.refresh_callback()





class ConnectionEditor(EditingTool):
    def __init__(self, connection: dict[str, RegionConnection]):
        super().__init__()

        self.connections = connection
        self.current_selection: RegionConnection | None = None

        self.create_new: p.Rect | None = None
        self.create_new_origin = None


    
    def userinput(self, action_keys, hold_keys, mouse_pos):
        if self.current_selection is None:
            if action_keys["mouse_left"]:
                for id, conn in self.connections.items():
                    if conn.rect.collidepoint(mouse_pos):
                        self.current_selection = self.connections[id]
                        return None
                    
            if hold_keys["mouse_left"]:
                if self.create_new is None:
                    self.create_new_origin = p.Vector2(mouse_pos.x//Tile.SIZE, mouse_pos.y//Tile.SIZE)*Tile.SIZE
                    self.create_new = p.Rect(*self.create_new_origin, 0, 0)
            
                corner = self.__get_selection_corner(mouse_pos)

                if corner.x > self.create_new_origin.x: self.create_new.x = self.create_new_origin.x
                else: self.create_new.x = corner.x
                    
                if corner.y > self.create_new_origin.y: self.create_new.y = self.create_new_origin.y
                else: self.create_new.y = corner.y
                
                self.create_new.width = abs(corner.x - self.create_new_origin.x)
                self.create_new.height = abs(corner.y - self.create_new_origin.y)


            else:
                if self.create_new is not None:
                    if self.create_new.width > Tile.SIZE or self.create_new.height > Tile.SIZE:
                        i = 0
                        while True:
                            if i not in self.connections:
                                break
                            i += 1
                        

                        conn = RegionConnection(
                            i,
                            p.Vector2(float(input("start x: ")),float(input("start y: "))),
                            self.create_new,
                            input("connecting region filename: "),
                            input("connection id for that region: ")
                        )

                        self.connections.setdefault(i, conn)
                        self.current_selection = conn

                        print("Connection created")
                    
                    self.create_new = None
                    self.create_new_origin = None


        

        else:
            if action_keys[p.K_DELETE]:
                self.connections.pop(self.current_selection.id)
                self.current_selection = None

            if action_keys["mouse_left"] and not self.current_selection.rect.collidepoint(mouse_pos):
                self.current_selection = None




    def __get_selection_corner(self, mouse_pos: p.Vector2):
        corner = p.Vector2(mouse_pos.x//Tile.SIZE, mouse_pos.y//Tile.SIZE)

        corner.x += max(sign(mouse_pos.x - self.create_new_origin.x), 0)
        corner.y += max(sign(mouse_pos.y - self.create_new_origin.y), 0)

        return corner*Tile.SIZE



    def draw(self, surface):
        surface_rect = surface.get_rect()
        surface_rect.topleft = self.target_pos
        for conn in self.connections.values():
            if conn.rect.colliderect(surface_rect):
                blit_rect = conn.rect.copy()
                blit_rect.topleft -= self.target_pos
                p.draw.rect(surface, "orange", blit_rect, 2)
        

        if self.current_selection is not None:
            blit_rect = self.current_selection.rect.copy()
            blit_rect.topleft -= self.target_pos
            p.draw.rect(surface, "red", blit_rect, 4)
        
        elif self.create_new is not None:
            blit_rect = self.create_new.copy()
            blit_rect.topleft -= self.target_pos
            p.draw.rect(surface, "red", blit_rect, 4)





class EntityEditor(EditingTool):
    def __init__(self, entity_data: list[tuple[int, int, type[Entity]]], refresh_callback: Callable[[], None]):
        self.entity_data = entity_data
        self.entity_rects = [self.__get_entity_rect(entity) for entity in self.entity_data]
        self.entity_class = Entity.find_class_by_name("Stalacsprite")
        

        self.refresh_callback = refresh_callback

        self.highlight_rect: p.Rect | None = None
    

    def userinput(self, action_keys, hold_keys, mouse_pos) -> None:
        selected_tile_pos = mouse_pos//Tile.SIZE
        if action_keys[p.K_e]:
            self.__set_new_entity_class()

        
        if action_keys["mouse_left"]:
            add_entity = True
            for i, rect in enumerate(self.entity_rects):
                if rect.collidepoint(mouse_pos):
                    self.entity_data.pop(i)
                    self.entity_rects.pop(i)
                    add_entity = False
                    break
            if add_entity:
                self.entity_data.append((*selected_tile_pos, self.entity_class))
                self.entity_rects.append(self.__get_entity_rect(self.entity_data[-1]))
            
            self.refresh_callback()
        
        self.highlight_rect = self.__get_entity_rect((*(selected_tile_pos-self.target_pos//Tile.SIZE), self.entity_class))


    def __get_entity_rect(self, data: tuple[int, int, type[Entity]]) -> p.Rect:
        rect = p.Rect(0, 0, *data[2].hitbox)
        rect.centerx = (data[0]+0.5)*Tile.SIZE
        rect.bottom = (data[1]+1)*Tile.SIZE
        return rect
    
    def __set_new_entity_class(self) -> None:
        while True:
            entity_class = Entity.find_class_by_name(input("Enter entity class (e.g. 'TestEnemy')"))

            if entity_class is not None:
                self.entity_class = entity_class
                print("New entity class set.")
                break
            else:
                print(f"Invalid entity class.")
    

    
    def draw(self, surface):
        if self.highlight_rect is not None:
            p.draw.rect(surface, "red" , self.highlight_rect, 1)