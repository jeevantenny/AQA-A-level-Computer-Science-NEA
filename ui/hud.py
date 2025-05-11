"""
Contains UI elements that will be shown during gameplay. All the element sprites
are already scaled so the there is no need to scale the surface they are drawn
onto.

All the elements inherit from the base class HudItem.
"""

import pygame as p

from . import HUD_SCALE_VALUE, FONT_SIZE, COLOR_PALETTE, blit_to_surface, transparent_surface

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import Coordinate

from file_processing import assets





class HudItem(BasicGameElement):
    """
    An item that is part of the heads up display. This is shown over the gameplay and conveys important
    information to the player
    """

    @classmethod
    def init_class(cls, asset_data: dict) -> None:
        if asset_data is None:
            asset_data = assets.load_class_assets("ui_assets.json")

        cls.load_assets(asset_data)
        super().init_class()

    
    def __init__(self, x: int, y: int, size: Coordinate) -> None:
        self.rect = p.Rect(*p.Vector2(x, y)*HUD_SCALE_VALUE, *p.Vector2(size)*HUD_SCALE_VALUE)
        self._surface_to_blit = transparent_surface(size)


    def draw(self, surface) -> None:
        self._surface_to_blit.fill("white")






class HealthBar(HudItem):
    "Displays the health of the player."

    size = (59, 9)

    BLIT_OFFSETS = (
        p.Vector2(1, 1)*HUD_SCALE_VALUE,
        p.Vector2(8, 2)*HUD_SCALE_VALUE
    )

    base_texture: p.Surface
    bar_texture: p.Surface
    heart_icon_texture: p.Surface



    def __init__(self, x: int, y: int) -> None:        
        super().__init__(x, y, self.size)


    def draw(self, surface: p.Surface, offset: Coordinate = (0, 0), health_amount: float = 1.0) -> None:
        super().draw(surface)
        offset = p.Vector2(offset)

        surface.blit(
            p.transform.scale_by(self.base_texture, HUD_SCALE_VALUE),
            self.rect.topleft+offset
        )
        # Draws the base texture

        if health_amount != 0:
            surface.blit(
                p.transform.scale_by(self.heart_icon_texture, HUD_SCALE_VALUE),
                self.rect.topleft+self.BLIT_OFFSETS[0]+offset
            )
            # Draws the heart icon


            blit_bar = p.transform.scale_by(self.bar_texture, HUD_SCALE_VALUE)
            blit_bar = blit_bar.subsurface(0, 0, blit_bar.get_width()*health_amount, blit_bar.get_height())
            
            surface.blit(blit_bar, self.rect.topleft + self.BLIT_OFFSETS[1] + offset)
            # Draws a section of tge bar texture according to how much health the player has





class PowerTankIndicator(HudItem):
    "Shows how many powertanks the player currently has."

    size = (22, 9)
    tank_icon_texture: p.Surface

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y, self.size)

        self.font = assets.SystemFont(FONT_SIZE)

    
    def draw(self, surface: p.Surface, number_of_tanks: int) -> None:
        super().draw(surface)
        blit_to_surface(self.tank_icon_texture, self._surface_to_blit)
        # Tank icon

        blit_to_surface(
            self.font.render(f"{number_of_tanks}", False, COLOR_PALETTE[0]),
            self._surface_to_blit,
            "right"
        )
        # Text displaying the number of tanks collected

        surface.blit(p.transform.scale_by(self._surface_to_blit, HUD_SCALE_VALUE), self.rect.topleft)
        # Scales the surface before being drawn onto the surface





class WeaponModeIndicator(HudItem):
    "Shows the player what weapon mode they have selected."

    size = (23, 38)

    melee_on_texture: p.Surface
    melee_off_texture: p.Surface
    ranged_on_texture: p.Surface
    ranged_off_texture: p.Surface

    def __init__(self) -> None:
        super().__init__(0, 0, self.size)


    def draw(self, surface: p.Surface, weapon_mode: int) -> None:
        super().draw(surface)

        if weapon_mode == 0: # Melee Weapon mode
            self._surface_to_blit.blit(self.melee_on_texture, (0, 0))
            self._surface_to_blit.blit(self.ranged_off_texture, (0, self.size[1]*0.5))
            # Draws the melee widget as on and the ranged widget as off.

        if weapon_mode == 1: # Ranged weapon mode
            self._surface_to_blit.blit(self.melee_off_texture, (0, 0))
            self._surface_to_blit.blit(self.ranged_on_texture, (0, self.size[1]*0.5))
            # Draws the melee widget as off and the ranged widget as on.

        scaled__surface_to_blit = p.transform.scale_by(self._surface_to_blit, HUD_SCALE_VALUE)
        # Scales the surface before being drawn onto the surface

        blit_pos = (surface.get_width()-scaled__surface_to_blit.get_width(), (surface.get_height()-scaled__surface_to_blit.get_height())*0.5)
        surface.blit(scaled__surface_to_blit, blit_pos)