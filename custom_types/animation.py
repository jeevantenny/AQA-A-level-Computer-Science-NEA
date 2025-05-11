"This module contains classes that store and manage animation data for game objects."

import pygame as p
from typing import Self, Literal, Any
from copy import deepcopy

from .gameplay import Timer

from debug import log, WARNING




# type controller_state = dict[str, Animation | dict[str, str]]

SPRITE_ANIM = "sprite_animation"
MODEL_ANIM = "model_animation"


class Animation:
    "Controls how what texture is shown for animated entities."

    def __new__(cls, name, anim_data, type: Literal["sprite_animation", "model_animation"] = SPRITE_ANIM) -> "SpriteAnimation":
        if type == SPRITE_ANIM:
            anim = SpriteAnimation(name, anim_data)
            return anim
        elif type == MODEL_ANIM:
            raise NotImplementedError("Model animation has not been implemented yet.")
            # There were plans to implement a model animation system wher that works
            # by rotating and repositioning sprites for different parts of the entity
            # but this plan was discontinued.
        
        else:
            raise ValueError(f"Invalid animation type '{type}'.")


    def __init__(self, name: str, anim_data: dict[str, Any]) -> None:
        self.name = name
        
        self.duration: float = anim_data["duration"]
        self.loop = anim_data.get("loop", False)
        self._anim_timer = Timer(self.duration, self.loop)
        # The duration of the animation
        
        self.anim_speed_multiplier = str(anim_data.get("anim_speed_multiplier", "1"))
        # Effect the speed and duration of the animation


    @property
    def anim_time(self) -> float:
        """
        How much time has passed from the start of the animation.
        The time resets if the animation loops.
        """

        time = self._anim_timer.time_elapsed

        if time == self.duration:
            return 0.0
    
        return time
    

    @property
    def complete(self) -> bool:
        return self._anim_timer.complete



    def update(self, delta_time: float, entity) -> None:
        self._anim_timer.update(delta_time*self._get_anim_property(self.anim_speed_multiplier, entity, 1))


    def get_frame(self, texture_map: dict[str, p.Surface]) -> p.Surface:
        "Gets the current animation frame to display."
        # Will be implemented by subclasses


    def play(self) -> None:
        "Starts the animations"
        self._anim_timer.start()
    

    def _get_anim_property(self, text: str, entity, default_value: Any) -> Any:
        """
        Returns the value for an animation property stored in a json
        file by evaluating the python expression.

        If the expression is invalid the default value is returned.
        """
        try:
            return eval(text, None, locals())
        except:
            return default_value


    def __str__(self) -> str:
        return f"{type(self).__name__}('{self.name}')"
    

    def __repr__(self) -> str:
        return  f"{type(self).__name__}(name: '{self.name}', duration: {self.duration}, anim_time: {self.anim_time})"
        


class SpriteAnimation(Animation):
    """
    A type of animation that works by flipping through different
    textures.
    """

    def __new__(cls, *args, **kwargs) -> Self:
        return object.__new__(cls)
        # Since SpriteAnimation inherits from Animation the __new__
        # method is redefined to it recurring infinately.
    
    def __init__(self, name: str, anim_data: dict[str, Any]) -> None:
        super().__init__(name, anim_data)

        self.timeline: dict[str, p.Surface] = {
            float(time): frame_name
            for time, frame_name in anim_data["timeline"].items()
        }
        # A dictionary of all frames and what time they should occur
        


    def get_frame(self, texture_map: dict[str, p.Surface]) -> p.Surface:
        frame_name = None
        for time, name in self.timeline.items():
            if self.anim_time >= time:
                frame_name = name
            else:
                break

        if frame_name is None:
            raise Exception("Initial frame not defined.")
        
        return texture_map[frame_name]

        



class controller_state(dict[str, Animation | dict[str, str]]):
    "A dictionary that stores the animations and transitions of a state."



class AnimController:
    """
    This class controls the playing of animations for an entity
    based on various conditions of the entity. Multiple animations
    can be played at the same time.
    """

    def __init__(self, controller_data: dict[str, str | dict], animations: dict[str, Animation]) -> None:
        self.name: str = controller_data["name"]

        self.states: dict[str, controller_state] = deepcopy(controller_data["states"])

        for state_data in self.states.values():
            state_data["animations"] = [animations[anim_name] for anim_name in state_data["animations"]]


        self.state_name = controller_data["starting_state"]


        self.errors = []
        # A list of all unique errors that have occured during state transitions


    @property
    def current_animations(self) -> list[Animation]:
        "All animations that are currently playing."

        return self.current_state["animations"]
    

    @property
    def current_state(self) -> controller_state:
        return self.states[self.state_name]
    
    @property
    def animations_complete(self) -> None:
        "Returns True if all current animations are complete."

        return all([animation._anim_timer.complete for animation in self.current_animations])

    



    def update(self, delta_time: float, entity) -> None:
        for state_name, trans_condition in self.current_state.get("transitions", {}).items():

            if self.__test_condition(trans_condition, entity):
                self.state_name = state_name
                for animation in self.current_animations:
                    animation.play()
                break

        for animation in self.current_animations:
            animation.update(delta_time, entity)


    

    def __test_condition(self, condition: str, entity) -> bool:
        """
        Method used to test transition conditions.

        Each state will have a list of other states it can transition to. Each
        state has a transition condition which is a python expression that can
        use attributes of the current AnimationController object and the entity
        it belongs to.
        """

        result: bool = False
        _locals = locals()

        try:
            result = bool(eval(condition, None, _locals))
            return result
        except Exception as e:
            error_data = (self.name, self.state_name, str(e))
            if error_data not in self.errors:
                self.errors.append(error_data)
                log(
                    WARNING,
                    f"Error found in animation controller when checking state transition conditions.\n{self.name}('{self.state_name}'): {e}\n"
                )
            return False



    def get_frame(self, texture_map: dict[str, p.Surface]) -> p.Surface:
        """
        Returns a frame that is combination of all the current frames of
        all current animations layered on top of one another.
        """

        from file_processing import assets
        final_frame = p.Surface((1, 1)).convert()
        final_frame.fill("white")

        for animation in self.current_animations:
            frame = animation.get_frame(texture_map)

            w = max(frame.get_width(), final_frame.get_width())
            h = max(frame.get_height(), final_frame.get_height())

            if w > final_frame.get_width() or h > final_frame.get_height():
                temp_frame = p.Surface((w, h)).convert()
                temp_frame.fill("white")
                temp_frame.blit(final_frame, (0, 0))
                final_frame = temp_frame

            final_frame.blit(frame, (0, 0))
        

        
        final_frame.set_colorkey(assets.COLOR_KEY)

        return final_frame