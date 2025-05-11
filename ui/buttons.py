"""
This moduel contains Buttons that will help the player to navigate
the user interface.
"""

import pygame as p
from typing import Callable

from . import FONT_SIZE, COLOR_PALETTE
from .elements import UIElement

from file_processing import assets

from custom_types.gameplay import Timer
from custom_types.file_representation import SaveFile

from audio import SoundFX





class Button(UIElement):
    """
    A UI element that allows the user to click the button to perform an action. The action to perform
    can be passing in as a function that has no arguments and returns None.
    """
    click_sound = "button_click"
    execute_delay = 0.12
    # Delay between when the user presses the button and when the action is performed
    # This time is used to play a click animation

    def __init__(
            self,
            x: int,
            y: int,
            size: tuple[int, int],
            textures: tuple[p.Surface, p.Surface],
            execute_on_click: Callable[[], None] | None = None,
            activated=True
        ) -> None:


        super().__init__(x, y, size)
        self.unclicked_texture, self.clicked_texture = textures

        self.execute_delay = Timer(type(self).execute_delay, False, execute_on_click)
        self.__active = activated


    @property
    def clicked(self) -> bool:
        return not self.execute_delay.complete
    

    @property
    def active(self) -> bool:
        return self.__active
    
    def activate(self) -> None:
        self.__active = True

    def deactivate(self) -> None:
        self.__active = False


    def click(self) -> None:
        "Runs the execite functions and plays the click sound."

        self.execute_delay.start()
        SoundFX.play(self.click_sound)


    def WASD_userinput(self, action_keys, hold_keys) -> UIElement | None:
        if self.active and self.execute_delay.complete:
            if action_keys[p.K_RETURN]:
                self.click()
                
        return super().WASD_userinput(action_keys, hold_keys)
            


    def mouse_userinput(self, action_keys, hold_keys, mouse_pos) -> None:
        if self.active and self.execute_delay.complete:
            if self.rect.collidepoint(mouse_pos) and action_keys["mouse_left"]:
                self.click()

    

    def update(self, delta_time: float) -> None:
        super().update(delta_time)
        self.execute_delay.update(delta_time)

        

    def draw(self, surface: p.Surface, offset = (0, 0)) -> None:
        blit_pos = self.rect.topleft+p.Vector2(offset)
        if self.clicked or not self.__active:
            surface.blit(self.clicked_texture, blit_pos)
        
        else:
            surface.blit(self.unclicked_texture, blit_pos)
    





class LongButton(Button):
    "This style of button is commonly used throughout the game so I made a dedicated class for it."

    size = (60, 13)
    unclicked_texture: p.Surface
    clicked_texture: p.Surface
    text_color = COLOR_PALETTE[1]

    def __init__(self, x: int, y: int, text: str, execute_on_click: Callable[[], None] | None = None, activated=True) -> None:

        self.text = text
        super().__init__(x, y, self.size, (self.unclicked_texture, self.clicked_texture), execute_on_click, activated)



    
    def draw(self, surface: p.Surface, offset = (0, 0)) -> None:
        super().draw(surface, offset)

        blit_pos = self.rect.topleft+p.Vector2(3, 1)
        if self.clicked or not self.active:
            blit_pos.y += 2
        
        text_surface = assets.SystemFont(FONT_SIZE).render(self.text, False, self.text_color)
        surface.blit(text_surface, blit_pos+offset)






class PopUpButton(Button):
    "Button type used in the state ConfirmationPopUp."

    size = (24, 13)

    unclicked_texture: p.Surface
    clicked_texture: p.Surface
    text_color = COLOR_PALETTE[0]

    def __init__(self, x, y, text: str, execute_on_click = None) -> None:
        self.text = text
        super().__init__(x, y, self.size, (self.unclicked_texture, self.clicked_texture), execute_on_click)



    
    def draw(self, surface: p.Surface, offset = (0, 0)) -> None:
        super().draw(surface, offset)
        text_surface = assets.SystemFont(FONT_SIZE).render(self.text, False, self.text_color)

        text_blit_pos = p.Vector2(self.rect.topleft)+((self.size[0]-text_surface.get_width())//2, 1)

        if self.clicked:
            text_blit_pos.y += 2

        surface.blit(text_surface, text_blit_pos+offset)






class MissionLogIcon(Button):
    """
    Buttons used to show the different save files or Missions as they are
    called in game.
    """

    size = (135, 35)
    TEXTURE_AREA = (1, 56, *size)

    texture: p.Surface


    def __init__(self, x: int, y: int, title: str, save_file_name: str, play_save_callback: Callable[[str], None]) -> None:
        self.title = title

        super().__init__(x, y, self.size, (self.texture, self.texture), lambda: play_save_callback(save_file_name))
    

    def draw(self, surface, offset=(0, 0)) -> None:
        super().draw(surface, offset)

        surface.blit(
            self.large_font.render(self.title, False, (56, 67, 95)),
            p.Vector2(self.rect.topleft)+(4, 1)+offset
        )