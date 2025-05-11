import pygame as p
from typing import Callable

from .world import Tile
from .entities import Entity



class Interactable:
    "Something the player can interact with and perform an action when they do."

    draw_level = -1
    # Interactables should be drawn behind regular entities.

    def __init__(self, interact_text: str, interact_action: Callable[[], None]) -> None:
        self.text = interact_text
        self.interact_action = interact_action



    def player_interact(self) -> None:
        self.interact_action()



class CheckPoint(Entity, Interactable):
    "Allows the player to update the Checkpoint progress at various locations in the world."

    hitbox = (48, 144)
    draw_level = -1

    uninteracted_texture: p.Surface
    interacted_texture: p.Surface
    
    def __init__(self, tile_pos: tuple[int, int], checkpoint_id: int, checkpoint_set_callback: Callable[[int], None]) -> None:
        self.interacted = False
        self.id = checkpoint_id

        Entity.__init__(self, 0, 0, self.hitbox, self.uninteracted_texture)
        Interactable.__init__(self, "Set Checkpoint", checkpoint_set_callback)
        # I had to manually set the __init__ functions otherwise the method resolution order will
        # cause problems.

        self.snap_to_tile(tile_pos)



    def player_interact(self) -> None:
        if not self.interacted:
            self.interact_action(self.id)
            self.interacted = True
            self.texture = self.interacted_texture