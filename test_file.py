import pygame as p
from time import sleep
from random import randint

import glob

from states import State
from typing import Any, Callable, Self
from custom_types import gameplay, animation, base_classes
import game_objects.enemies

from file_processing import assets, data, world

from debug import timer

from file_processing import world

from developer_tools import create_region_map_png





class ReadOnlyError(Exception):
    def __init__(self) -> None:
        super().__init__("Property is read only, cannot be modified or deleted")


class read_only(property):
    def __init__(self, fget: Callable[[Any], Any] | None = ..., doc: str | None = ...) -> None:
        super().__init__(fget, self._display_error, self._display_error, doc)

    def _display_error(self, *_):
        raise ReadOnlyError
    
    

class Singleton:
    _instances = {}
    def __new__(cls, *args, **kwargs) -> Self:
        cls._instances.setdefault(cls, super().__new__(cls))
        return cls._instances[cls]
    
    




class Test:
    x = 2, 34, 60009887
    def __init__(self) -> None:
        self.items = set([1, 2, 3, 4, 5, 6])
        self.value = self.x[2]


    def __iter__(self):
        for item in self.items:
            yield item




class Point(Singleton):
    pass






@timer
def true_blur(surface: p.Surface, intensity: int):
    if intensity < 0:
        raise ValueError("Intensity must be greater than 0")
    if intensity + 2 > min(*surface.get_size()):
        raise ValueError("Intensity is too large for given surface")
    
    width, height = surface.get_size()

    i = intensity
    blurred_surface = p.Surface((width, height))



    for y in range(height):
        for x in range(width):

            region_rect = (
                max(x-i, 0),
                max(y-i, 0),
                min(i, x) + 1 + min(i, width-1-x),
                min(i, y) + 1 + min(i, height-1-y)
            )
            
            color = p.transform.average_color(surface, region_rect, False)
            blurred_surface.set_at((x, y), color)
    
    
    
    return blurred_surface



@timer
def blur(surface: p.Surface, intensity: int):
    i = intensity + 1
    image_size = p.Vector2(surface.get_size())
    blurred_surface = p.transform.smoothscale(surface, image_size/i)
    blurred_surface = p.transform.smoothscale(blurred_surface, image_size)

    return blurred_surface



if __name__ == "__main__":
    print(glob.glob("data/*", recursive=True))