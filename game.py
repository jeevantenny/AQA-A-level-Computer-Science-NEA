"Contains the Game class."

import pygame as p
from pygame.locals import *

from collections import defaultdict
import traceback
from time import perf_counter

from settings import video
from states import *

from file_processing.assets import DebugFont, load_texture
from config import *

import ui
import audio
import settings

from math_functions import clamp
from debug import log, CRITICAL, WARNING, GAME_INFO, DEBUGGING
import ui.buttons






class Game:
    """
    This is the main class of the game. The start_state parameter takes a state class as an argument. This will be the state
    the game starts with. Call the start() method to start the gameloop.
    """

    def __init__(self, start_state: type[state.State] = state.State, *state_args) -> None:
        p.mixer.pre_init()
        p.init()
        audio.init()
        settings.load()
        # Initialise pygame and cutsom modules

        self.monitor_info = p.display.Info() # An object that holds the information of the compputer's moniter

        self.resizable_size = WINDOW_STARTING_SIZE
        # This variable stores the size of the window before becoming fullscreen.
        # The window will set back to this size when coming out of full screen.

        self.window = p.display.set_mode(WINDOW_STARTING_SIZE, RESIZABLE | DOUBLEBUF | HWSURFACE)
        # Creates the game window and assigns the window surface to self.window

        self.fullscreen = False
        # Variable that controls the toggling between fullscreen and resizable mode


        state.State.init_class()
        ui.init()
        
        if TITLE:
            p.display.set_caption(TITLE)
        if ICON:
            p.display.set_icon(load_texture(ICON, translucency=True))

        
        
        self.run = True # The game runs while the value of this variable is True.

        self.clock = p.time.Clock()
        self.prev_time = perf_counter()
        self.delta_time = 1/video.fps # Used to record the time between frames. It is currently assigned a starting value.

        # The following two dictionaries hold the player's keyboard and mouse input.
        # Both of them are defaultdicts which return a default value for any key entered, even if the key is not in the dictionary
        # The key is then added into the dictionary with the defualt value pair.

        # Keyboard buttons are represented using pygame's key representations (A = pygame.K_a, B = pygame.K_b, space = pygame.K_SPACE)
        # Mouse buttons are represented by "mouse_left" and "mouse_right"

        self.action_keys = defaultdict(bool)
        # The value for a key in this dictionary will be True if the player has pressed the key in the current frame. Else it will be False
        # Default = False
        # This dictionary will have an "any" key that can be used to check if any button has been pressed

        self.hold_keys = defaultdict(float)
        # Stores how long (in seconds) each key has been pressed for as a float. When a key is lifted the the value will return to 0.0.
        # 0.0


        self.state_stack = state.StateStack(start_state(*state_args), background_state=backgrounds.Stars())
        # This is the state stack. It is a stack that holds different game states.
        # During the game loop, the top state is processed.
        # States within the stack can pop or push states into the stack.


        # These variables were used when debugging
        self.debug_font = DebugFont(16)
        self.game_speed = 1 # to slow down the speed of the game to debug
        self.error_occured = False






    def start(self) -> None:
        """
        Starts the game loop. The game loop has an input, process and draw cycle. 
        """

        try:
            while self.run:
                self.userinput()
                self.update()
                self.draw()

                self.next_frame()
        
        except Exception:
            traceback.print_exc()
            if DEBUGGING:
                input("\033[36mClose Window ->\033[0m")
                # This if statement was used when debugging to prevent the window from closing when an exception occurs to allow me to see what happened on screen.
                # It will display a prompt to the console to close the window.
        

        finally:
            # This line of code always executes at the end of the program, even if there's an uncaught exception and the game crashes
            # This ensures that the game will try to save the user's progress and settings even if the game crashes.
            self.quit() # I AM INEVITABLE

    

    
    def userinput(self) -> None:
        "The first stage of the gameloop where the userinput is stored into dictionaries."

        for key in self.action_keys:
            self.action_keys[key] = False
        # Sets all the values in the dictionary to False as it is only meant be True if the key was pressed in the current frame.
        
        for event in p.event.get():
            if event.type == QUIT:
                self.run = False
            # Closes the game when the 'X' button on the window is clicked.
            

            elif event.type == VIDEORESIZE and not self.fullscreen:
                width, height = event.size
                min_width, min_height = MIN_WINDOW_SIZE

                if width < min_width or height < min_height:
                    self.window = p.display.set_mode((max(width, min_width), max(height, min_height)), RESIZABLE | DOUBLEBUF | HWSURFACE)
                # Enusures that the window never becomes smaller than the minimum window size when the player resizes the window.


            # When a keyboard button is pushed down
            elif event.type == KEYDOWN: 
                self.action_keys[event.key] = True
                self.action_keys["any"] = True
                # Set
                
                self.hold_keys[event.key] = self.delta_time

            # When a beyboard button is released
            elif event.type == KEYUP:
                self.hold_keys[event.key] = 0.0


            # When a mouse button is pressed down
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.action_keys["mouse_left"] = True
                    self.hold_keys["mouse_left"] = self.delta_time
                elif event.button == 3:
                    self.action_keys["mouse_right"] = True
                    self.hold_keys["mouse_right"] = self.delta_time
                
                self.action_keys["any"] = True

            
            # When a mouse button is released
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.hold_keys["mouse_left"] = 0.0
                elif event.button == 3:
                    self.hold_keys["mouse_right"] = 0.0
        
        
        # Increment the time a button was pushed down for
        for key, value in self.hold_keys.items():
            if value != 0.0:
                self.hold_keys[key] += self.delta_time



        # Pressing ALT and F11 keys will toggle fullscreen mode
        if self.hold_keys[K_LALT] and self.action_keys[K_F11]:
            self.fullscreen = not self.fullscreen
            
            if self.fullscreen:
                self.resizable_size = self.window.get_size()
                self.window = p.display.set_mode((self.monitor_info.current_w, self.monitor_info.current_h), FULLSCREEN | DOUBLEBUF | HWSURFACE)
                # Changes the display mode to full screen
            
            else:
                self.window = p.display.set_mode(self.resizable_size, RESIZABLE | DOUBLEBUF | HWSURFACE)
                # Changes the display mode back to resizable.




        if DEBUGGING:
            if self.hold_keys[K_LCTRL] and self.action_keys[K_BACKSPACE]:
                self.state_stack.pop(exit_transition=False)
            # Pressing control backspace will force quit the current state (only works in debugging mode.)

        self.state_stack.userinput(self.action_keys, self.hold_keys)




    def update(self) -> None:
        "The second stage of the gameloop where game logic is processed."

        self.state_stack.update(self.delta_time*self.game_speed)

        audio.Music.update(self.delta_time)
        # Updates the music of the game.
        # This is mainly done to update the music's volume when the player changes the setting for it.






    def draw(self) -> None:
        "The third stage of the gameloop where the screen is rendered."

        state_debug_text = self.state_stack.draw(self.window)
        # Calls the state stack's draw method to dipslay the current state
        # This returns either None or a string containing information useful when debugging.


        if DEBUGGING:
            current_state = self.state_stack[-1]
            self.window.fill(DEBUG_TEXT_BACKGROUND, (0, 0, 800, 25), special_flags=BLEND_RGB_SUB)
            self.window.blit(
                self.debug_font.render(f"FPS: {self.clock.get_fps():.0f}, Current State: {current_state}, Previous State: {current_state.prev_state}, Background: {self.state_stack.background_state}, Show Background: {current_state.show_background}",True, (255, 255, 255)),
                (5, 3)
            ) # Diplays basic information related to the game that will always be shown

            if state_debug_text is not None:
                self.window.fill(DEBUG_TEXT_BACKGROUND, (0, 25, 800, 25), special_flags=BLEND_RGB_SUB)
                self.window.blit(self.debug_font.render(f"{state_debug_text}", True, "white"), (5, 28))
                # Displays the debug text of the current state if there is any

    


    def next_frame(self) -> None:
        "The fourth stage of the gameloop where the display is updated and the delta time is calculated for the next frame."

        p.display.update()
        # Refreshed the display so that the contents of self.window is visible on the actual window
        self.clock.tick(video.fps)
        # Controls the framerate of the game

        time_now = perf_counter()
        self.delta_time = clamp(time_now - self.prev_time, 1/video.fps - FRAME_DURATION_ERROR, 1/video.fps + FRAME_DURATION_ERROR)
        self.prev_time = time_now
        # Calculates the new value for delta time
        





    def quit(self) -> None:
        "Makes sure any data that needs to be saved on any state is saved before exiting the program."

        try:
            settings.save() # Saves user settings
            self.state_stack.quit() # Calls the quit method on all states allowing them to save any data
            p.quit() # Quits pygame
            log(GAME_INFO, "Game Closed")
        except Exception:
            traceback.print_exc()
            log(CRITICAL, "Error occured when closing. State data may not have been saved.")
            # If an error occurs when trying to save data state data, a critical message will be output to the console.