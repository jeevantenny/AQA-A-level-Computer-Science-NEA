"""
This module contains files load_region and save_region functions which are used when a region
needs to be loaded.
"""

import pygame as p
from typing import Any, TextIO, Callable, Iterable, Iterator
from copy import copy
from functools import wraps

from .assets import load_texture

from game_objects.world import raw_chunk_dict, Tile
from game_objects.entities import Entity
from game_objects.items import Item

from custom_types.file_representation import WorldRegion, RegionConnection, CameraData, MapData


REGION_DIR = "data/world/regions/"



CHUNK_LEVELS = ['B', 'M', 'F']
# Corresponds to background, middle-ground and foreground

DISPLAY_NAME = "display_name"
TILE_DATA = "tile_data"
CHUNKS = "chunks"
ENTITIES = "entities"
ITEMS = "items"
GRAVITY = "gravity"
BACKGROUND = "background"
CAMERA = "camera"
MAP = "map"
CONNECTIONS = "connections"
CHECKPOINTS = "checkpoints"
MUSIC = "music"



def __default_property_values() -> None:
    "Returns a dictionary containing the default value for each region property."

    return {
        DISPLAY_NAME: None,
        TILE_DATA: set(["general"]),
        CHUNKS: {},
        ENTITIES: [],
        ITEMS: [],
        GRAVITY: 1.0,
        BACKGROUND: (190, 190, 190),
        CAMERA: CameraData(),
        MAP: MapData(),
        CONNECTIONS: {},
        CHECKPOINTS: {0: (5, 5)},
        MUSIC: None
    }


def load_region(file_name: str) -> WorldRegion:
    """
    Loads a region file and returns it as a WorldRegion object. The file name corresponds to
    a perticular file path.

    E.g. arenis/surface -> data/world/region/arenis/surface.region
    """

    property_values = __default_property_values()

    with open(f"{REGION_DIR}{file_name}.region", "r") as f:
        while True:
            line = f.readline()
            if line == "":
                return WorldRegion(file_name, *list(property_values.values()))
            
            line = line.strip()

            if line in region_properties_functions:
                property_values[line] = region_properties_functions[line][0](f, line)




def save_region(file_name: str, region: WorldRegion) -> None:
    """
    Saves the information stored in a WorldRegion object into a
    region text file. This was only used by the LevelEditor I used
    to create the levels and won't actually be called during normal
    gameplay.
    """

    with open(f"{REGION_DIR}{file_name}.region", "w") as f:
        for property_name, (_, setter_function) in region_properties_functions.items():
            if setter_function is not None:
                setter_function(region, f, property_name)
        
        return None
        









def region_property_getter(func: Callable[[str, Any], Any]):
    @wraps(func)
    def wrapper(region_file: TextIO, property_name: str):
        return_value = None
        while True:
            line = region_file.readline()

            if line == "":
                raise SyntaxError(f"Expected expression '/{property_name}' in .region file.")

            line = line.strip()

            if line == f"/{property_name}":
                if return_value is None:
                    raise Exception("No return value was recieved.")
                
                return return_value
            

            elif line != "":
                return_value = func(line, return_value)
    
    return wrapper

def region_property_setter(func: Callable[[WorldRegion], Iterator[str] | None]):
    @wraps(func)
    def wrapper(region: WorldRegion, region_file: TextIO, property_name: str):
        data_to_write = func(region)
        if data_to_write is not None:
            region_file.write(f"{property_name}\n")
            for line in data_to_write:
                region_file.write(f"{line}\n")
            region_file.write(f"/{property_name}\n\n")

    
    return wrapper


# The following functions will be used to get or set the region propertyies of a file
# Each pair of functions deals with a specific property

@region_property_getter
def __get_display_name(line: str, _) -> str:
    return line

@region_property_setter
def __set_display_name(region: WorldRegion) -> (Iterator[str] | None):
    if region.display_name is not None:
        return (region.display_name, )


@region_property_getter
def __get_tile_data(line: str, data: set[str] | None) -> set[str]:
    if data is None:
        data = set()
    
    data.add(line)
    return data

@region_property_setter
def __set_tile_data(region: WorldRegion) -> (Iterator[str] | None):
    if region.tile_data:
        return region.tile_data


@region_property_getter
def __get_raw_chunks(line: str, chunks: raw_chunk_dict | None) -> raw_chunk_dict:
    if chunks is None:
        chunks: raw_chunk_dict = {}
    
    x, y, level, tile_codes = line.split(" ")
    level = level.upper()

    if level in CHUNK_LEVELS:
        key = (int(x), int(y))
        raw_chunk = chunks.get(key, {l: None for l in CHUNK_LEVELS})
        raw_chunk[level] = list(tile_codes)

        chunks[key] = raw_chunk

    return chunks

@region_property_setter
def __set_raw_chunks(region: WorldRegion) -> (Iterator[str] | None):
    if region.raw_chunks:
        items = []
        for (x, y), raw_chunk in region.raw_chunks.items():
            for level, tile_codes in raw_chunk.items():
                if tile_codes is not None:
                    items.append(f"{x} {y} {level} "+"".join(list(tile_codes)))
        
        return items


@region_property_getter
def __get_entities(line: str, entities: list[tuple[int, int, type[Entity]]] | None) -> list[tuple[int, int, type[Entity]]]:
    if entities is None:
        entities = []
    
    x, y, entity_type_name = line.split()

    entity_class = Entity.find_class_by_name(entity_type_name)

    if entity_class is None:
        raise ValueError(f"Invalid entity type '{entity_type_name}' in region file.")

    entities.append((int(x), int(y), entity_class))

    return entities

@region_property_setter
def __set_entities(region: WorldRegion) -> (Iterator[str] | None):
    if region.entities:
        return [
            f"{x:.0f} {y:.0f} {entity_class.__name__}"
            for x, y, entity_class in region.entities
        ]

@region_property_getter
def __get_items(line: str, items: list[tuple[int, int, type[Entity]]] | None) -> list[tuple[int, int, type[Entity]]]:
    if items is None:
        items = []
    
    x, y, entity_type_name = line.split()

    entity_class = Item.find_class_by_name(entity_type_name)

    if entity_class is None:
        raise ValueError(f"Invalid entity type ('{entity_type_name}') in region file.")

    items.append((int(x), int(y), entity_class))

    return items

@region_property_setter
def __set_items(region: WorldRegion) -> (Iterator[str] | None):
    if region.items:
        return [
            f"{x:.0f} {y:.0f} {item_class.__name__}"
            for x, y, item_class in region.items
        ]

@region_property_getter
def __get_background(line: str, _) -> p.Color:
    return p.Color(*map(int, line.split(" ")))

@region_property_setter
def __set_background(region: WorldRegion) -> (Iterator[str] | None):
    if isinstance(region.background_color, p.Color):
        c = region.background_color
        return (f"{c[0]} {c[1]} {c[2]}", )

    elif isinstance(region, str):
        raise NotImplementedError


@region_property_getter
def __get_camera(line: str, camera_data: CameraData | None) -> CameraData:
    if camera_data is None:
        camera_data = CameraData()
    
    values = line.split()
    if len(values) == 1:
        return CameraData(int(values[0]), camera_data.boundary)
    elif len(values) == 4:
        return CameraData(camera_data.area_size, p.Rect(*map(Tile.SIZE.__mul__, (map(int, line.split(" "))))))
    
    else:
        raise ValueError("Invalid value type for 'camera' found in region file.")
    


@region_property_setter
def __set_camera(region: WorldRegion) -> (Iterator[str] | None):
    lines = [str(region.camera.area_size)]
    if region.camera.boundary is not None:
        lines.append(" ".join([str(v//Tile.SIZE) for v in region.camera.boundary]))

    return lines


@region_property_getter
def __get_map(line: str, map_data: MapData | None) -> MapData:
    if map_data is None:
        map_data = MapData()

    values = line.split()
    
    if len(values) == 1:
        return MapData(values[0], map_data.map_offset)
    
    elif len(values) == 2:
        return MapData(map_data.map_name, (int(values[0]), int(values[1])))
    
    else:
        raise ValueError("Invalid value type for 'map' found in region file.")
    
@region_property_setter
def __set_map(region: WorldRegion) -> (Iterator[str] | None):
    offset = region.mapdata.map_offset
    lines = [
        region.mapdata.map_name,
        f"{offset[0]} {offset[1]}"
    ]

    return lines


@region_property_getter
def __get_connections(line: str, connections: dict[str, RegionConnection] | None) -> dict[str, RegionConnection]:
    if connections is None:
        connections = {}
    
    data = line.split(" ")

    rect_values = map(Tile.SIZE.__mul__, map(int, data[3:7]))

    enter_pos = (int(data[7]), int(data[8]))
    rect = p.Rect(*rect_values)

    conn = RegionConnection(
        int(data[0]),
        enter_pos,
        rect,
        data[1],
        int(data[2])
    )

    connections[conn.id] = conn

    return connections

@region_property_setter
def __set_connections(region: WorldRegion) -> (Iterator[str] | None):
    if region.connections:
        items = []
        for conn in region.connections.values():
            values = [
                str(conn.id),
                conn.connecting_region,
                str(conn.connection_id),
                *[str(int(v/Tile.SIZE)) for v in conn.rect],
                *[str(int(v)) for v in conn.enter_pos]
            ]

            items.append(f" ".join(values))
        
        return items


@region_property_getter
def __get_checkpoints(line: str, checkpoints: dict[str, tuple[int, int]] | None) -> dict[str, tuple[int, int]]:
    if checkpoints is None:
        checkpoints = {}

    data = tuple(map(int, line.split()))

    checkpoints[data[0]] = (data[1], data[2])

    return checkpoints

@region_property_setter
def __set_checkpoints(region: WorldRegion) -> (Iterator[str] | None):
    if region.checkpoints:
        items = []
        for id, (x, y) in region.checkpoints.items():
            items.append(f"{id} {x} {y}")
        
        return items








region_properties_functions = {
    DISPLAY_NAME: (__get_display_name, __set_display_name),
    TILE_DATA: (__get_tile_data, __set_tile_data),
    CHUNKS: (__get_raw_chunks, __set_raw_chunks),
    ENTITIES: (__get_entities, __set_entities),
    ITEMS: (__get_items, __set_items),
    GRAVITY: (None, None), 
    BACKGROUND: (__get_background, __set_background),
    CAMERA: (__get_camera, __set_camera),
    MAP: (__get_map, __set_map),
    CONNECTIONS: (__get_connections, __set_connections),
    CHECKPOINTS: (__get_checkpoints, __set_checkpoints)
}
# Makes it easier to find the right function to get or set a region property
# rather than using an if statement