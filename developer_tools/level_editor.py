import pygame as p

import game_objects.ship

from .world_building_tools import *
from .test_play import TestPlay

from states.state import State

import game_objects
from game_objects import items
from game_objects.world import Tile, Chunk, ChunkManager
from game_objects.entities import EntityManager

from file_processing import assets, data, world
from custom_types.file_representation import WorldRegion, CameraData

from debug import log, STATE_INFO



class LevelEditor(State):
    """
    This state will not be shown in the final game. It is intended to be used to design the world.
    """

    ship_landing_sites = assets.load_json("data/world/ship_landing_sites.json")
    save_file = None
    # Although LevelEditor doesn't need a save file it performs unbounded method calls for TestState and
    # passes itself in as the argument. This won't work if LevelEditor doesn't have the 'save_file' attribute.

    def __init__(self, region = "test"):
        super().__init__()

        self.region_file_name = region
        self.loaded_region = world.load_region(region)

        raw_chunks = {}

        for key, tile_codes in self.loaded_region.raw_chunks.items():
            for level, codes in tile_codes.items():
                raw_chunks.setdefault(key, {})
                raw_chunks[key][level] = list(codes) if codes is not None else None

        self.background_color = self.loaded_region.background_color
        self.connections = self.loaded_region.connections

        self.tile_data = {}

        for file_name in self.loaded_region.tile_data:
            self.tile_data |= data.load_tile_data(file_name)

        self.chunk_manager = ChunkManager({}, raw_chunks, self.tile_data, 20)
        self.entities = EntityManager()

        
        self.target_pos = p.Vector2(self.loaded_region.checkpoints[0])*Tile.SIZE
        EditingTool.init_class(self.target_pos)
        game_objects.init(self.entities, self.chunk_manager.loaded_chunks)
            

        self.tools: list[EditingTool] = [
            TileEditor(raw_chunks, self.tile_data, self.refresh_chunks),
            ConnectionEditor(self.connections),
            EntityEditor(self.loaded_region.entities, self.refresh_entities)
        ]

        self.current_tool = self.tools[0]
        self.tile_editor: TileEditor = self.tools[0]


        self.__show_grid = True

        self.__debug_font = assets.DebugFont(16)

        self.refresh_entities()
    

    


    def get_region(self, entities=True, camera_data=True) -> WorldRegion:
        raw_chunks = self.tile_editor.current_version.copy()
        empty = self.tile_editor.get_filled_chunk()

        for key, tile_codes in raw_chunks.copy().items():
            for level, codes in tile_codes.items():
                if codes == empty:
                    tile_codes[level] = None
            
            if tile_codes == {"B": None, "M": None, "F": None}:
                raw_chunks.pop(key)
                log(STATE_INFO, f"Removed empty chunk at {key}")

        region_entities = []
        if entities:
            for entity in self.entities:
                if not isinstance(entity, (items.Collectable, game_objects.ship.ShipEntity)):
                    region_entities.append((*entity.get_occupying_tile(), type(entity)))
        
        return WorldRegion(
            self.loaded_region.file_name,
            self.loaded_region.display_name,
            self.loaded_region.tile_data,
            raw_chunks,
            region_entities,
            self.loaded_region.items,
            self.loaded_region.gravity,
            self.background_color,
            self.loaded_region.camera if camera_data else CameraData(),
            self.loaded_region.mapdata,
            self.connections,
            self.loaded_region.checkpoints
        )
    
    
    @property
    def mouse_pos(self) -> p.Vector2:
        return self.target_pos + p.mouse.get_pos()

    

    def userinput(self, action_keys, hold_keys):
        Entity.group = self.entities

        if hold_keys[p.K_LCTRL]:
            if action_keys[p.K_s]:
                print(f"Saved region '{self.region_file_name}'.")
                self.save_world()

            if action_keys[p.K_t]:
                self.change_tool()

            if action_keys[p.K_r]:
                self.__init__(self.region_file_name)

            if action_keys[p.K_p]:
                TestPlay(self.get_region(not hold_keys[p.K_e], not hold_keys[p.K_c]), self.tile_data, self.mouse_pos).add_to_stack()

            if action_keys[p.K_g]:
                self.__show_grid = not self.__show_grid

        else:
            if hold_keys[p.K_s]:
                self.target_pos.y += 48
            if hold_keys[p.K_w]:
                self.target_pos.y += -48
            if hold_keys[p.K_a]:
                self.target_pos.x += -48
            if hold_keys[p.K_d]:
                self.target_pos.x += 48
        
        self.current_tool.userinput(action_keys, hold_keys, self.mouse_pos)


    def update(self, delta_time):
        self.chunk_manager.update(self.target_pos)

        self.current_tool.update(delta_time)


                
    def draw(self, surface: p.Surface):
        surface.fill((200, 200, 200))
        
        visible_region = p.Rect(*self.target_pos, *surface.get_size())
        editing_level = "A" if self.current_tool is not self.tile_editor else self.tile_editor.draw_level

        if editing_level != "F":
            self.chunk_manager.draw_background(surface, visible_region, -self.target_pos)

        self.chunk_manager.draw_middleground(surface, visible_region, -self.target_pos, 100 if editing_level in ("B", "F") else 255)
        if editing_level != "B":
            self.chunk_manager.draw_foreground(surface, visible_region, -self.target_pos, 100 if editing_level == "M" else 255)

        
        if self.__show_grid:
            self.__draw_grid(surface)

        self.current_tool.draw(surface)

        for entity in self.entities:
            entity.draw(surface, -self.target_pos)



        return f"mouse_pos: {self.mouse_pos} {self.mouse_pos//Tile.SIZE}, current_tool: {self.current_tool}"
    


        
    def __draw_grid(self, surface: p.Surface):
        tx, ty = int(self.target_pos.x), int(self.target_pos.y)
        sw, sh = surface.get_size()



        for x in range(Tile.SIZE, (sw//Tile.SIZE + 1)*Tile.SIZE, Tile.SIZE):
            p.draw.line(surface, "green", (x, 0), (x, sh))
        
        
        for y in range(Tile.SIZE, (sh//Tile.SIZE + 1)*Tile.SIZE, Tile.SIZE):
            p.draw.line(surface, "green", (0, y), (sw, y))


        chunk_x_ranges = range(Chunk.SIZE - tx%Chunk.SIZE, (sw//Chunk.SIZE + 1)*Chunk.SIZE, Chunk.SIZE)
        chunk_y_ranges = range(Chunk.SIZE - ty%Chunk.SIZE, (sh//Chunk.SIZE + 1)*Chunk.SIZE, Chunk.SIZE)
        visible_chunk_x = range(tx//Chunk.SIZE+1, (tx+sw)//Chunk.SIZE+1, 1)
        visible_chunk_y = range(ty//Chunk.SIZE+1, (ty+sh)//Chunk.SIZE+1, 1)


        for x in chunk_x_ranges:
            p.draw.line(surface, "darkblue", (x, 0), (x, sh), 3)
        
        
        for y in chunk_y_ranges:
            p.draw.line(surface, "darkblue", (0, y), (sw, y), 3)
        

        for x in visible_chunk_x:
            for y in visible_chunk_y:
                surface.blit(
                    p.transform.scale_by(assets.SystemFont(8).render(f"{(x, y)}", False, "white", "black"), 2),
                    p.Vector2(x, y)*Chunk.SIZE - (tx, ty)
                )

        
        


    def change_tool(self) -> None:
        i = (self.tools.index(self.current_tool) + 1)%len(self.tools)
        self.current_tool = self.tools[i]


    def reload_editor(self) -> None:
        target_pos = self.target_pos.copy()
        self.__init__(self.region_file_name)
        self.target_pos = target_pos
                


    def refresh_chunks(self) -> None:
        self.chunk_manager.raw_chunks = self.tile_editor.current_version
        self.chunk_manager.refresh()
        self.chunk_manager.update(self.target_pos)


    def refresh_entities(self) -> None:
        self.entities.empty()

        for x, y, entity_class in self.tools[2].entity_data:
            entity_class(0, 0).snap_to_tile((x, y))
        
        for i, (x, y, item_class) in enumerate(self.loaded_region.items):
            item_class.summon_collectable((x, y), (self.region_file_name, i))



    def save_world(self):
        world.save_region(
            self.region_file_name,
            self.get_region()
        )



