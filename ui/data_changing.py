"Contains UI elements that are mainly used to control user settings."

import pygame as p

from . import FONT_SIZE, COLOR_PALETTE, elongate_ui_texture, blit_to_surface, transparent_surface
from .elements import UIElement
from .buttons import Button

from audio import SoundFX

from file_processing import assets
from custom_types.gameplay import Timer
from math_functions import clamp





class Slider(UIElement):
    "Allows the player to set a value for a setting by moving the slider head across."

    size = (18, 24)

    loaded_texture: p.Surface
    unloaded_texture: p.Surface
    knob_texture: p.Surface
    text_color = COLOR_PALETTE[0]

    slide_delay = 0.05
    slide_sound = "slider_scroll"



    def __init__(
            self,
            x: int, y: int,
            text: str, text_color=(250, 255, 255),
            length=80,
            min_value=0, max_value=10, current_value=0,
            step=1
        ) -> None:
        self.text = (text, (x, y), text_color)
        self.min = int(min_value)
        self.max =  int(max_value)
        self.step = step
        self.current_value = clamp(int(current_value), self.min, self.max)

        self.loaded_bar = elongate_ui_texture(self.loaded_texture, length)
        self.unloaded_bar = elongate_ui_texture(self.unloaded_texture, length)

        self.slide_delay = Timer(type(self).slide_delay)

        self.mouse_dragging = False

        
        super().__init__(x, y, (length, self.size[1]))


    
    @property
    def slide_amount(self) -> float:
        """
        Returns how much the slider is moved as a float from 0.0 to 1.0.

        0.0 - All the way to the left
        
        1.0 - All the way to the right
        """

        return float(clamp((self.current_value - self.min)/(self.max - self.min), 0, 1))
    

    @slide_amount.setter
    def slide_amount(self, value: float) -> None:
        value = (clamp(value, 0, 1)*(self.max - self.min) + self.step/2)//self.step
        self.current_value = int(value*self.step) + self.min
    

    @property
    def selection_rect(self) -> p.Rect:
        return p.Rect(*self.__get_knob_position(), *self.knob_texture.get_size())
        


    @property
    def text_padding(self) -> p.Vector2:
        return p.Vector2(0, 10)



    def WASD_userinput(self, action_keys, hold_keys) -> UIElement | None:
        if not self.mouse_dragging:
            if self.slide_delay.complete:
                if self.is_key_pressed(action_keys, hold_keys, p.K_d) and self.current_value != self.max:
                    self.current_value = min(self.max, self.current_value + self.step*int(hold_keys[p.K_d]*2+1))
                    self.slide_delay.start()
                    SoundFX.play(self.slide_sound)
                if self.is_key_pressed(action_keys, hold_keys, p.K_a) and self.current_value != self.min:
                    if self.current_value%self.step:
                        self.current_value -= self.current_value%self.step
                    else:
                        self.current_value = max(self.min, self.current_value - self.step*int(hold_keys[p.K_a]*2+1))
                    self.slide_delay.start()
                    SoundFX.play(self.slide_sound)
            

        
        if self.is_key_pressed(action_keys, hold_keys, p.K_w):
            return self.up
        if self.is_key_pressed(action_keys, hold_keys, p.K_s):
            return self.down
    


    def mouse_userinput(self, action_keys, hold_keys, mouse_pos) -> None:
        if not self.mouse_dragging:
            if self.rect.collidepoint(mouse_pos) and action_keys["mouse_left"]:
                self.mouse_dragging = True
        
        elif hold_keys["mouse_left"]:
            c_width = self.knob_texture.get_width()
            self.slide_amount = (mouse_pos.x - self.rect.x - c_width/2)/(self.rect.width - c_width)
        
        else:
            self.mouse_dragging = False

    


    def update(self, delta_time) -> None:
        super().update(delta_time)
        self.slide_delay.update(delta_time)



    def draw(self, surface, offset = (0, 0)) -> None:
        offset = p.Vector2(offset)
        surface.blit(self.small_font.render(f"{self.text[0]}: {self.current_value}", False, self.text_color), self.rect.topleft+offset)

        surface.blit(self.unloaded_bar, self.rect.topleft+offset+(0, 10))
        if self.slide_amount != 0:
            loaded_amount = self.loaded_bar.subsurface(0, 0, int(self.loaded_bar.get_width()*self.slide_amount), self.loaded_bar.get_height())
            surface.blit(loaded_amount, self.rect.topleft+self.text_padding+offset)
        
        surface.blit(self.knob_texture, self.__get_knob_position()+offset)



    

    def __get_knob_position(self) -> p.Vector2:
        "Returns the position of the knob of the slider."

        x_offset = (self.loaded_bar.get_width() - self.knob_texture.get_width())*self.slide_amount
        y_offset = -2

        return self.rect.topleft + p.Vector2(x_offset, y_offset) + self.text_padding
    






class Toggle(UIElement):
    "Allows the player to toggle a setting between a True or False state."

    min_text_padding = 52
    size = (min_text_padding+18, 15)

    toggle_on_texture: p.Surface
    toggle_off_texture: p.Surface
    knob_texture: p.Surface
    text_color = COLOR_PALETTE[0]

    toggle_delay = 0.1
    toggle_sound = "button_click"




    def __init__(self, x: int, y: int, text: str, start_value: bool = False) -> None:
        self.text_surface = self.small_font.render(text, False, self.text_color)

        self.on = start_value

        self.toggle_delay = Timer(type(self).toggle_delay)
        
        super().__init__(x, y, (self.size[0]+self.text_padding.x-self.min_text_padding, self.size[1]))


    @property
    def selection_rect(self) -> p.Rect:
        return p.Rect(*(self.rect.topleft + self.text_padding), self.toggle_on_texture.get_width(), self.toggle_on_texture.get_height()+2)


    @property
    def text_padding(self) -> p.Vector2:
        return p.Vector2(max(self.text_surface.get_width()+5, self.min_text_padding), 0)
    


    def toggle(self) -> None:
        "Toggles the toggle."

        self.on = not self.on
        self.toggle_delay.start()
        SoundFX.play(self.toggle_sound)


    

    def WASD_userinput(self, action_keys, hold_keys) -> UIElement | None:
        if action_keys[p.K_RETURN]:
            self.toggle()
            
        return super().WASD_userinput(action_keys, hold_keys)
    

    def mouse_userinput(self, action_keys, hold_keys, mouse_pos) -> None:
        if self.selection_rect.collidepoint(mouse_pos) and action_keys["mouse_left"]:
            self.toggle()

    
    def update(self, delta_time) -> None:
        super().update(delta_time)
        self.toggle_delay.update(delta_time)
    


    def draw(self, surface: p.Surface, offset = (0, 0)) -> None:
        offset = p.Vector2(offset)
        surface.blit(self.text_surface, self.rect.topleft + offset)

        if self.on:
            surface.blit(self.toggle_on_texture, (self.rect.left, self.rect.top + 1) + self.text_padding + p.Vector2(offset))
        else:
            surface.blit(self.toggle_off_texture, (self.rect.left, self.rect.top + 1) + self.text_padding + p.Vector2(offset))
        
        surface.blit(self.knob_texture, self.__get_knob_position() + p.Vector2(offset))


    
    def __get_knob_position(self) -> p.Vector2:
        "Returns the position of the knob of the toggle."

        move_amount = self.toggle_delay.countdown/self.toggle_delay.duration

        if self.on:
            move_amount = 1-move_amount

        x_offset = (self.toggle_on_texture.get_width() - self.knob_texture.get_width())*move_amount
        # print(x_offset)
        # x_offset = ((x_offset)//UI_SCALE_VALUE)*UI_SCALE_VALUE
        # print(x_offset)
        
        return p.Vector2(self.rect.left + x_offset, self.rect.top) + self.text_padding
    








class KeyBinder(Button):
    min_text_padding = 55
    block_size = (60, 15)
    size = (min_text_padding+block_size[0], block_size[1])

    unclicked_texture: p.Surface
    clicked_texture: p.Surface
    _text_color = COLOR_PALETTE[0]

    _invalid_key_names = [
        "escape"
    ]

    set_key_sound = "slider_scroll"

    def __init__(self, x, y, action_name: str, starting_key: int | str) -> None:
        self._text_font = assets.SystemFont(FONT_SIZE)

        self._text_surface = self._text_font.render(self.__format_action_name(action_name), False, self._text_color)
        self.key = starting_key
        self._check_for_key = False
        self._surface_to_blit = transparent_surface(self.size)

        self._block_unclicked = elongate_ui_texture(self.unclicked_texture, self.block_size[0])
        self._block_clicked = elongate_ui_texture(self.clicked_texture, self.block_size[0])


        super().__init__(x, y, self.size, (None, None), self._start_checking)


    @property
    def selection_rect(self) -> p.Rect:
        return p.Rect(self.rect.x+self.min_text_padding, self.rect.y, *self.block_size)
    

    def _start_checking(self) -> None:
        self._check_for_key = True

    
    def mouse_userinput(self, action_keys, hold_keys, mouse_pos) -> None: pass


    def WASD_userinput(self, action_keys, hold_keys) -> UIElement | None:
        if self._check_for_key:
            if action_keys["any"]:
                for key, pressed in action_keys.items():
                    if key != "any" and pressed and self.__is_key_valid(key):
                        self.key = key
                        SoundFX.play(self.set_key_sound)
                        break
                
                self._check_for_key = False
        else:
            return super().WASD_userinput(action_keys, hold_keys)
    


    def __is_key_valid(self, key: int | str) -> bool:
        "Returns True if the key can be used as a keybind."

        if isinstance(key, int):
            key_name = p.key.name(key)
        else:
            key_name = key

        
        return key_name not in self._invalid_key_names

        
        

    
    def __key_display_name(self, key: int | str) -> str:
        "Returns the display name for a perticular key."

        if isinstance(key, int):
            return p.key.name(key).upper()
        else:
            return key.replace('_', ' ').upper()

        

    def __format_action_name(self, action_name: str) -> str:
        """
        Takes the variable name for a keybind and converts it into a display
        name by capitalising the first letter and replacing all the underscores
        with spaces.
        """

        display_name = f"{action_name[0].upper()}{action_name[1:]}"

        return display_name.replace('_', ' ')

        

    def draw(self, surface: p.Surface, offset = (0, 0)) -> None:
        self._surface_to_blit.fill(assets.COLOR_KEY)

        if self._check_for_key:
            block_text = "Press a Key"
        else:
            block_text = self.__key_display_name(self.key)

        if self.clicked:
            block_to_blit = self._block_clicked.copy()
            key_text_pos = (5, 4)
        else:
            block_to_blit = self._block_unclicked.copy()
            key_text_pos = (5, 2)

        blit_to_surface(self._text_surface, self._surface_to_blit, "left")

        blit_to_surface(self._text_font.render(block_text, False, self._text_color), block_to_blit, key_text_pos)
        blit_to_surface(block_to_blit, self._surface_to_blit, "right")

        surface.blit(self._surface_to_blit, self.rect.topleft)