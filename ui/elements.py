"Contains the base class UIelement and the ElementMatrix."

import pygame as p

from . import FONT_SIZE

from file_processing import assets

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import Timer, actions_dict, holds_dict, Coordinate

from audio import SoundFX

from file_processing import assets
from math_functions import vector_min, sign




class UIElement(BasicGameElement):
    """
    A single element in the user interface that can be selected while
    being part of an ElementMatrix object.
    """

    size: tuple[int, int]
    # 
    hold_delay = 0.4


    @classmethod
    def init_class(cls, asset_data: dict | None = None) -> None:
        if asset_data is None:
            asset_data = assets.load_class_assets("ui_assets.json")

        cls.load_assets(asset_data)
        ElementMatrix.load_assets(asset_data)
        super().init_class()


    @classmethod
    def __assets__(cls, asset_data) -> None:
        cls.small_font = assets.SystemFont(FONT_SIZE)
        cls.large_font = assets.SystemFont(FONT_SIZE*2)
        super().__assets__(asset_data)





    def __init__(
            self,
            x: int,
            y: int,
            size: tuple[int, int]
        ) -> None:


        self.rect = p.Rect(x, y, *size)

        self.up: UIElement | None = None
        self.down: UIElement | None = None
        self.right: UIElement | None = None
        self.left: UIElement | None = None
        # These attributes will hold pointers to neighbouring elements.
        # Values will be assigned in the ElementMatrix object.


    @property
    def neighbours(self): # tuple[UIElement | None, UIElement | None, UIElement | None, UIElement | None]
        "Returns the neighboring elements "
        return self.up, self.down, self.left, self.right
    
    @neighbours.setter
    def neighbours(self, value) -> None:
        try:
            self.up, self.down, self.left, self.right = value
        except TypeError:
            raise TypeError(f"Expected tuple length 4 of UIElement | NoneType. Got {type(value).__name__} instead.")


    @property
    def selection_rect(self) -> p.Rect:
        """
        The size and position the bracket of the ElementMatrix object should be
        when it is selecting this element.
        """
        return self.rect
        


    @property
    def text_padding(self) -> p.Vector2:
        "How much the UIElement's texture will be shifted due to any text."
        
        return p.Vector2(0, 0)
    

    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict, mouse_pos: p.Vector2) -> None:
        self.WASD_userinput(action_keys, hold_keys)
        self.mouse_userinput(action_keys, hold_keys, mouse_pos)
        

    def WASD_userinput(self, action_keys: actions_dict, hold_keys: holds_dict):
        if self.is_key_pressed(action_keys, hold_keys, p.K_w):
            return self.up
        if self.is_key_pressed(action_keys, hold_keys, p.K_s):
            return self.down
        if self.is_key_pressed(action_keys, hold_keys, p.K_a):
            return self.left
        if self.is_key_pressed(action_keys, hold_keys, p.K_d):
            return self.right
    

    def mouse_userinput(self, action_keys: actions_dict, hold_keys: holds_dict, mouse_pos: p.Vector2) -> None: pass
    # Will be implemented by subclasses.
        


    def is_key_pressed(self, action_keys: actions_dict, hold_keys: holds_dict, key: int) -> bool:
        return action_keys[key] or hold_keys[key] > self.hold_delay
    


    def draw(self, surface: p.Surface, offset: Coordinate = (0, 0)) -> None: pass
    # Will be implemented by subclasses.







class ElementMatrix(BasicGameElement):
    """
    Arranged UI elements into a graph like structure where the player can
    navigate between elements using WASD keys.

    The class takes a number of list of UIElement objects. One list represents
    a column so multiple lists will form a row of columns side by side.
    """
    TEXTURE_PATH = "ui/ui_elements.png"
    input_delay = 0.12
    # This value effects the speed at which the user can navigate betwen UI elements
    BRACKET_AREAS = (
        (89, 13, 3, 3),
        (93, 13, 3, 3),
        (89, 17, 3, 3),
        (93, 17, 3, 3)
    )

    scroll_sound = "menu_scroll"

    @classmethod
    def init_class(cls, asset_data: dict | None = None) -> None:
        if asset_data is None:
            asset_data = assets.load_class_assets("ui_assets.json")

        cls.load_assets(asset_data)
        super().init_class()
        


    def __init__(self, *elements: list[UIElement], element_seperation: int = 4) -> None:
        self.element_seperation = element_seperation
        self.elements: set[UIElement] = set()

        self.current_element = elements[0][0]
        # The top element in the first column
        
        
        # The following nested for loop takes the tuple of lists from elements and add all the Ui elements
        # from it and puts it into the set self.elements.
        #
        # It also assignes the correct element to each left, right, up and down attribute to each element
        # so that the player can navigate to each element using the WASD keys

        x_offset = self.current_element.rect.x
        for c, column in enumerate(elements):
            y_offset = self.current_element.rect.y # the y coordinate the first element in the column should have
            max_width = 0 # The largest width of an element in the given column
            prev_column = elements[c-1] # Holds the previos column

            for i, element in enumerate(column):
                max_width = max(max_width, element.rect.width)
                element.rect.left = x_offset = max(x_offset, element.rect.left)


                if i != 0:
                    element.up, column[i-1].down = column[i-1], element
                    # Creates a link between the current element and the element above it
                
                element.rect.top = max(y_offset, element.rect.top)
                y_offset = element.rect.top + element.rect.height + self.element_seperation

                if c != 0 and prev_column:
                # This isn't the first column and there is at least one element in the previous column
                    element.left = prev_column[min(i, len(prev_column)-1)]
                    if element.left.right is None:
                        element.left.right = element
                    # Makes a connection between the two elements that are in the same y level
                    # One is from the current column and the other is from the previous column
                    # If the previous column's elements right attribute is not None the connection
                    # is only made to be one way
                

                self.elements.add(element)

            for element in prev_column:
                if element.right is None:
                    element.right = column[-1]
            
            x_offset += max_width + self.element_seperation*3
        
        self.input_timer = Timer(self.input_delay)
        
        self.bracket_rect = self.get_target_bracket()
        # An ElementMatrix object will have a bracket which shows the player what
        # UIElement they have selected. This rect object determins the position
        # and size of the bracket

        self._show_bracket = False
        # The bracket will only show if the ElementMatrix is currently
        # taking user input. Having the bracket shown indicates to the player
        # that they are currently controlling the ElementMatrix.



    def get_target_bracket(self) -> p.Rect:
        "Returns a rect which dictates where the bracket"
        r = self.current_element.selection_rect
        return p.Rect(r.left - 2, r.top - 2, r.width + 1, r.height + 1)



    def userinput(self, action_keys: actions_dict, hold_keys: holds_dict, mouse_pos: p.Vector2) -> None:
        self._show_bracket = True
        # Sets the value to True so that the bracketis shown for the next frame.
        if self.input_timer.complete:
            element_change = self.current_element.WASD_userinput(action_keys, hold_keys)
            if element_change is not None:
                self.current_element = element_change
                self.input_timer.start()
                SoundFX.play(self.scroll_sound)
            else:
                for element in self.elements:
                    element.mouse_userinput(action_keys, hold_keys, mouse_pos)


    

    def update(self, delta_time: float) -> None:
        for element in self.elements:
            element.update(delta_time)

        self.__update_bracket(delta_time)
        self.input_timer.update(delta_time)



    def __update_bracket(self, delta_time: float) -> None:
        """
        Updates the position of the bracket according to the input_timer so
        that creates an animation where the bracket moves smoothly between
        UI elements.
        """

        target = self.get_target_bracket()
        diplacement = target.topleft - p.Vector2(self.bracket_rect.topleft)
        if not self.input_timer.complete and diplacement.magnitude() != 0.0:
            move_amount = self.input_timer.countdown

            velocity = diplacement/move_amount

            width_difference = target.width - self.bracket_rect.width
            width_change = width_difference/move_amount

            height_difference = target.height - self.bracket_rect.height
            height_change = height_difference/move_amount

            self.bracket_rect.topleft += vector_min(velocity*delta_time, diplacement)
            self.bracket_rect.width += min(abs(width_change*delta_time), abs(width_difference))*sign(width_difference)
            self.bracket_rect.height += min(abs(height_change*delta_time), abs(height_difference))*sign(height_difference)


        else:
            self.bracket_rect = target





    def draw(self, surface: p.Surface, offset: Coordinate = (0, 0)) -> None:
        for element in self.elements:
            element.draw(surface, offset)

        if self._show_bracket:
            self.__draw_bracket(surface, p.Vector2(offset))

            # p.draw.rect(surface, "yellow", self.current_element.selection_rect, 2)


            self._show_bracket = False



    def __draw_bracket(self, surface: p.Surface, offset: p.Vector2) -> None:
        "Draws the bracket onto the surface."

        blit_rect = self.bracket_rect.copy()
        blit_rect.center += offset
        bracket_textures = list(self.assets.values())
        surface.blits((
            (bracket_textures[0], blit_rect.topleft),
            (bracket_textures[1], blit_rect.topright),
            (bracket_textures[2], blit_rect.bottomleft),
            (bracket_textures[3], blit_rect.bottomright)
        ))