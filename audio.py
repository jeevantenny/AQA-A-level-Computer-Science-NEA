"""
This module contains classes that are used to control audio playback. I have made these classes
because it is easier to manage the audio this way rather than using pygame.mixer directly.
"""

import pygame as p
from typing import NoReturn
 
from file_processing import assets
import settings

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import Timer
import settings.audio

from debug import log, GAME_INFO
from errors import AssetError




MUSIC_DIR = "assets/audio/songs/"
SOUND_FX_DIR = "assets/audio/sound_fx/"
SOUND_LINK_PATH = "assets/audio_links.json"



def init() -> None:
    audio_data = assets.load_json(SOUND_LINK_PATH)
    Music.init_class(audio_data["music"])
    SoundFX.init_class(audio_data["sound_fx"])


class Music(BasicGameElement):
    "This class use used to control the playback of music in the game."

    DEFAULT_FADE_DURATION = 1
    music_list: dict[str, str]
    current_song = None

    def __new__(cls) -> NoReturn:
        raise TypeError(f"{cls} cannot create instances.")
        # There is no need to create an instance of this class so it should not be done
    
    @classmethod
    def init_class(cls, music_list) -> None:
        cls.load_assets(music_list)
        cls._timer = Timer(cls.DEFAULT_FADE_DURATION)
        super().init_class()
    
    @classmethod
    def __assets__(cls, asset_list) -> None:
        cls.music_list = asset_list
        # Loads the list of music from the audio_links.json file

    
    @classmethod
    def play(cls, song_name: str) -> None:
        "Plays the song that goes by the song name."

        if cls.current_song is None:
            try:
                p.mixer.music.load(f"{MUSIC_DIR}{cls.music_list[song_name]}")
                p.mixer.music.play(-1) # Plays the song and makes it loop indefinitely
                cls.current_song = song_name
                log(GAME_INFO, f"Playing song '{song_name}'")
            
            except KeyError:
                raise ValueError(f"Invalid song name '{song_name}'.")
            
            except FileNotFoundError:
                raise AssetError(f"File path specified in '{SOUND_LINK_PATH}' does not exists. There is no such file as '{cls.music_list[song_name]}'.")
        
        elif cls.current_song != song_name:
            p.mixer.music.fadeout(cls.DEFAULT_FADE_DURATION*1000)
            cls.current_song = None
            cls._timer = Timer(cls.DEFAULT_FADE_DURATION+0.1, False, cls.play, song_name).start()
            # If there is already a song playing the current song is faded out before playing the new song
        
    

    @classmethod
    def pause(cls) -> None:
        "Pauses the current song playing."

        if cls.current_song is not None:
            p.mixer.music.pause()
            log(GAME_INFO, f"Paused song {cls.current_song}")

    
    @classmethod
    def resume(cls) -> None:
        "Resumes the song after it has been paused."

        if cls.current_song is not None:
            p.mixer.music.unpause()
            log(GAME_INFO, f"Resumed song {cls.current_song}")


    @classmethod
    def stop(cls) -> None:
        "Stops the current song from playing"
        if cls.current_song is not None:
            p.mixer.music.stop()
            p.mixer.music.unload()
            log(GAME_INFO, f"Stopped playing song '{cls.current_song}'")
            cls.current_song = None
    


    @classmethod
    def update(cls, delta_time: float) -> None:
        cls._timer.update(delta_time)
        p.mixer.music.set_volume(settings.audio.music_volume)
        # Updates the volume of the current song to match the setting







class SoundFX(BasicGameElement):
    "This class is used to control the playback of sound effects in the game."

    sound_fx_list: dict[str, str]
    
    
    @classmethod
    def init_class(cls, sound_fx_list) -> None:
        cls.load_assets(sound_fx_list)
        super().init_class()
    
    @classmethod
    def __assets__(cls, sound_fx_list) -> None:
        cls.sound_fx_list = sound_fx_list
        # Loads the list of sound effects from the audio_links.json file
    
    def __new__(cls) -> NoReturn:
        raise TypeError(f"{cls} cannot create instances.")
        # There is no need to create an instance of this class so it should not be done
    

    @classmethod
    def play(cls, sound_name: str) -> None:
        "Plays the sound effect that goes by the sound name."

        try:
            sound = p.mixer.Sound(f"{SOUND_FX_DIR}{cls.sound_fx_list[sound_name]}")
            sound.set_volume(settings.audio.gameplay_volume)
            sound.play()
            log(GAME_INFO, f"Played sound '{sound_name}'")
        
        except KeyError:
            raise ValueError(f"Invalid sound name '{sound_name}'")
        
        except FileNotFoundError:
            raise AssetError(f"File file specified in '{SOUND_LINK_PATH}' does not exists. There is no such file as '{cls.music_list[sound_name]}'.")