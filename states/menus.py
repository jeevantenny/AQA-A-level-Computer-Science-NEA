"""
This module contains states that will be used to display a menu to the player.
The player can navigate to different screens using UI elements that are part
of the states.
"""

import pygame as p
from typing import Literal, Callable
from math import cos, pi

from .state import State
from .gameplay import Play
from .transitions import Fade

from ui import UI_SCALE_VALUE, FONT_SIZE, COLOR_PALETTE, blit_to_surface, format_text, render_heading, transparent_surface
from ui.elements import ElementMatrix
from ui.buttons import LongButton, PopUpButton, MissionLogIcon
from ui.data_changing import Slider, Toggle, KeyBinder

from file_processing import assets, data
from audio import Music, SoundFX

from custom_types.file_representation import SaveFile
from custom_types.gameplay import Coordinate
from math_functions import range_percent

from settings import keybinds, video, audio

from debug import log, STATE_INFO
from errors import SaveFileError


BACKGROUND_DIM_AMOUND = 150


class Menu(State):
    """
    A subclass of state that that is mainly used to show UI elements. The elements are first drawn a small surface
    called the ui_grid. It is then scaled up in size before being drawn onto the screen. This creates the pixel art
    look and avoids having to scale each UI element individually.
    """
    show_background = True

    @classmethod
    def load_assets(cls, asset_data) -> None:
        cls._background_dim_surface = p.Surface((1, 1))
        return super().load_assets(asset_data)

    def __init__(self, grid_size: Coordinate, grid_alpha=False) -> None:
        super().__init__()

        self.ui_grid = p.Surface(grid_size)

        if grid_alpha:
            self.ui_grid.convert_alpha()
        else:
            self.ui_grid.convert()
        
        self.ui_grid.set_colorkey(assets.COLOR_KEY)


    def _get_mouse_pos(self) -> p.Vector2:
        "Returns the position of the mouse relative to the pixel scale and menu offset."

        return p.Vector2(p.mouse.get_pos())//UI_SCALE_VALUE
    

    def blit_ui_grid(self, surface: p.Surface, offset: Coordinate | Literal["centre", "top", "bottom", "left", "right"] = (0, 0), alpha=255) -> None:
        """
        Scales up the ui_grid before being drawn onto the surface. The offset argument determines the position at which
        the ui_grid is drawn. Passing in 'centre' for offset will draw the grid in the middle of the surface.
        """

        scaled_ui_grid = p.transform.scale_by(self.ui_grid, UI_SCALE_VALUE)

        blit_to_surface(scaled_ui_grid, surface, offset, alpha)


    def draw(self, surface) -> None:
        self.ui_grid.fill(assets.COLOR_KEY)


    def draw_on_enter(self, surface, transition_amount) -> None:
        super().draw_on_enter(surface, transition_amount)
        self.ui_grid.fill(assets.COLOR_KEY)

    def draw_on_exit(self, surface, transition_amount) -> None:
        super().draw_on_exit(surface, transition_amount)
        self.ui_grid.fill(assets.COLOR_KEY)



    def dim_surface(self, surface: p.Surface, amount: int) -> None:
        "Darkens the surface by the amount specified. Tnis is used to darken the background when a menu is shown."

        self._background_dim_surface.set_alpha(int(amount))
        surface.blit(p.transform.scale(self._background_dim_surface, surface.get_size()), (0, 0))









class PopUpMenu(Menu):
    """
    A sublass of Menu that shows a smaller window to in te middle of the actual game window. It is used to display
    notifications to the player such as a confirmation window or an item description pop up.
    """

    window_texture: p.Surface
    title_text_padding = 15
    subtext_padding = (30, 40)
    prompt_padding = 10

    draw_prev_state = True
    prev_state_dim_amount = 100
    # This does not relate to the background state. It is how much the previous previous statd
    # should be dimmed by in a range from 0 to 255

    pop_up_sound = "menu_pop_up"

    enter_duration = 0.2
    exit_duration = 0.2

    def __init__(self, title: str, subtext: str | None = None, prompt="Press Enter to continue", size=(180, 100)):
        super().__init__(size)
        self.size = size
        self.window = assets.set_stretchable_texture(self.window_texture, self.size)
        

        title_surface = assets.SystemFont(FONT_SIZE*2).render(title, False, COLOR_PALETTE[0])
        
        self.window.blit(
            title_surface,
            ((size[0]-title_surface.get_width())//2, self.title_text_padding)
        )

        if subtext is not None:
            desc_box = format_text(subtext, assets.SystemFont(FONT_SIZE), size[0]-self.subtext_padding[0], 2,  COLOR_PALETTE[0])
            self.window.blit(
                desc_box,
                ((size[0]-desc_box.get_width())//2, self.subtext_padding[1])
            )
            
        font_surface = assets.SystemFont(FONT_SIZE).render(prompt, False, COLOR_PALETTE[3])
        self.window.blit(font_surface, ((self.size[0]-font_surface.get_width())//2, self.size[1]-self.prompt_padding-font_surface.get_height()))





    def add_to_stack(self) -> None:
        super().add_to_stack()
        SoundFX.play(self.pop_up_sound)
        # Plays an entrance sound when the state is added



    
    def _get_mouse_pos(self) -> p.Vector2:
        menu_offset = (p.display.get_window_size()-p.Vector2(self.size)*UI_SCALE_VALUE)*0.5

        return (p.mouse.get_pos()-menu_offset)/UI_SCALE_VALUE


    
    def userinput(self, action_keys, hold_keys) -> None:
        if action_keys[p.K_ESCAPE] or action_keys[p.K_RETURN] or action_keys["mouse_left"]:
            self.state_stack.pop()
        
    

    def draw(self, surface) -> None:
        super().draw(surface)
        if self.draw_prev_state:
            self.prev_state.draw(surface)

        self.dim_surface(surface, self.prev_state_dim_amount)
        self.ui_grid = self.window.copy()
        self._blit_to_ui_grid()
        self.blit_ui_grid(surface, "centre")


    def _blit_to_ui_grid(self) -> None:
        "Draw any additional elements onto the pop up."
        pass
    

    def draw_on_enter(self, surface, transition_amount) -> None:
        super().draw_on_enter(surface, transition_amount)
        if self.draw_prev_state:
            self.prev_state.draw(surface)
        
        self.dim_surface(surface, 100*transition_amount)
        self.ui_grid = assets.set_stretchable_texture(self.window_texture, (self.size[0], self.size[1]*transition_amount**2))
        self.blit_ui_grid(surface, "centre")


    def draw_on_exit(self, surface, transition_amount) -> None:
        self.draw_on_enter(surface, 1-transition_amount)





class ConfirmationPopUp(PopUpMenu):
    "A type of PopUpMenu that shows the user a prompt to confirm an action."

    size = (200, 80)

    def __init__(self, title: str, confirm_action: Callable[[], None], subtext: str | None = None) -> None:
        super().__init__(title, subtext, "", self.size)

        call_when_confirmed = lambda: (self.state_stack.pop(), confirm_action())
        # Calls the two function in the lambda one after the other
        # This ensures that the pop up menu is closed when the player presses the 'YES' button
        
        self.buttons = ElementMatrix(
            [PopUpButton(65, self.size[1]-PopUpButton.size[1]-10, "YES", call_when_confirmed)],
            [PopUpButton(0, 0, "NO", self.state_stack.pop)]
        )


    def userinput(self, action_keys, hold_keys) -> None:
        if action_keys[p.K_ESCAPE]:
            self.state_stack.pop()
        
        self.buttons.userinput(action_keys, hold_keys, self._get_mouse_pos())
        


    def update(self, delta_time) -> None:
        self.buttons.update(delta_time)

    def _blit_to_ui_grid(self) -> None:
        self.buttons.draw(self.ui_grid)








class TitleScreen(State):
    "A Menu state that shows the main Title screen of the game."

    show_background = True

    title_texture: p.Surface
    title_offset = 100

    enter_duration = 1.7

    def __init__(self) -> None:
        super().__init__()

        self.prompt_text_surface = assets.SystemFont(FONT_SIZE*UI_SCALE_VALUE).render("-- Press any button to Start --", False, COLOR_PALETTE[0])



    def add_to_stack(self) -> None:
        super().add_to_stack()
        Music.play("menu_theme")
        # Starts the main theme


    def userinput(self, action_keys: dict[int, bool], hold_keys: dict[int, bool]) -> None:
        if action_keys["any"]:
            self.state_stack.reset(MissionSelect(), transition=Fade(1))

    

    def draw(self, surface: p.Surface) -> None:
        title_surface = p.transform.scale_by(self.title_texture, UI_SCALE_VALUE)

        surface.blit(
            title_surface,
            ((surface.get_width()-title_surface.get_width())*0.5, self.title_offset)
        )
        surface.blit(
            self.prompt_text_surface,
            ((surface.get_width()-self.prompt_text_surface.get_width())*0.5, surface.get_height()-self.prompt_text_surface.get_height()-50)
        )


    
    def draw_on_enter(self, surface, transition_amount) -> None:
        super().draw_on_enter(surface, transition_amount)

        self.draw(surface)
        surface.fill((int(255*(1-transition_amount)),)*3, special_flags=p.BLEND_RGB_SUB)




class MissionSelect(Menu):
    "Shows the three save files the player can choose from to play on."

    save_file_names: dict[str, str]

    heading = "Choose a Mission Log"
    heading_padding = 15

    def __init__(self) -> None:
        super().__init__((250, 300))

        self.region_name = "cave"

        self.heading_surface = render_heading(self.heading)


        show_state_info = lambda file_name: MissionInfo(file_name).add_to_stack()
        # Function that calls the MissionInfo state for the save file the player has selected


        button_list = [
            MissionLogIcon(self.heading_padding, 50, display_name, file_name, show_state_info)

            for file_name, display_name in self.save_file_names.items()
        ]

        open_setting = lambda: Settings().add_to_stack()


        self.mission_logs = ElementMatrix(button_list, [LongButton(0, 0, "Settings", open_setting)], element_seperation=6)



    def userinput(self, action_keys, hold_keys) -> None:
        self.mission_logs.userinput(action_keys, hold_keys, self._get_mouse_pos())


    def update(self, delta_time) -> None:
        self.mission_logs.update(delta_time)

        
    


    def draw(self, surface) -> None:
        super().draw(surface)
        self.ui_grid.blit(self.heading_surface, (self.heading_padding,)*2)
        self.mission_logs.draw(self.ui_grid)

        self.blit_ui_grid(surface)







class MissionInfo(Menu):
    """
    Shows the player information regarding the current save file. In this state the player can choose to 
    play on the save file, copy the data to another file or delete the save file.
    """
    save_file_names: dict[str, str]

    heading_padding = 15
    subtext_padding = 50

    region_names: dict[str, str]

    enter_duration = 0.4
    exit_duration = 0.4


    def __init__(self, save_file_name: str) -> None:
        super().__init__((400, 300))

        self.save_file = self.__get_save_file(save_file_name)
        self.save_file_name = save_file_name

        heading_text = self.save_file_names.get(save_file_name, "Mission Log")

        # I have used a series of lambda functions to store what each button should do when clicked.

        if self.save_file is None:
            create_play_state = lambda: Play.init_for_new_save(save_file_name)
            subtext = "New Mission"
        elif self.save_file is SaveFileError:
            subtext = "Save File Corrupted"
        else:
            create_play_state = lambda: Play.init_from_save(self.save_file, save_file_name)
            time_played = self.__get_hour_reading(self.save_file.hours_played)
            current_region = self.region_names.get(self.save_file.current_region, self.save_file.current_region)
            subtext = f"Hours Played: {time_played}\n\nCurrent Region:\n{current_region}"
        # Sets an appropriate message to subtext depending on weather the save file has been played on before
        # Sets an appropriate function to create_play_state to either continue a save file or start on a new one.


        if self.save_file is not SaveFileError:
            play_save_file = lambda: self.state_stack.reset(create_play_state(), transition=Fade(3))
            # The function that will call the play state to allows the player to play on the save file.

            play_confirm_window = lambda: ConfirmationPopUp(f"Play {heading_text}?", play_save_file).add_to_stack()
            # The function that will call a confirmation window asking weather the player wants to start playing.
        else:
            save_corrupted_message = f"The save file appears to be corrupted. You won't be able to play on it at the moment. You could delete the save file and start a new one."
            play_confirm_window = lambda: PopUpMenu("Save File Corrupted", save_corrupted_message).add_to_stack()
            # The functions shows a pop up telling the player that the save file got corrupted.



        copy_state_popup = lambda: CopyMissionMenu(self.save_file, save_file_name).add_to_stack()



        delete_progress = lambda: (data.delete_save_data(save_file_name), self.__init__(save_file_name))
        # This lambda function deletes the progress and reinitializes the MissionInfo state to show the new iinformation

        delete_confirm_window = lambda: ConfirmationPopUp(f"Delete {heading_text}?", delete_progress).add_to_stack()
        

        self.buttons = ElementMatrix(
            [LongButton(self.heading_padding, 200, "Play Mission", play_confirm_window)],
            [LongButton(0, 0, "Back", self.state_stack.pop)],
            [LongButton(0, 0, "Copy Mission", copy_state_popup, (self.save_file is not None and self.save_file is not SaveFileError))],
            [LongButton(0, 0, "Delete Mission", delete_confirm_window, (self.save_file is not None))]
        )



        
        self.heading_surface = render_heading(heading_text)
        self.subtext_surface = format_text(subtext, assets.SystemFont(FONT_SIZE*2), 300, 4, COLOR_PALETTE[5])
        # These surfaces will be used to display text to the player


        self.prev_state_surface = None
        self.current_state_surface = None
        # These surfaces will be used to display the state entrance animation


    def __get_save_file(self, save_file_name: str) -> SaveFile | SaveFileError | None:
        """
        Loads the save file going by the name and returns it. Returns None if the save file is
        empty. Returns a SaveFileError object if the save file got corrupted.
        """

        try:
            return data.load_save_data(save_file_name)
        except SaveFileError:
            return SaveFileError


    def __get_hour_reading(self, hours: float) -> str:
        "Returns the hours played as a string in the format HH:MM."

        h = int(hours)
        m = int((hours-h)*60)

        if m < 10:
            m_string = f"0{m}"
        else:
            m_string = f"{m}"

        return f"{h}:{m_string}"


    def userinput(self, action_keys, hold_keys) -> None:
        self.buttons.userinput(action_keys, hold_keys, self._get_mouse_pos())

        if action_keys[p.K_ESCAPE]:
            self.state_stack.pop()
            SoundFX.play(LongButton.click_sound)


    
    def update(self, delta_time) -> None:
        self.buttons.update(delta_time)
        self.prev_state_surface = None
        self.current_state_surface = None

    
    def draw(self, surface) -> None:
        super().draw(surface)
        self.ui_grid.blit(self.heading_surface, (self.heading_padding,)*2)

        self.ui_grid.blit(self.subtext_surface, (self.heading_padding, self.subtext_padding))
        self.buttons.draw(self.ui_grid)

        self.blit_ui_grid(surface)




    def draw_on_enter(self, surface: p.Surface, transition_amount: float) -> None:
        super().draw_on_enter(surface, transition_amount)

        w, h = surface.get_size()

        if self.prev_state_surface is None:
            self.prev_state_surface = transparent_surface((w, h))
            self.prev_state.draw(self.prev_state_surface)

        if self.current_state_surface is None:
            self.current_state_surface = transparent_surface((w, h))
            self.draw(self.current_state_surface)

        move_amount = self.__get_move_amount(transition_amount)

        surface.blit(self.prev_state_surface, (int(-w*move_amount), 0))
        surface.blit(self.current_state_surface, (int(w*(1-move_amount)), 0))


    def __get_move_amount(self, transition_amount: float) -> float:
        "Returns how much the states sprites should be offset to provide a smooth transition animation."
        return -0.5*cos(pi*transition_amount)+0.5


    
    def draw_on_exit(self, surface, transition_amount) -> None:
        self.draw_on_enter(surface, 1-transition_amount)















class CopyMissionMenu(PopUpMenu):
    "Shows a menu asking the player what file they wnat to copy the current mission to."

    save_file_names: dict[str, str]

    size = (200, 150)
    draw_prev_state = False
    # I made it not render the previous for this menu because the framerate dropped too much

    def __init__(self, save_file: SaveFile, save_file_name: str) -> None:
        super().__init__("Copy Mission Data", "Choose an available mission log to copy data to. You can only copy to empty mission logs.", "Press ESCAPE to close menu", self.size)

        copy_to_file = lambda file_name: (data.save_data(save_file, file_name), self.state_stack.pop())
        # This function will overwrite the specified save file with the data pf the current save file
        # It also closes the pop up afterwards

        button_list = []

        for file_name, display_name, in self.save_file_names.items():
            if file_name != save_file_name and file_name != "mission_e":
                activated = True
                try:
                    if data.load_save_data(file_name) is not None:
                        activated = False
                except SaveFileError: pass

                copy_to_current_file = lambda fn=file_name: (copy_to_file(fn), log(STATE_INFO, f"Copied from {save_file_name} to {fn}"))
                # I had to pas in a defualt argument here because I realised that the arguments for copy_to_file
                # are only evaluated when the function is called resulting it always copy to the last save file in
                # dictionary.
                # It also outputs a debug message to the console

                button_list.append(LongButton(15, 70, display_name, copy_to_current_file, activated))

        self.buttons = ElementMatrix(button_list)

    
    def userinput(self, action_keys, hold_keys) -> None:
        if action_keys[p.K_ESCAPE]:
            self.state_stack.pop()

        self.buttons.userinput(action_keys, hold_keys, self._get_mouse_pos())


    def update(self, delta_time) -> None:
        self.buttons.update(delta_time)
    

    def _blit_to_ui_grid(self) -> None:
        self.buttons.draw(self.ui_grid)







    












class Settings(Menu):
    "State that shows all the game's settings that the user can change. The users changes are stored at 'data/settings.json'."

    heading = "Settings"
    heading_padding = 15

    def __init__(self) -> None:
        super().__init__((400, 400))

        self.heading_surface = render_heading(self.heading)

        self.camerashake = Toggle(self.heading_padding, 50, "Camera Shake", video.camerashake)
        self.draw_particles = Toggle(0, 0, "Render Particles", video.draw_particles)
        self.fps = Slider(0, 0, "FPS", min_value=30, max_value=120, current_value=video.fps, step=10)

        self.music_volume = Slider(0, 0, "Music", max_value=100, current_value=audio.music_volume*100)
        self.gameplay_volume = Slider(0, 0, "Sound fx", max_value=100, current_value=audio.gameplay_volume*100)

        self.keybind_buttons = {
            action_name: KeyBinder(0, 0, action_name, key)

            for action_name, key, in keybinds.all_settings().items()
        }

        self.setting_elements = ElementMatrix(
            [
                self.camerashake,
                self.draw_particles,
                self.fps,
                self.music_volume,
                self.gameplay_volume,
            ],

            list(self.keybind_buttons.values())
        )



    def userinput(self, action_keys, hold_keys) -> None:
        if action_keys[p.K_ESCAPE]:
            self.state_stack.pop()
            SoundFX.play(LongButton.click_sound)
            
        self.setting_elements.userinput(action_keys, hold_keys, self._get_mouse_pos())



    def update(self, delta_time) -> None:
        self.setting_elements.update(delta_time)

        video.fps = self.fps.current_value
        audio.music_volume = self.music_volume.current_value/100
        audio.gameplay_volume = self.gameplay_volume.current_value/100




    def draw(self, surface: p.Surface) -> None:
        super().draw(surface)

        self.ui_grid.blit(self.heading_surface, (self.heading_padding,)*2)
        
        self.setting_elements.draw(self.ui_grid)

        self.blit_ui_grid(surface)


    def quit(self) -> None:
        video.camerashake = self.camerashake.on
        video.draw_particles = self.draw_particles.on
        video.fps = self.fps.current_value
        
        audio.music_volume = self.music_volume.current_value/100
        audio.gameplay_volume = self.gameplay_volume.current_value/100


        for action_name, keybinder in self.keybind_buttons.items():

            keybinds.set_keybind(action_name, keybinder.key)