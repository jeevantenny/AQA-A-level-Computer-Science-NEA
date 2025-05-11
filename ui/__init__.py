"""
UI elements are used for navigation and changing user preferences.
They can be menus, buttons, sliders, toggles or just text on the screen.

The sprites of these elements (except HUD items) are in pixel scale so
they will need to be drawn to a surface that will be scaled up afterwards.
"""

import pygame as p
from typing import Literal

from file_processing import assets
from custom_types.gameplay import Coordinate


def init() -> None:
    from .elements import UIElement
    from .hud import HudItem

    asset_data = assets.load_class_assets("ui_assets.json")
    UIElement.init_class(asset_data)
    HudItem.init_class(asset_data)
    # Applies assets to class attributes




UI_SCALE_VALUE = 3
HUD_SCALE_VALUE = UI_SCALE_VALUE*1.5
FONT_SIZE = 8

COLOR_PALETTE = (
    (250, 255, 255),
    (19, 14, 38),
    (13, 36, 135),
    (56, 67, 95),
    (105, 125, 142),
    (193, 215, 219)
)


def elongate_ui_texture(texture: p.Surface, width: int, edge=3) -> p.Surface:
    """
    Increases the width of the texture by a certain amount. The texture is split into
    3 parts (left part, middle part and right part).
    
    To create the final texture a the middle part is blitted multiple times onto a surface
    to fill it. This filled surface is blitted onto the middle of the final surface. Then
    the left and right parts are blitted onto the left and right sides of this texture.
    This texture is then returned.

    If the given width argument is smaller then the actual width or the width of the
    texture is smaller than the edge. It will return a copy of the original surface.
    """

    w, h = texture.get_size()
    if width > w > edge*2:
        middle = p.Surface((width-edge*2, h))
        middle_texture = texture.subsurface(edge, 0, w-edge*2, h)

        for i in range(width-edge*2//middle_texture.get_width() + 1):
           middle.blit(middle_texture, (middle_texture.get_width()*i, 0))
        # The middle part is blitted multiple times to fill the surface

        elongated = transparent_surface((width, h))
        
        blit_to_surface(texture.subsurface(0, 0, edge, h), elongated) # Right part is blitted
        blit_to_surface(middle, elongated, "centre") # Middle filled part is blitted
        blit_to_surface(texture.subsurface(w-edge, 0, edge, h), elongated, "right") # Right part is blitted

        return elongated
    else:
        return texture.copy()
    



def render_heading(text: str, size=3) -> p.Surface:
    """
    Creates a surface containing the title text. Two surfaces of the text with different colours is layered
    on top of one another to creat a depth effect.
    """

    heading_font = assets.SystemFont(FONT_SIZE)
    font_surface = heading_font.render(text, False, COLOR_PALETTE[2]).convert()
    font_surface.blit(heading_font.render(text, False, COLOR_PALETTE[0]).convert(), (0, -1))
    return p.transform.scale_by(font_surface, size)
    


def blit_to_surface(
        source: p.Surface,
        destination: p.Surface,
        position: Coordinate | Literal["centre", "top", "bottom", "left", "right"] = (0, 0),
        alpha=255
    ) -> None:
    """
    This functions the same as 'pygame.Surface.blit' but provides extra options for the blit
    position that anchor the source surface to a point on the destination surface.
    """

    match position:
        case "centre":
            blit_pos = (p.Vector2(destination.get_size())-source.get_size())*0.5

        case "top":
            blit_pos = (destination.get_width()-source.get_width())*0.5, 0

        case "bottom":
            blit_pos = (destination.get_width()-source.get_width())*0.5, destination.get_height()-source.get_height()

        case "left":
            blit_pos = 0, (destination.get_height()-source.get_height())*0.5

        case "right":
            blit_pos = destination.get_width()-source.get_width(), (destination.get_height()-source.get_height())*0.5

        case _:
            try:
                blit_pos = p.Vector2(position)
            
            except ValueError:
                raise ValueError(f"Invalid position argument '{position}'")
    
    surface_to_blit = source.copy()
    surface_to_blit.set_alpha(alpha)

    destination.blit(surface_to_blit, blit_pos)





def format_text(
        text: str,
        font: p.font.Font,
        text_box_width: int,
        space_width: int,
        color: p.Color,
        antialias=False
    ) -> p.Surface:
    "Takes the given text and renders them onto a surface and divides the words into seperate lines."

    word_surfaces: list[p.Surface | str] = []
    for line in text.split('\n'):
        for word in line.split():
            word_surfaces.append(
                font.render(word, antialias, color)
            )
        
        word_surfaces.append("newline")

    if not word_surfaces:
        raise ValueError("Text does not contain any words.")

    line_index = 0
    char_height = word_surfaces[0].get_height()
    cursor_x = 0

    lines: list[list[p.Surface]] = [[]]

    for word in word_surfaces:
        if word == "newline":
            line_index += 1
            lines.append([])
            cursor_x = 0
            continue
    
        if word.get_width() > text_box_width-cursor_x:
            if cursor_x == 0:
                raise ValueError("Word too large to fit on text box.")
            
            line_index += 1
            lines.append([])
            cursor_x = 0

        lines[line_index].append(word)
        cursor_x += word.get_width()+space_width
    
    text_box = p.Surface((text_box_width, len(lines)*(char_height)))
    text_box.fill("white")
    text_box.set_colorkey("white")

    for i, line in enumerate(lines):
        cursor_x = 0
        for word in line:
            text_box.blit(word, (cursor_x, i*char_height))
            cursor_x += word.get_width()+space_width
    
    return text_box







def transparent_surface(size: tuple[int, int], colorkey: p.Color = assets.COLOR_KEY) -> p.Surface:
    "Returns a surface that is already transparent with with a colorkey."

    surf = p.Surface(size)
    surf.fill(colorkey)
    surf.set_colorkey(colorkey)
    return surf