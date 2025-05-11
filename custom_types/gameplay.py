"""
This module contains classes.
"""

import pygame as p
from typing import Self, Callable, Sequence, Literal
from collections import defaultdict
from time import perf_counter


### Code only works in python 3.12
# type actions_dict = defaultdict[str | int, bool]
# type holds_dict = defaultdict[str | int, float]
# type Coordinate = tuple[float, float] | Sequence[float] | p.Vector2

class actions_dict(defaultdict[str | int, bool]): pass
class holds_dict(defaultdict[str | int, float]): pass
class Coordinate(Sequence[float]): pass





class FloatRect:
    """
    Similar to pygame.rect.Rect but is able to store floating point.
    values. I will use this to represent the hitbox and position of
    entities as I found that using integer values caused problems
    with collision.
    """

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x, self.y, self.width, self.height = x, y, width, height

    @property
    def left(self) -> float:
        return self.x
    @left.setter
    def left(self, value: float):
        self.x = value
        
    @property
    def right(self) -> float:
        return self.x + self.width
    @right.setter
    def right(self, value: float):
        self.x = value - self.width
    
    @property
    def top(self) -> float:
        return self.y
    @top.setter
    def top(self, value: float):
        self.y = value
        
    @property
    def bottom(self) -> float:
        return self.y + self.height
    @bottom.setter
    def bottom(self, value: float):
        self.y = value - self.height

    @property
    def topleft(self) -> float:
        return self.left, self.top
    @topleft.setter
    def topleft(self, value: tuple[float, float]):
        self.left, self.top = value

    @property
    def topright(self) -> float:
        return self.right, self.top
    @topright.setter
    def topright(self, value: tuple[float, float]):
        self.right, self.top = value

    @property
    def bottomleft(self) -> float:
        return self.left, self.bottom
    @bottomleft.setter
    def bottomleft(self, value: tuple[float, float]):
        self.left, self.bottom = value

    @property
    def bottomright(self) -> float:
        return self.right, self.bottom
    @bottomright.setter
    def bottomright(self, value: tuple[float, float]):
        self.right, self.bottom = value

    @property
    def centerx(self) -> float:
        return self.x + self.width/2
    @centerx.setter
    def centerx(self, value: float):
        self.x = value - self.width/2
    
    @property
    def centery(self) -> float:
        return self.y + self.height/2
    @centery.setter
    def centery(self, value: float):
        self.y = value - self.height/2
    
    @property
    def center(self) -> float:
        return self.centerx, self.centery
    @center.setter
    def center(self, value: tuple[float, float]):
        self.centerx, self.centery = value

    @property
    def size(self) -> float:
        return self.width, self.height
    @size.setter
    def size(self, value):
        self.width, self.height = value


    def colliderect(self, rect_value: p.Rect | Self) -> bool:
        "Returns True of the given rect intersects the current rect."

        if abs(self.centerx - rect_value.centerx) < (self.width*0.5 + rect_value.width/2):
            if abs(self.centery - rect_value.centery) < (self.height*0.5 + rect_value.height/2):
                return True
            
        return False
    


    def contact_with(self, rect_value: p.Rect | Self) -> Literal["top", "bottom", "left", "right"] | None:
        """
        Returns the side on which the given rect comes into contact with
        the currents rect. Returns None if no sides come into contact.

        This method will be useful for collision checking between entities
        and tiles.
        """
        
        if abs(self.centerx - rect_value.centerx) < (self.width + rect_value.width)/2:
            if self.top == rect_value.bottom:
                return "top"
            if self.bottom == rect_value.top:
                return "bottom"
            
        if abs(self.centery - rect_value.centery) < (self.height + rect_value.height)/2:
            if self.left == rect_value.right:
                return "left"
            if self.right == rect_value.left:
                return "right"
            
        return None
    


    def scale(self, amount: float) -> Self:
        """
        Increases the rect's size by a scale factor while keeping
        the centre position the same.
        """

        rect = FloatRect(0, 0, *p.Vector2(self.size)*amount)
        rect.center = self.center
        return rect

    
    

    def draw(self, surface: p.Surface, offset: Coordinate, width: int, color: p.Color) -> None:
        "Draws the given rect onto the surface with a line width and colour."

        p.draw.rect(surface, color, (self.x+offset[0], self.y+offset[1], self.width, self.height), width)


    
    def copy(self) -> Self:
        return FloatRect(self.x, self.y, self.width, self.height)



class Timer:
    """
    The Timer class starts a countdown of a certain duration and executes a
    function when it is completed. There is also the option for the timer
    to loop and execute the function at the end of each loop.

    This is one the most used functions throughout the game as it is needed
    to ensure framerate independance and to perform actions after a time
    delay.
    """

    def __init__(self, seconds: float, loop = False, execute_after: Callable[[], None] | None = None) -> None:
        self.duration = float(seconds)
        self.countdown = 0.0
        self.loop = loop

        
        self._func = execute_after

        self._can_execute = False


    @property
    def complete(self) -> bool:
        "Return True if the timer is complete. It will also return True if it hasn't started yet."
        return self.countdown <= 0.0
    

    @property
    def time_elapsed(self) -> float:
        "Return the time that has elasped after start() was called."
        return self.duration - self.countdown
    

    @property
    def completion_amount(self) -> float:
        "Return the percentage completion of the timer as a decimal (0.0 - 1.0)."
        if self.duration == 0:
            return 1.0
        else:
            return self.time_elapsed/self.duration


    def update(self, delta_time: float) -> None:
        if not self.complete:
            self.countdown -= delta_time

        if self.complete:
            if self._func is not None and self._can_execute:
                self._func()

            if self.loop:
                self.countdown += self.duration
            else:
                self.countdown = 0.0
                self._can_execute = False



    def start(self) -> Self:
        "Starts the timer by setting the countdown attribute to the duration"
        self.countdown = self.duration
        self._can_execute = True
        return self
    

    def stop(self) -> None:
        """
        Stops the timer and sets the countdown to 0.0. This will not
        trigger the execute function.
        """
        self.countdown = 0.0
        self._can_execute = False


    def copy(self) -> Self:
        "Returns a copy of the timer that hasn't been started."
        return Timer(self.duration, self.loop, self._func, *self._args)
    

    def __repr__(self) -> str:
        return f"{type(self).__name__}{self.countdown}"