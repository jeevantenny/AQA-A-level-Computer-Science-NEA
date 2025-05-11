"This module contains various states that act as a transition when the state stack is reset."

import pygame as p

from .state import State




class Transition(State):
    "A state that shows a visual tranistion when the state stack reset and populated with new states."

    def __init__(self, duration: float) -> None:
        self.enter_duration = self.exit_duration = duration/2
        # The sum of the enter_duration and the exit_duration will be
        # the total duration of the transition.
    



class Fade(Transition):
    "Transition that fades the screen through colour (default is black)."

    def __init__(self, duration: float, color: p.Color = (0, 0, 0)) -> None:
        super().__init__(duration)

        self.darken_prev_state = p.Surface((10, 10)).convert()
        self.darken_prev_state.fill(color)
        self.darken_prev_state.set_alpha(0)



    def draw_on_enter(self, surface, transition_amount) -> None:
        super().draw_on_exit(surface, transition_amount)
        self.darken_prev_state.set_alpha(int(255*(transition_amount**2)))
        surface.blit(p.transform.scale(self.darken_prev_state, surface.get_size()), (0, 0))
        # Fade into black
    

    def draw_on_exit(self, surface, transition_amount) -> None:
        self.draw_on_enter(surface, 1-transition_amount)
        # Fades out of black
        # I made it do draw_on_enter in reverse to avoid repeating code.