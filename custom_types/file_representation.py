"""
This module contains various classes that store information from json, binary and custom region files (which are plaintext). Most of these
classes inherit from NamedTuple but for some I need to be able to change the attributes of the class instances which NamedTuple does not
allow.
"""

import pygame as p
from typing import NamedTuple, Any

from debug import log, STATE_INFO



class TileData(NamedTuple):
    """
    Stores the properties of a single tile. This will be used during world generation
    to create Tile objects.
    """

    code: str
    name: str
    type: str
    texture: tuple[p.Surface, p.Surface]
    collision: bool
    breakable: bool
    friction: float
    wall_jump: bool
    damage_sides: dict[str, tuple[int, str]]



class EntityData(NamedTuple):
    """
    Used to save the entities into a save file. An EntityData object will store the name of the entity's class and the
    attributes required to recreate the entity again when the player continues the save file later. These attributes
    are determimed in the get_entity_data method of an entity.

    The class contains init_args which are the arguments required to initialse en entity object when recreating
    it. The changes attributes store a dictionary of attribute name and it's value when the EntityData object was
    created.
    """
    
    class_name: str
    init_args: list[Any]
    changed_attributes: dict[str, Any]


class RegionConnection(NamedTuple):
    "Stores the information for a connection between world regions."
    id: str
    enter_pos: tuple[int, int]
    rect: p.Rect
    connecting_region: str
    connection_id: str


class CameraData(NamedTuple):
    """
    Stores information regarding how to set up the Camera object for
    a perticular region.
    """
    area_size: int = 600
    boundary: p.Rect | None = None


class MapData(NamedTuple):
    """
    Stores the name of the map to show for a region along
    with the offset for the player marker compared to the
    actual player position.
    """
    map_name: str = "arenis"
    map_offset: tuple[int, int] = (0, 0)



class WorldRegion(NamedTuple):
    """
    Stores all the information obtained from a region file in a
    format that will be easy to access when generating a region.
    """
    file_name: str
    display_name: str | None
    tile_data: set[str]
    raw_chunks: dict[tuple[int, int], dict[str, list[str] | None]]
    entities: list[tuple[float, float, type[object]]]
    items: list[tuple[float, float, type[object]]]
    gravity: float
    background_color: p.Color
    camera: CameraData
    mapdata: MapData
    connections: dict[int, RegionConnection] = {}
    checkpoints: dict[int, tuple[int, int]] = {}
    music: str | None = None




class ProgressData(NamedTuple):
    """
    Stores information regarding the player's progression. It stores the region
    the player was in and what regions and planets the player has discovered.
    There are two ways to store the player's progress.

    Live Progress:
    This is when the player stops playing before getting to a checkpoint. The
    game stores the player EntityData along with any other entity in the region.
    It also stores what tiles have been broken. This is all done to ensure that
    the player can pick up where they left off from their last play session.

    Checkpoint Progress:
    This is when the player does reach a checkpoint. It stores the player's
    EntityData and the checkpoint ID. It doesn't store any other entities or
    broken tiles as these should be reset. The game should load the entities
    that are tied to the region.
    """

    region: str
    checkpoint: tuple[int, EntityData] | None
     # A checkpoint consists of the checkpoint id of the region and the entity data for the player at that checkpoint

    entities: list[EntityData] | None
    broken_tiles: dict[tuple[int, int], set[tuple[int, int]]]
    discovered_regions: list[str]
    discovered_planets: list[str]
    ship_powertanks: set[tuple[int, str]]






class SaveFile:
    """
    Stores the information for a save file. When saving progress the class instance
    is directly stored onto the biniary file using the pickle module.
    """

    def __init__(
            self,
            region_name: str,
            starting_checkpoint: tuple[int, EntityData]
        ) -> None:


        self.__progress_data: list[ProgressData] = [
            ProgressData(
                region_name,
                None,
                [],
                {},
                [region_name],
                [region_name.split("/")[0]],
                set()
            ),

            ProgressData(
                region_name,
                starting_checkpoint,
                None,
                {},
                [region_name],
                [region_name.split("/")[0]],
                set()
            )
        ]

        self.use_checkpoint = False
        self._time_played = 0.0
        # The time played is stored in seconds


    @property
    def live_progress(self) -> ProgressData:
        return self.__progress_data[0]
    
    @live_progress.setter
    def live_progress(self, value: ProgressData) -> None:
        self.__progress_data[0] = value

    @property
    def checkpoint_progress(self) -> ProgressData:
        return self.__progress_data[1]


    @property
    def current_region(self) -> str:
        return self.live_progress.region
    
    @current_region.setter
    def current_region(self, value: str) -> None:
        data = self.live_progress
        self.live_progress = ProgressData(
            value,
            None,
            data.entities,
            data.broken_tiles,
            data.discovered_regions,
            data.discovered_planets,
            data.ship_powertanks
        )
    


    @property
    def entities(self) -> list[EntityData]:
        return self.live_progress.entities
    
    @entities.setter
    def entities(self, value: list[EntityData]) -> None:
        self.__update_list(self.live_progress.entities, value)
        
    
    @property
    def last_checkpoint(self) -> tuple[int, EntityData]:
        return self.checkpoint_progress.checkpoint
    


    @property
    def broken_tiles(self) -> dict[tuple[int, int], set[tuple[int, int]]]:
        return self.live_progress.broken_tiles
    
    @broken_tiles.setter
    def broken_tiles(self, tiles: dict[tuple[int, int], set[tuple[int, int]]]) -> None:
        self.live_progress.broken_tiles.clear()
        for key, value in tiles.items():
            self.live_progress.broken_tiles[key] = value.copy()
            

    

    @property
    def dicovered_regions(self) -> list[str]:
        return self.live_progress.discovered_regions
    
    def add_new_region(self, region_name: str) -> None:
        "Adds the new region to the list of regions the player has discovered."

        if region_name not in  self.live_progress.discovered_regions:
            self.live_progress.discovered_regions.append(region_name)
            self.add_new_planet(region_name.split('/')[0])
    
    @property
    def dicovered_planets(self) -> list[str]:
        return self.live_progress.discovered_planets
    
    def add_new_planet(self, planet_name: str) -> None:
        "Adds the new planet to the list of planets the player has discovered."

        if planet_name not in  self.live_progress.discovered_planets:
            self.live_progress.discovered_planets.append(planet_name)

    @property
    def ship_powertanks(self) -> set[tuple[int, str]]:
        return self.live_progress.ship_powertanks
    @ship_powertanks.setter
    def ship_powertanks(self, tanks: set[tuple[int, str]]) -> None:
        for tank in tanks:
            self.live_progress.ship_powertanks.add(tank)
    

    @property
    def hours_played(self) -> float:
        "Returns how many hours the player has played on this save file."
        return self._time_played/(60*60)

    def increment_time_played(self, seconds: float) -> None:
        "Increments the time player in seconds."
        self._time_played += max(seconds, 0)


    

    def set_live_progress(
            self,
            region: str,
            entities: list[EntityData],
            broken_tiles: list[tuple[int, int]],
            regions: list[str],
            planets: list[str]
        ) -> None:
        "Sets the live progress for the save file."

        self.current_region = region
        self.entities = entities
        self.live_progress.broken_tiles = broken_tiles
        self.live_progress.discovered_regions = regions
        self.live_progress.discovered_planets = planets
    


    def set_checkpoint(self, id: int, player_data: EntityData) -> None:
        """
        Updates the checkpoint progress of the save file. This means that
        when the player character dies their progress will be reset to back
        this.
        """

        self.__progress_data[1] = ProgressData(
            self.current_region,
            (id, player_data),
            None,
            self.broken_tiles.copy(),
            self.dicovered_regions.copy(),
            self.dicovered_planets.copy(),
            self.ship_powertanks.copy()
        )



    def revert_to_checkpoint(self) -> None:
        """
        Reverts the live progress of the player to use the progress recorded
        at the last checkpoint.
        """

        self.live_progress = ProgressData(
                self.checkpoint_progress.region,
                None,
                [],
                {},
                self.checkpoint_progress.discovered_regions.copy(),
                self.checkpoint_progress.discovered_planets.copy(),
                self.checkpoint_progress.ship_powertanks.copy()
            )
        
        log(STATE_INFO, "Reverted progress to checkpoint")
        
        self.use_checkpoint = True
    



    def print_data(self) -> None:
        print(f"Save Data:\nuse checkpoint: {self.use_checkpoint}\nhours: {self.hours_played}\ncurrent region: {self.current_region}\ndiscovered region: {self.dicovered_regions}\ndiscovered planets: {self.dicovered_planets}\nship tanks: {self.ship_powertanks}")




    def __update_list(self, working_list: list, new_list: list) -> None:
        "Clears working_list and fills it with the values of new_list."

        working_list.clear()
        working_list.extend(new_list)