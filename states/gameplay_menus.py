"""
This module contains states for menus that will be shown during gameplay such as when the game is
paused, the player finds a new item or opens the map.
"""

import pygame as p
from typing import Callable

from .state import State
from .menus import Menu, PopUpMenu, ConfirmationPopUp, TitleScreen, Settings, PopUpMenu
from .transitions import Fade
from .gameplay_effects import SlowMotion
from .gameplay import Play

from game_objects.player import Player
from game_objects import items, ship

from file_processing import assets

from ui import UI_SCALE_VALUE, FONT_SIZE, COLOR_PALETTE, buttons, elements, gameplay_elements, gameplay_elements, render_heading
from audio import Music, SoundFX
from settings import keybinds, video

from custom_types.gameplay import Timer
from custom_types.file_representation import SaveFile

from math_functions import clamp, range_percent



class PauseMenu(Menu):
    "This menu is displayed when the player paused the game."

    show_background = False
    heading = "Game Paused"
    heading_padding = (10, 15)

    enter_duration = 0.25
    exit_duration = 0.25
    dim_opacity = 100

    enter_sound = "slider_scroll"

    def __init__(self) -> None:
        super().__init__((100, 200))

        self.text = assets.SystemFont(16).render("Game Paused", True, (0, 255, 0))
        self.heading_surface = render_heading(self.heading, 2)

        self.button_matrix = self.__get_element_matrix()

        self.exit_gameplay = False


    def add_to_stack(self) -> None:
        Music.pause()
        SoundFX.play(self.enter_sound)
        return super().add_to_stack()



    def __get_element_matrix(self) -> elements.ElementMatrix:
        "Gets the element matrix for the pause menu."


        main_menu = lambda: self.state_stack.reset(TitleScreen(), transition=Fade(2.5))
        main_menu_popup = lambda: ConfirmationPopUp("Save and Quit?", main_menu, "Are you sure you want to save and quit?").add_to_stack()


        return elements.ElementMatrix(
            [
                buttons.LongButton(self.heading_padding[0], 40, "Close", self._close_menu),
                buttons.LongButton(0, 0, "Settings", lambda: Settings().add_to_stack()),
                buttons.LongButton(0, 0, "Main Menu", main_menu_popup),
            ]
        )
    



    def _close_menu(self) -> None:
        """
        This will be used by the buttons to control weather the game should return
        to main menu.
        """

        self.state_stack.pop()
        SoundFX.play(self.enter_sound)
        # Plays the exit sound (which is the same as the entrance sound)

        


    def userinput(self, action_keys: dict[int, bool], hold_keys: dict[int, bool]) -> None:
        if action_keys[p.K_ESCAPE]: # Press Escape to close menu
            self._close_menu()
        else:
            self.button_matrix.userinput(action_keys, hold_keys, p.Vector2(p.mouse.get_pos())/UI_SCALE_VALUE)

    

    def update(self, delta_time: float) -> None:
        self.button_matrix.update(delta_time)



    def draw(self, surface: p.Surface) -> None:
        super().draw(surface)

        self.prev_state.draw(surface)
        self.dim_surface(surface, self.dim_opacity)
         # Show gameplay behind menu but make it slightly darker

        self.ui_grid.blit(self.heading_surface, self.heading_padding)
        self.button_matrix.draw(self.ui_grid)
        self.blit_ui_grid(surface)
        # Draw the Heading text and buttons






    def draw_on_enter(self, surface: p.Surface, transition_amount: float) -> None:
        super().draw_on_enter(surface, transition_amount)

        self.prev_state.draw(surface)
        self.dim_surface(surface, self.dim_opacity*transition_amount)
        # Change how much the gameplay is darkened depending on the transition amount

        self.ui_grid.blit(self.heading_surface, self.heading_padding)
        self.button_matrix.draw(self.ui_grid)
        
        move_amount = (1-transition_amount)**3
        self.blit_ui_grid(surface, (-300*move_amount, 0))
        # Offset the ui grid to move in from the side when the game is paused


    
    def draw_on_exit(self, surface: p.Surface, transition_amount: float) -> None:
        self.draw_on_enter(surface, 1-transition_amount)
        # Same as draw_on_enter but in reverse



    

    def quit(self) -> None:
        if self.exit_gameplay:
            self.state_stack.reset(TitleScreen(), transition=Fade(1))
        
        Music.resume()
        if self.exit_gameplay:
            Music.stop()


            




class ItemMenu(PopUpMenu):
    "Shows the information for an item the player collects."

    show_background = False

    item_desc: dict[str, dict[str, str]]

    enter_duration = 0.7
    exit_duration = 0.2

    def __init__(self, collectable: items.Collectable) -> None:

        self.collectable = collectable
        item_class = self.collectable.collect_item

        try:
            item_name = self.item_desc[item_class.__name__]["name"]
        
        except KeyError:
            item_name = item_class.__name__
        
        try:
            item_desc = self.item_desc[item_class.__name__]["desc"]
        except KeyError:
            item_desc = "No description"

        super().__init__(item_name, item_desc)


    def update_on_enter(self, delta_time, transition_amount) -> None:
        super().update_on_enter(delta_time, transition_amount)

        if transition_amount <= 0.6:
            self.collectable.update(delta_time)
            # Plays the animation for the collectable being collected


    
    def draw_on_enter(self, surface, transition_amount) -> None:
        menu_open_amount = range_percent(transition_amount, 0.71, 1)

        if menu_open_amount != 0:
            super().draw_on_enter(surface, menu_open_amount)
        else:
            self.prev_state.draw(surface)
        # Waits for the collectable animation to finish before playing
        # the regular pop up entrance animation

    
    def draw_on_exit(self, surface, transition_amount) -> None:
        super().draw_on_enter(surface, 1-transition_amount)
        # Same as draw_on_enter but in reverse and without the waiting for the item animation







class ShipNavigationMenu(PopUpMenu):
    "Shows the player what planets they can visit and allows them to save progress at the spaceship's checkpoint."

    show_background = False

    size = (300, 200)
    window_texture: p.Surface

    _planet_button_position = (100, 20)
    _planet_button_size = (30, 30)

    prev_state: Play

    def __init__(self, ship_entity: ship.ShipEntity, player_powertanks: set[tuple[int, str]], current_planet: str) -> None:
        super().__init__("Navigation Control", "Choose a planet to travel to.", "Press ESCAPE to close", size=self.size)

        self._ship = ship_entity
        self._player_powertanks = player_powertanks
        self._current_planet = current_planet

        self._powertank_indicator = gameplay_elements.ShipPowerTankIndicator(40, 100)

        can_add_tanks = len(self._player_powertanks) != 0
        # The Add tanks button should only be activated if the player collected new powertanks


        button_2Dlist: list[list[buttons.Button]] = []

        button_2Dlist.append(
            [
                buttons.LongButton(20, 70, "Add Tanks", self.add_tanks_to_ship, can_add_tanks)
            ]
        )

        button_2Dlist.append([])

        not_enough_tanks_pop_up = lambda x: PopUpMenu(
                "Not Enough Power Tanks",
                "Collect Power tanks and add them to the ship to explore new planets.",
                size=(220, 80)
            ).add_to_stack()

        for planet_name, site_data in ship.ShipEntity.landing_sites["sites"].items():
            if planet_name != self._current_planet:
                planet_texture = assets.load_texture(site_data["planet_texture"])
                planet_texture = p.transform.scale(planet_texture, self._planet_button_size)

                planet_distance: int = ship.ShipEntity.landing_sites["distances"][self._current_planet][planet_name]

                if len(self._ship._powertanks) >= planet_distance:
                    execute_on_click = self.ship_take_off
                else:
                    execute_on_click = not_enough_tanks_pop_up
                
                button_2Dlist[-1].append(
                    gameplay_elements.PlanetInfoButton(
                        *self._planet_button_position,
                        planet_name,
                        planet_distance,
                        execute_on_click
                    )
                )
        
        


        self._buttons = elements.ElementMatrix(*button_2Dlist)


    def ship_take_off(self, planet_name: str) -> None:
        self._ship.take_off(planet_name)
        self.state_stack.pop()

    
    def add_tanks_to_ship(self) -> None:
        """
        Adds the Power tanks the player has collected to the ship. It then
        refreshed the state to to update the functionality of the buttons.
        """

        self._ship.get_tanks_from_player()
        self.__init__(self._ship, self._player_powertanks, self._current_planet)




    def userinput(self, action_keys, hold_keys) -> None:
        if action_keys[p.K_ESCAPE]:
            self.state_stack.pop()
        
        if action_keys[p.K_h]:
            self.ship_take_off("arenis")
            
            
        self._buttons.userinput(action_keys, hold_keys, self._get_mouse_pos())



    def update(self, delta_time) -> None:
        self._buttons.update(delta_time)




    def _blit_to_ui_grid(self) -> None:
        self._powertank_indicator.draw(self.ui_grid, len(self._ship._powertanks))
        self._buttons.draw(self.ui_grid)









class RegionMap(Menu):
    "Displays the map of the current region the player is in."

    show_background = False

    map_size = (150, 100)
    border_texture: p.Surface
    border_width = 8
    ship_icon: p.Surface
    map_data: dict[str, str]

    prev_state_dim_amount = 100

    player_marker: p.Surface

    scroll_speed = 10
    scroll_delay = 0.04
    scroll_sound = "slider_scroll"

    enter_duration = 0.2
    exit_duration = 0.2

    def __init__(self, map_name: str, player_pos: p.Vector2, map_offset: p.Vector2):
        super().__init__(self.map_size)

        self.player_pos = p.Vector2(player_pos) + map_offset - p.Vector2(self.player_marker.get_size())//2
        self.player_pos.x -= 1

        try:
            self.map_texture = assets.load_texture(self.map_data[map_name]["texture"])
        except KeyError:
            raise ValueError(f"Invalid map name '{map_name}'")
        
        title_text = f"Planet {self.map_data[map_name]['map_title']}"
        self.title_surface = assets.SystemFont(FONT_SIZE*2*UI_SCALE_VALUE).render(title_text, False, "white")

        prompt_text = f"Press [ {p.key.name(keybinds.toggle_map).upper()} ] to toggle map      WASD keys to scroll"
        self.prompt_surface = assets.SystemFont(FONT_SIZE*UI_SCALE_VALUE).render(prompt_text, False, "white")
        
        self.scroll_pos = self.player_pos-p.Vector2(self.map_size)*0.5
        self.scroll_timer = Timer(self.scroll_delay)

        self.__clamp_map_scroll()


    def __scroll(self, x: int, y: int) -> None:
        "Scroll through the map."

        self.scroll_pos += (x, y)
        self.scroll_timer.start()
        SoundFX.play(self.scroll_sound)
    

    def userinput(self, action_keys, hold_keys) -> None:
        if self.scroll_timer.complete:
            if hold_keys[p.K_w]:
                self.__scroll(0, -self.scroll_speed)

            if hold_keys[p.K_s]:
                self.__scroll(0, self.scroll_speed)

            if hold_keys[p.K_a]:
                self.__scroll(-self.scroll_speed, 0)

            if hold_keys[p.K_d]:
                self.__scroll(self.scroll_speed, 0)


        if action_keys[p.K_ESCAPE] or action_keys[keybinds.toggle_map]:
            self.state_stack.pop()


        self.__clamp_map_scroll()



    def update(self, delta_time) -> None:
        self.scroll_timer.update(delta_time)



    def __map_scale_values(self, surface: p.Surface) -> int:
        "How much the map should be scaled."
        return surface.get_width()//250
    

    def __clamp_map_scroll(self) -> None:
        "Make user the player can't scroll out of the map."

        self.scroll_pos.x = clamp(self.scroll_pos.x, 0, self.map_texture.get_width()-self.map_size[0])
        self.scroll_pos.y = clamp(self.scroll_pos.y, 0, self.map_texture.get_height()-self.map_size[1])
    

    def draw(self, surface: p.Surface) -> str:
        self.prev_state.draw(surface)
        self.dim_surface(surface, self.prev_state_dim_amount)

        surface_middle = p.Vector2(surface.get_size())*0.5
        # Middle position of the window surface

        map_surface = p.Surface(self.map_size)
        map_surface.fill(COLOR_PALETTE[3])
        map_surface.blit(self.map_texture, -self.scroll_pos)
        map_surface.blit(self.player_marker, self.player_pos-self.scroll_pos)
        # Draws the map and the player marker at the correct offset

        scaled_map = p.transform.scale_by(map_surface, self.__map_scale_values(surface))
        # Scales the map

        map_border = assets.set_stretchable_texture(self.border_texture, p.Vector2(scaled_map.get_size())//UI_SCALE_VALUE, 8)
        scaled_map.blit(p.transform.scale_by(map_border, UI_SCALE_VALUE), (0, 0))
        # Adds the border to the map

        map_blit_pos = surface_middle-p.Vector2(scaled_map.get_size())*0.5
        surface.blit(scaled_map, map_blit_pos)
        # Draws the map onto the surface

        title_blit_pos = (surface_middle[0]-self.title_surface.get_width()*0.5, map_blit_pos[1]-self.title_surface.get_height()-3)
        surface.blit(self.title_surface, title_blit_pos)
        # Draws the title text

        prompt_blit_pos = (surface_middle[0]-self.prompt_surface.get_width()*0.5, map_blit_pos[1]+scaled_map.get_height()+3)
        surface.blit(self.prompt_surface, prompt_blit_pos)
        # Draws the prompt text telling the player what actions they can do.

        return f"scroll pos: {self.scroll_pos}"
        # Debug text


    def draw_on_enter(self, surface, transition_amount) -> None:
        super().draw_on_enter(surface, transition_amount)

        self.prev_state.draw(surface)
        self.dim_surface(surface, self.prev_state_dim_amount)

        surface_size = p.Vector2(self.map_size[0], int(self.map_size[1]*transition_amount**2))*self.__map_scale_values(surface)
        map_surface = p.Surface(surface_size)
        map_surface.fill(COLOR_PALETTE[3])
        blit_pos = (p.Vector2(surface.get_size())-map_surface.get_size())*0.5

        surface.blit(map_surface, blit_pos)


    def draw_on_exit(self, surface, transition_amount) -> None:
        self.draw_on_enter(surface, 1-transition_amount)





# This class is unused
class WeaponSelectState(Menu):
    "Allows the player to choose from all the the weapons they have collected."

    show_background = False

    def __init__(self) -> None:
        super().__init__((250, 250))

        self.ranged_selector = gameplay_elements.WeaponSelector(20, 20)


    def userinput(self, action_keys, hold_keys) -> None:
        if not hold_keys[keybinds.select_weapon]:
            self.state_stack.pop()


    def draw(self, surface) -> None:
        super().draw(surface)

        self.prev_state.draw(surface)
        self.dim_surface(surface, PopUpMenu.prev_state_dim_amount)

        self.ranged_selector.draw(self.ui_grid)

        self.blit_ui_grid(surface, "bottom")












    
class GameOverScreen(Menu):
    "This state is show when the player character dies. It from here the player can either try again or return to main menu."

    show_background = False

    enter_duration = 3
    prev_state: Play

    title_text = "GAME OVER"
    title_text_padding = 15

    def __init__(self) -> None:
        super().__init__((200, 100))

        self.title_surface = render_heading(self.title_text, 4)

        retry_function = lambda: self.state_stack.reset(Play.init_from_save(self.prev_state.save_file, self.prev_state.save_file_name), transition=Fade(2.5))
        # The function to call when the player want to try again

        main_menu_function = lambda: self.state_stack.reset(TitleScreen(), transition=Fade(2))
        # The function to call when the player want to return to the main menu.
        
        self.buttons = elements.ElementMatrix(
            [buttons.LongButton(34, 80, "Try Again", retry_function)],
            [buttons.LongButton(0, 0, "Main Menu", main_menu_function)]
        )


    def add_to_stack(self) -> None:
        """
        I modified this method to account for an edge case.

        If the player character happens to die during the SlowMotion gameplay effect the GameOverScreen state may be removed
        instead of the SlowMotion state. This will cause the game to be stuck in the SlowMotion state. So before this state is
        added to the stack the previous SlowMotion State is first removed.
        """

        while isinstance(self.state_stack[-1], SlowMotion):
            list.pop(self.state_stack)

        super().add_to_stack()

    

    def _get_ui_grid_offset(self) -> p.Vector2:
        return (p.display.get_window_size()-p.Vector2(self.ui_grid.get_size())*UI_SCALE_VALUE)*0.5


    
    def userinput(self, action_keys, hold_keys) -> None:
        self.buttons.userinput(action_keys, hold_keys, (p.mouse.get_pos()-self._get_ui_grid_offset())/UI_SCALE_VALUE)

    def update(self, delta_time) -> None:
        self.buttons.update(delta_time)


    def update_on_enter(self, delta_time, transition_amount) -> None:
        super().update_on_enter(delta_time, transition_amount)

        self.prev_state.update(delta_time*(1-transition_amount)*0.5)

    def draw_on_enter(self, surface: p.Surface, transition_amount: float) -> None:
        super().draw_on_enter(surface, transition_amount)
        self.prev_state.draw(surface)

        fade_amount = transition_amount**2

        menu_fade_amount = (max(0, transition_amount-0.5))*2
        menu_fade_amount = menu_fade_amount**2

        surface.fill((int(255*fade_amount),)*3, special_flags=p.BLEND_RGB_SUB)
        self.ui_grid.set_alpha(int(255*menu_fade_amount))

        self.blit_ui_grid(surface, "centre")

    
    def draw(self, surface) -> None:
        self.ui_grid.fill("black")
        
        self.buttons.draw(self.ui_grid)
        self.ui_grid.blit(self.title_surface, ((self.ui_grid.get_width()-self.title_surface.get_width())*0.5, self.title_text_padding))

        self.blit_ui_grid(surface, "centre")