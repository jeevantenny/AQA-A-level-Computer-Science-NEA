"This module contains functions used to load certain files from the data folder."

import pygame as p
import pickle

from . import load_json
from .assets import load_texture, grid_texture

from custom_types.file_representation import TileData
from custom_types.file_representation import SaveFile

from debug import log, STATE_INFO, DEBUGGING
from errors import SaveFileError



from game_objects.world import Tile, BACKGROUND_TILE_DIM_AMOUNT


SAVE_FILE_DIR = "user_data/save_files/"
TILE_DATA_DIR = "data/tile_data/"



def load_save_data(file_name: str) -> SaveFile | None:
    """
    Loads the SaveData object stored in the finary file. If the file is empty, the function will
    return None. If a pickle.UnpicklingError occurs it means save file was corrupted and will
    raise a SaveFileError.
    """

    full_path = f"{SAVE_FILE_DIR}{file_name}.bin"
    with open(full_path, "rb") as f:
        try:
            save_data: SaveFile = pickle.load(f)

            log(STATE_INFO, f"Loaded save file: '{full_path}'")
            if DEBUGGING:
                save_data.print_data()
            
            return save_data

        except EOFError:
            return None
            # Catches the error that occurs when attempting to read from an empty file.
            # This is fine because it means the save file is empty or hasn't been played on.
        
        except pickle.UnpicklingError:
            raise SaveFileError(file_name)
            # If a pickle.UnpicklingError occurs it means thet save file got corrupted.
            # This will raise a SaveFileError which will be handled someplace else.





def save_data(save_data: SaveFile, file_name: str) -> None:
    """
    Saves the given SaveData object into a binary file using the pickle module. Raises a 
    ValueError if the given save_data is not of type SaveFile.
    """

    if not isinstance(save_data, SaveFile):
        raise ValueError("save_data is not of type SaveFile")

    full_path = f"{SAVE_FILE_DIR}{file_name}.bin"
    with open(full_path, "wb") as f:
        pickle.dump(save_data, f)
    
    log(STATE_INFO, f"Saved save file: '{full_path}'")
    if DEBUGGING:
        save_data.print_data()




def delete_save_data(file_name: str) -> None:
    "Deletes the SaveFile object stores on the file."
    
    full_path = f"{SAVE_FILE_DIR}{file_name}.bin"
    with open(full_path, "wb"): pass

    log(STATE_INFO, f"Deleted save file '{full_path}'")





def load_tile_data(name: str) -> dict[str, TileData]:
    """
    Loads the tile data from a json file and returns it as a dictionary. The dictionary contains a
    TileData object for every tile code.
    """
    
    file_path = f"{TILE_DATA_DIR}{name}.tile_data.json"
    data_file: dict[str, str | int | dict[str, dict]] = load_json(file_path)

    tile_textures = grid_texture(load_texture(data_file["spritesheet"]), (data_file["tile_size"],)*2)

    tile_data: dict[str, TileData] = {}

    background_dimming = p.Surface((Tile.SIZE, Tile.SIZE))
    background_dimming.set_alpha(BACKGROUND_TILE_DIM_AMOUNT)
    dimmed_colorkey = (255 - BACKGROUND_TILE_DIM_AMOUNT,)*3
    
    for code, data in data_file.get("tiles", {}).items():
        if "texture" not in data:
            raise AttributeError(data["name"], "texture")
            # 'texture' is a required attribute for a tile
        
        data.setdefault("properties", {})
        # Sets an 

        texture_x, texture_y = data["texture"]
        f_texture: p.Surface = p.transform.rotate(tile_textures[texture_y][texture_x], 90*data.get("texture_rotation", 0))
        # This will be the texture used when the tile is in the middleground or foreground

        b_texture = f_texture.copy()
        b_texture.blit(background_dimming, (0, 0))
        b_texture.set_colorkey(dimmed_colorkey)
        # This texture will be used when the tile is in the background

        tile_data[code] = TileData(
                            code,
                            data.get("name", "untitled"),
                            data.get("type", "full"),
                            (f_texture, b_texture),
                            data["properties"].get("collision", True),
                            data["properties"].get("breakable", False),
                            data["properties"].get("friction", 1),
                            data["properties"].get("wall_jump", True),
                            data["properties"].get("damage_sides", {})
                        )
        # Creates a TileData object for every tile code with the properties specified in the file
        # If a property isn't specified the default value is used
        
    return tile_data