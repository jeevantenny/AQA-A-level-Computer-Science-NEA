"This module contains functions used to load various types of assets from the assets folder."

import pygame as p
from typing import Callable, Any
from functools import partial

from . import load_json
from errors import AssetLinkError


# I have created constants for path to the directories that hold relevent assets.
TEXTURE_DIR = "assets/textures/"
TEXTURE_MAP_DIR = "assets/texture_maps/"
ANIM_DIR = "assets/animations/"
ANIM_CONTROLLER_DIR = "assets/animation_controllers/"

COLOR_KEY = (255, 255, 255)


SystemFont = partial(p.font.Font, "assets/fonts/Tiny5-Regular.ttf")
# The main font that is displayed in the UI

DebugFont = partial(p.font.SysFont, "Arial")
# The font that is used when displaying information for debugging







def load_texture(path: str, translucency = False, colorkey: p.Color | None = COLOR_KEY) -> p.Surface:
    """
    Loads images from the textures folder and returns it as pygame.surface.Surface.
    """
    
    try:
        texture = p.image.load(TEXTURE_DIR + path)
        if translucency:
            texture = texture.convert_alpha()
        else:
            texture = texture.convert()
            if colorkey is not None:
                texture.set_colorkey(colorkey)
    except FileNotFoundError:
        return load_texture("unknown.png")

    return texture



def set_stretchable_texture(texture: p.Surface, size: tuple[int, int], section_width=5) -> p.Surface:
    """
    Uses the texture surface provided to fill an area by of given size. This is mainly used for menu windows
    that can have a veriaty of sized and where's not feasable to create different sized textures for different
    menus.

    Somewhat similar to the rectangle tool in MS Word where the border thickness stays the same. The border
    thickness here is 'section_width'.
    """

    width = section_width*3
    texture = texture.subsurface(0, 0, width, width)
    size = (int(size[0]), int(size[1]))

    surface = p.Surface(size)
    surface.fill("white")
    surface.set_colorkey("white")


    sections = grid_texture(texture, (section_width, section_width))
    # splits the original surface into 9 sections


    for y in range((size[1]-1)//section_width):
        for x in range((size[0]-1)//section_width):
            surface.blit(sections[min(y, 1)][min(x, 1)], p.Vector2(x, y)*section_width)
            # Fills the top, left and middle parts of the final surface with the
            # correct sections
        
        surface.blit(sections[min(y, 1)][-1], (size[0]-section_width, y*section_width))
        # Fills the right part of the final surface with the right edge sections
        
    
    for x in range((size[0]-1)//section_width):
        surface.blit(sections[-1][min(x, 1)], (x*section_width, size[1]-section_width))
        # Fills the bottom part of the final surface with the bottom edge sections
    
    surface.blit(sections[-1][-1], (size[0]-section_width, size[1]-section_width))
    # Draws the bottom right section onto the bottom right of the final surface



    return surface



def load_texture_map(path: str) -> dict[str, p.Surface]:
    """
    Loads a texture map json file from the texture maps folder and returns it as a
    dictionary.
    """

    map_file = load_json(TEXTURE_MAP_DIR + path)

    spritesheet: p.Surface = load_texture(map_file["spritesheet"])
    mapping_rects: dict = map_file["mappings"]
    mappings: dict[str, p.Surface] = {}

    for name, region in mapping_rects.items():
        try:
            section = spritesheet.subsurface(*region)
            mappings[name] = section
            # Replaces the rect value for the spritesheet section with the correspoding texture

        except ValueError:
            raise ValueError(f"Invalid rect argument for '{name}'.")
            # Raise a ValueError if the rect value is outside the spritesheet
    

    return mappings





def grid_texture(texture: p.Surface, cell_size: tuple[int, int]) -> list[list[p.Surface]]:
    "Converts a surface into a grid of squares represented by a 2D list."

    texture_grid: list[list[p.Surface]] = []

    w, h = texture.get_size()

    for y in range(0, h - h%cell_size[1], cell_size[1]): # Iterates through all possible y values for each cell
        texture_grid.append([])
        for x in range(0, w - w%cell_size[0], cell_size[0]): # Iterates through all possible x values
            texture_grid[-1].append(texture.subsurface(x, y, *cell_size))
    

    return texture_grid






# lists all valid asset types and the function that will interpret the information stored in the asset link file.
# It also indicates if the result from the function can be further narrowed down by a dictionary key.
ASSET_TYPES: dict[str, Callable[[str], p.Surface|dict]] = {
    "texture": (load_texture, False),
    "texture_map": (load_texture_map, True),
    "animation": (lambda path: load_json(ANIM_DIR+path), False),
    "anim_controller": (lambda path: load_json(ANIM_CONTROLLER_DIR+path), False),
    "json": (load_json, True)
}



def load_class_assets(path: str) -> dict[str, dict[str, Any]]:
    """
    Returns a dictionary that specified all that assets that needs to assigned classes when they are
    initialized
    """

    full_path = f"assets/{path}"
    asset_link_file = load_json(full_path)

    asset_list: dict[str, dict[str, str]] = {key: {} for key in ASSET_TYPES.keys()}

    # This loads all the assets mentioned in the assets json file and stores them in asset_list which
    for asset_type, assets in asset_link_file.items():
        if asset_type != "links":
            if asset_type not in ASSET_TYPES:
                raise AssetLinkError(full_path, f"Invalid asset catagory '{asset_type}'.")
                # Raises an error if an asset type in the json file is not valid.
            
            for name, path in assets.items():
                asset_list[asset_type][name] = ASSET_TYPES[asset_type][0](path)
            
            
            

    class_links: dict[str, dict[str, Any]] = asset_link_file["links"]
            

    for class_name, link in class_links.items():
        for attribute_name, (asset_type, asset_name, *key) in link.items():
            if asset_type not in ASSET_TYPES: # If the asset type to link is not a valid one
                raise AssetLinkError(full_path, f"Invalid asset type '{asset_type}' for '{class_name}'.")
            
            if asset_name not in asset_list[asset_type]: # If there is no asset that goes by the name in the asset catagory
                raise AssetLinkError(full_path, f"Invalid asset name '{asset_name}' of type '{asset_type}' for '{class_name}'.")
            
            asset = asset_list[asset_type][asset_name]
            if key:
                if not ASSET_TYPES[asset_type][1]: # If the asset cannot be divided down further
                    raise AssetLinkError(full_path, f"Asset type '{asset_type}' is not iterable.")
                asset = asset[key[0]]

            link[attribute_name] = asset
    

    return class_links