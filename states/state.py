"Contains the base state class and the StateStack class."

import pygame as p

from file_processing import assets

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import Timer
from math_functions import clamp
from debug import *





class State(BasicGameElement):
    """
    Base class for any state in the game.
    """
    state_stack = None

    show_background = False
    enter_duration = 0.0
    exit_duration = 0.0
    

    @classmethod
    def init_class(cls) -> None:
        cls.load_assets(assets.load_class_assets("state_assets.json"))
        super().init_class()

    def __init__(self) -> None:
        self.state_stack: StateStack



    @property
    def prev_state(self): # State | None
        "Returns the state that is behind the current state in the stack."

        if self.state_stack is not None and self in self.state_stack:
            i = self.state_stack.index(self)
            if i != 0:
                return self.state_stack[i-1]
        
        return None



    def add_to_stack(self) -> None:
        """
        Pushes the state to the stack. It also allows the state to perform an
        action when it is pushed. to the stack.
        """
        if self not in self.state_stack:
            self.state_stack.append(self)
            log(GAME_INFO, f"Added {self} to statestack")


    def update_on_enter(self, delta_time: float, transition_amount: float) -> None:
        "Processing while entering state."

        transition_amount = clamp(transition_amount, 0, 1)


    def update_on_exit(self, delta_time: float, transition_amount: float) -> None:
        "Processing while exiting state."

        transition_amount = clamp(transition_amount, 0, 1)



    def draw(self, surface) -> (str | None):
        super().draw(surface)
        # States can output a debug message that will be used by the main
        # Game class to display at the top of the screen in debug mode.


    def draw_on_enter(self, surface: p.Surface, transition_amount: float) -> None:
        "Display an entrance animation when the state is pushed from the stack."

        transition_amount = clamp(transition_amount, 0, 1)
    

    def draw_on_exit(self, surface: p.Surface, transition_amount: float) -> None:
        "Display an exit animation when the state is popped from the stack."

        transition_amount = clamp(transition_amount, 0, 1)


    def quit(self) -> None:
        "Saves any data that needs to be saved."


    def __repr__(self) -> str:
        return f"{self}(stack_position: {self.state_stack.index(self)}, prev: {self.prev_state})"
    

    def __str__(self) -> str:
        return type(self).__name__
    








ENTER_STATE = 1
SHOW_STATE = 2
EXIT_STATE = 3
RESET_TRANSITION = 4



class StateStack(list[State]):
    def __init__(self, *states: State, background_state: State | None = None) -> None:
        super().__init__()
        State.state_stack = self
        
        self.current_action = ENTER_STATE
        for state in states:
            state.add_to_stack()
            
        if background_state:
            self.background_state = background_state
        else:
            self.background_state = None
    
        self.timer = Timer(self[-1].enter_duration).start()

        self.reset_transition = None
        self.states_to_add = None



    def reset(self, *states: State, transition: State | None = None) -> None:
        """
        Clears the state stack and fills it with new states. A transition animation
        can be played during this.
        """
        
        self.current_action = RESET_TRANSITION
        if transition is not None:
            self.reset_transition = transition
            self.states_to_add = states

            self.timer.duration = transition.enter_duration
            self.timer.start()
        else:
            self.pop_all()
            for state in states:
                state.add_to_stack()
            
            self.current_action = SHOW_STATE


    def __reset_after_transition(self, states: tuple[State]) -> None:
        self.pop_all()
        for state in states:
            state.add_to_stack()


    def append(self, state: State) -> None:
        super().append(state)
        if state.enter_duration and self.current_action == SHOW_STATE:
            self.current_action = ENTER_STATE
            self.timer.duration = state.enter_duration
            self.timer.start()
    

    def pop(self, exit_transition=True) -> State:
        "Removes and quits the top state."

        if self[-1].exit_duration != 0 and exit_transition:
            self.current_action = EXIT_STATE
            self.timer.duration = self[-1].exit_duration
            self.timer.start()
        else:
            state = super().pop()
            log(GAME_INFO, f"Removed {state} from statestack")
            state.quit()


    def pop_all(self) -> None:
        for _ in range(len(self)):
            super().pop().quit()
        
        log(GAME_INFO, "Cleared statestack")
    


    def userinput(self, action_keys: dict[int, bool], hold_keys: dict[int, bool]) -> None:
        if (
            (
                self.current_action == SHOW_STATE
                or (self.current_action == RESET_TRANSITION and self.states_to_add is None)
            )
            and self
            ):
            self[-1].userinput(action_keys, hold_keys)


    def update(self, delta_time: float) -> None:
        "Updates the background state and top state."

        self.timer.update(delta_time)
  
        if self.background_state is not None and self[-1].show_background:
            self.background_state.update(delta_time)



        if self.current_action == ENTER_STATE:
            self[-1].update_on_enter(delta_time, self.timer.completion_amount)

        elif self.current_action == SHOW_STATE:
            self[-1].update(delta_time)

        elif self.current_action == EXIT_STATE:
            self[-1].update_on_exit(delta_time, self.timer.completion_amount)
            if self.timer.complete:
                self.pop(False)
        


        if self.current_action == RESET_TRANSITION:
            if self.states_to_add is not None:
                self.reset_transition.update_on_enter(delta_time, self.timer.completion_amount)
            else:
                self[-1].update(delta_time)
                self.reset_transition.update_on_exit(delta_time, self.timer.completion_amount)

        
            if self.timer.complete:
                if self.states_to_add is not None:
                    self.__reset_after_transition(self.states_to_add)
                    self.states_to_add = None
                    self.timer.start()
                else:
                    self.reset_transition = None
                    self.current_action = SHOW_STATE
            

            
        elif self.timer.complete:
            self.current_action = SHOW_STATE
            


    def draw(self, surface: p.Surface) -> str | None:
        "Draws the background state and top state onto the window."

        if self.background_state is not None and self[-1].show_background:
            self.background_state.draw(surface)
        
        

        if self.current_action == SHOW_STATE:
            return self[-1].draw(surface)

        elif self.current_action == ENTER_STATE:
            self[-1].draw_on_enter(surface, self.timer.completion_amount)

        elif self.current_action == EXIT_STATE:
            self[-1].draw_on_exit(surface, self.timer.completion_amount)
        


        elif self.current_action == RESET_TRANSITION:
            self[-1].draw(surface)
            if self.states_to_add is not None:
                self.reset_transition.draw_on_enter(surface, self.timer.completion_amount)
            else:
                self.reset_transition.draw_on_exit(surface, self.timer.completion_amount)

            



    def quit(self) -> None:
        for state in self:
            state.quit()



    def __str__(self) -> str:
        return f"{type(self).__name__}[length: {len(self)}, top: {self[-1]}]"