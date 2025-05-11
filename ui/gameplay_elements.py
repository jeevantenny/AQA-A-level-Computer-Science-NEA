"Contains UI elements that will be shown in gameplay menus."

import pygame as p
from typing import Callable

from . import COLOR_PALETTE, format_text, blit_to_surface
from .elements import UIElement
from .buttons import Button

from custom_types.gameplay import Coordinate



# This class is unused
class WeaponSelector(UIElement):
    "Allows the player to select a weapon by scrolling through available options."

    size = (26, 46)
    _selection_rect_size = (26, 28)

    square_texture: p.Surface
    column_texture: p.Surface

    def __init__(self, x: int, y: int):
        super().__init__(x, y, self.size)
        self.surface_to_blit = p.Surface(self.size)
        self.surface_to_blit.set_colorkey("white")


    @property
    def selection_rect(self) -> p.Rect:
        rect = p.Rect(0, 0, *self._selection_rect_size)
        rect.center = self.rect.center
        return rect
    

    def draw(self, surface, offset=(0, 0)) -> None:
        self.surface_to_blit.fill("white")
        blit_to_surface(self.column_texture, self.surface_to_blit, "top")
        blit_to_surface(self.square_texture, self.surface_to_blit, "left")

        surface.blit(self.surface_to_blit, self.rect.topleft+p.Vector2(offset))









class ShipPowerTankIndicator(UIElement):
    "Shows the player how many powertanks the ship has."

    size = (28, 62)
    column_height = 10
    max_amount = 20
    # The maximum amount of tanks that can be displayed

    base_texture: p.Surface
    icon_texture: p.Surface
    icon_size = (12, 6)
    icon_offset = (3, 51)

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, self.size)
    

    def draw(self, surface: p.Surface, tank_amount: int, offset: Coordinate =(0, 0)) -> None:
        main_offset = p.Vector2(offset)
        surface.blit(self.base_texture, self.rect.topleft+main_offset)

        for i in range(min(tank_amount, self.max_amount)):
            x_offset = self.icon_size[0]*(i%2)
            y_offset = -self.icon_size[1]*(i//2)
            blit_pos = main_offset+self.rect.topleft+self.icon_offset+(x_offset, y_offset)

            surface.blit(self.icon_texture, blit_pos)








class PlanetInfoButton(Button):
    """
    Shows information regarding a planet that the player can travel to. Calls the ship's
    take off method when clicked.
    """

    size = (120, 42)
    base_texture: p.Surface
    full_texture_map: dict[str, p.Surface]
    text_offset = (43, 5)
    # The class will need the full spritesheet to find the icon texture for
    # a specific planet.

    def __init__(self, x: int, y: int, planet_name: str, tanks_needed: int, ship_take_off_callback: Callable[[str], None], activated=True) -> None:
        self._current_texture = self.base_texture.copy()
        planet_texture = self.full_texture_map[f"{planet_name}_icon"]
        self._current_texture.blit(planet_texture, (5, 3))

        from states.gameplay_menus import RegionMap
        planet_display_name = RegionMap.map_data[planet_name]["map_title"]

        title_surface = format_text(
            f"Planer {planet_display_name}\nPower tanks needed:\n{tanks_needed}",
            self.small_font,
            100,
            2,
            COLOR_PALETTE[3]
        )

        self._current_texture.blit(title_surface, self.text_offset)

        super().__init__(x, y, self.size, (self.base_texture, self.base_texture), lambda: ship_take_off_callback(planet_name), activated)


    def draw(self, surface, offset=(0, 0)) -> None:
        surface.blit(self._current_texture, self.rect.topleft+p.Vector2(offset))