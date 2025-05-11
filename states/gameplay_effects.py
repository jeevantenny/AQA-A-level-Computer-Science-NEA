"""
This class contains states that will be be put ontop of the Play state in the
stack to alter the speed and visuals of the gameplay.
"""

import pygame as p

from .state import State

from custom_types.gameplay import Timer



# At the moment this is the only gameplay effect there is
class SlowMotion(State):
    "Slows down the speed of the game."

    def __init__(self, duration: float, speed=0.1) -> None:
        super().__init__()
        self.timer = Timer(duration, execute_after=self.state_stack.pop).start()
        # The timer will remove the slowmotion state after it's duration
        self.speed = speed
        if self.state_stack is not None and not isinstance(self.state_stack[-1], SlowMotion):
            self.add_to_stack()

    def userinput(self, action_keys, hold_keys) -> None:
        self.prev_state.userinput(action_keys, hold_keys)

    def update(self, delta_time) -> None:
        self.prev_state.update(delta_time*self.speed)
        self.timer.update(delta_time)

    def draw(self, surface) -> None:
        self.prev_state.draw(surface)