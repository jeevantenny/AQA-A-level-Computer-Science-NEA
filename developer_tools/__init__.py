import pygame as p

from game_objects.world import Chunk, index_to_tile_coordinates, AIR

from file_processing import world


def create_region_map_png(region_name: str, png_path: str):
    raw_chunks = world.load_region(region_name).raw_chunks

    chunk_x_range = None
    chunk_y_range = None

    for x, y in raw_chunks.keys():
        if chunk_x_range is None:
            chunk_x_range = [x, x]
        else:
            chunk_x_range = [min(x, chunk_x_range[0]), max(x, chunk_x_range[1])]
            
        if chunk_y_range is None:
            chunk_y_range = [y, y]
        else:
            chunk_y_range = [min(y, chunk_y_range[0]), max(y, chunk_y_range[1])]
    

    width = chunk_x_range[1]-chunk_x_range[0]+1
    height = chunk_y_range[1]-chunk_y_range[0]+1

    chunk_offset = p.Vector2(-chunk_x_range[0], -chunk_y_range[0])

    map_surface = p.Surface(p.Vector2(width, height)*Chunk.TILES_PER_SIDE)
    map_surface.fill("white")

    for chunk_pos, tile_data in raw_chunks.items():
        if tile_data.get("M") is not None:
            __add_tiles_to_image(map_surface, tile_data["M"], chunk_pos, chunk_offset)
            
        # if tile_data.get("F") is not None:
        #     __add_tiles_to_image(map_surface, tile_data["F"], chunk_pos, chunk_offset)

    p.image.save(map_surface, png_path, "PNG")




def __add_tiles_to_image(image: p.Surface, tile_codes: str, chunk_pos: tuple[int, int], chunk_offset: p.Vector2):
        for i, code in enumerate(tile_codes):
            if code != AIR:
                pixel_pos = (chunk_pos+chunk_offset)*Chunk.TILES_PER_SIDE + index_to_tile_coordinates(i)
                image.set_at((int(pixel_pos.x), int(pixel_pos.y)), "black")