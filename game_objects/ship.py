import pygame as p
from typing import Callable, Any
from math import sin, pi

from custom_types.file_representation import EntityData

from .entities import AnimatedEntity
from .world import Tile
from .player import Player

from custom_types.base_classes import BasicGameElement
from custom_types.gameplay import Timer

from file_processing import assets



# The three states the ShipEntity can be in
IDLE = 0
TAKE_OFF = 1
LANDING = 2

class ShipEntity(AnimatedEntity):
    """
    This entity allows the player to travel between planets.
    """

    hitbox = (144, 30)
    # Small compared to the ships's sprite.
    # This hitbox will be used to control the opening of the ship's navigation menu
    player_detect_area = (16, 16)
    always_update = True
    draw_level = 5
    
    take_off_height = 6000
    take_off_time = 4.5
    land_time = 8.5
    bob_period = 3.5
    bob_offset = 5

    landing_sites: dict

    def __init__(
            self,
            planet_name: str,
            player: Player,
            change_planet_callback: Callable[[str], None],
            tanks: set[tuple[int, int]] | None = None,
        ) -> None:
        self._planet = planet_name

        try:
            super().__init__(0, 0, self.hitbox, self.texture_map, self.animation_data, None)
            self.snap_to_tile(tuple(self.landing_sites["sites"][self._planet]["position"]))
            self.landing_site_pos = self.position
        
        except KeyError:
            raise ValueError(f"Invalid planet name '{planet_name}'")
        
        self._change_planet = change_planet_callback

        self.movement_timer = Timer(self.take_off_time)
        # Controls the speed of take off and landing

        self.state = IDLE
        self.can_open_menu = False

        self.bob_timer = Timer(self.bob_period, True).start()

        self._player = player

        if tanks is None:
            self._powertanks: set[tuple[str, int]] = set(
                [
                    (1, "built_in"),
                    (2, "built_in")
                ]
            )

        else:
            self._powertanks = tanks.copy()

        self._destination: str | None = None


    @property
    def player_detect_rect(self) -> p.Rect:
        """
        The area in which the player must be out of in order for them to open
        the ship's navigation menu again.
        """

        rect = p.Rect(0, 0, *p.Vector2(self.player_detect_area)*Tile.SIZE)
        rect.center = self.position
        return rect


    def update(self, delta_time) -> None:
        super().update(delta_time)
        self.movement_timer.update(delta_time)

        match self.state:
            case 0: # IDLE
                self.bob_timer.update(delta_time)
                self.position = self.landing_site_pos
                
                if not self._player.rect.colliderect(self.player_detect_rect):
                    self.can_open_menu = True
                
                if self.can_open_menu:
                    if self.rect.colliderect(self._player.rect):
                        from states.gameplay_menus import ShipNavigationMenu
                        ShipNavigationMenu(self, self._player.collected_powertanks, self._planet).add_to_stack()
                        self.can_open_menu = False
                        # When the player collides with the ships 
            
            case 1: # TAKE_OFF
                self.position = self.landing_site_pos[0], self.landing_site_pos[1]-self.take_off_height*(self.movement_timer.completion_amount**2)
                if self.movement_timer.complete:
                    self._change_planet(self._destination)
                    # When the ship has finished taking off the new Play state will be loaded for the new planet

            case 2: # LANDING
                self.position = self.landing_site_pos[0], self.landing_site_pos[1]-self.take_off_height*((1-self.movement_timer.completion_amount)**4)
                if self.movement_timer.complete:
                    self.can_open_menu = False
                    # This is to ensure the ship's navigation menu doesn't immediatly open after landing

                    

        if self.movement_timer.complete:
            self.state = IDLE


    def draw(self, surface, offset=(0, 0), alpha=255) -> None:
        bob_offset = p.Vector2(0, self.bob_offset*sin(self.bob_timer.completion_amount*2*pi))
        return super().draw(surface, offset+bob_offset, alpha)
    


    def get_tanks_from_player(self) -> None:
        "Takes the powertanks collected by the player and adds them to the ship."

        for tank_id in self._player.collected_powertanks:
            self._powertanks.add(tank_id)
        
        self._player.collected_powertanks.clear()

    

    def take_off(self, destination: str) -> None:
        if destination in self.landing_sites["sites"] and destination != self._planet:
            self._destination = destination
            self.state = TAKE_OFF
            self.movement_timer.duration = self.take_off_time
            self.movement_timer.start()

        else:
            raise ValueError(f"Invalid destination name '{destination}'")



    def land(self) -> None:
        self.state = LANDING
        self.movement_timer.duration = self.land_time
        self.movement_timer.start()
        
    @classmethod
    def should_be_in_region(cls, region_name: str) -> bool:
        "Returns True if the ship should be summoned in the given region."

        for site_data in cls.landing_sites["sites"].values():
            if site_data["region"] == region_name:
                return True
            
        return False
    


    def get_collision_tiles(self) -> list[tuple[int, int, str]]:
        """
        Gets the position and type of the tiles that make up the ship's hitbox.

        The player will need to stand on top of and inside the ship and a recgular entity
        hitbox won't work. So the shape of the ship will be approximated with different
        types of tiles.

        The tile codes used will be in the general tile data json file.
        """

        tiles = []

        ship_x, ship_y = self.get_occupying_tile()

        for x, y, tile_code in self.landing_sites["collision_tiles"]:
            tiles.append((ship_x+x, ship_y+y, tile_code))
        
        return tiles