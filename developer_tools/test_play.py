import pygame as p
from typing import Literal

from states.state import State
from states.gameplay import Play

import game_objects
from game_objects import ship
from game_objects.world import Chunk, ChunkManager
from game_objects.entities import EntityManager
from game_objects.player import Player
from game_objects.items import *

from custom_types.file_representation import TileData, WorldRegion

from file_processing import assets






class TestPlay(Play):
    def __init__(self, region: WorldRegion, tile_data: dict[str, TileData], player_pos: p.Vector2):
        State.__init__(self)

        self.region = region

        self.chunks: dict[tuple[int, int], Chunk] = {}
        self.chunk_manager = ChunkManager(self.chunks, self.region.raw_chunks, tile_data)

        self.entities = EntityManager(camerashake_callback=self.camerashake)

        game_objects.init(self.entities, self.chunks, 1)


        self.debug_font = assets.DebugFont(16)

        self.camera = None
        self.show_rects = False

        self.player = Player(*player_pos)
        self.player.acquire_item(DoubleJump, ("test", 1))
        self.player.acquire_item(WallJump, ("test", 2))
        self.player.acquire_item(GroundPound, ("test", 3))

        self._load_items()
        self._load_region_entities()

        self.death_screen_called = False

        if ship.ShipEntity.should_be_in_region(self.region.file_name):
            self._summon_ship(self.region.file_name)
        self._load_hud()





    
    def userinput(self, action_keys, hold_keys) -> None:
        if hold_keys[p.K_LCTRL] and action_keys[p.K_g]:
            self.show_rects = not self.show_rects
        
        if action_keys[p.K_ESCAPE]:
            self.state_stack.pop()
        self.player.userinput(action_keys, hold_keys)


    def _should_change_region(self) -> Literal[False]:
        return False
    


    def player_dead(self) -> None:
        self.state_stack.pop()




    def quit(self) -> None: pass