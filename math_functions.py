"This module provides helpful functions that deals with integers, floats and pygame vectors."

import pygame as p
from random import uniform
from typing import Literal, Any





def clamp(value: int | float, Min: int | float, Max: int | float) -> (int | float):
    "Restricts the number given to the range given."

    return min(Max, max(value, Min))



def sign(value: int | float) -> Literal[-1, 0, 1]:
    "Returns the sign of a number. If the number is equal to 0 than return 0."

    if value == 0:
        return 0
    return abs(value)/value



def vector_min(*vectors: p.Vector2) -> p.Vector2:
    "Returns the vector with the smallest value."

    magnitude_list = [v.magnitude() for v in vectors]
    i = magnitude_list.index(min(*magnitude_list))

    return vectors[i]




def vector_max(*vectors: p.Vector2) -> Any:
    "Returns the vector with the largest magnitude."

    magnitude_list = [v.magnitude() for v in vectors]
    i = magnitude_list.index(max(*magnitude_list))
    
    return vector_max[i]



def unit_vector(vector: p.Vector2) -> p.Vector2:
    "Return the direction of the vector as another vector. This vector will have a magnitude of one."

    size = vector.magnitude()
    if size == 0:
        return p.Vector2(0, 0)
    else:
        return vector/size
    

def range_percent(value: float, min: float, max: float) -> float:
    """
    Restricts value between range of min and max. It then returns what percentage of the range the resultant value is.

    E.g. value = 8, min = 2, max = 12

    The restricted value will still be 8 as it is within the range. It will then return (8-2)/(12-2) to give to give 0.6.
    """

    restricted_value = clamp(value, min, max)
    return (restricted_value-min)/(max-min)
    


def random_error(value: float, error: float) -> float:
    "Returns value provided with a random error of + or - error."

    return uniform(value-error, value+error)