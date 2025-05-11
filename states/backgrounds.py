"""
This module contains background states. These states play in the background
of other states.
"""

import pygame as p

from ui import COLOR_PALETTE

from .state import State

# At the moment there is only one background State 'Starts' which is
# very basic as it only shows a block colour.

# But the background system can be expanded easily to have different variety
# background designs there can also be moving backgrounds.


# This state was initially going to show a scrolling backdrop of stars
# but that feature was removed due to time constraints and performance
# issues.
class Stars(State):
    def draw(self, surface) -> None:
        surface.fill(COLOR_PALETTE[1])