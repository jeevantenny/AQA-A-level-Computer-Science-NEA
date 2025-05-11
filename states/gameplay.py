"Contains the Play state which is the state used for the gameplay."

import pygame as p
from typing import Self

import game_objects.creature_types
import game_objects.enemies
import game_objects.ship

from .state import State
from .transitions import Fade

from audio import Music

import game_objects
from game_objects import enemies, items, ship
from game_objects.camera import Camera
from game_objects.world import Tile, Chunk, ChunkManager
from game_objects.entities import Entity, EntityManager
from game_objects.player import Player
from game_objects.props import CheckPoint

from ui import hud

from settings import keybinds

from file_processing import assets, data, world, load_json
from custom_types.file_representation import EntityData, SaveFile
from custom_types.gameplay import Coordinate

from math_functions import vector_min, unit_vector
from debug import log, STATE_INFO, WARNING, DEBUGGING










class Play(State):
    """
    Shows the Gameplay and allows the player to control the Player object and interact with the world. There are four ways this
    class can be used which will be explained below.
    """

    show_background = False

    save_file: SaveFile | None = None
    save_file_name: str
    timer_played: float

    player: Player | None = None

    _ship_entity: ship.ShipEntity | None = None

    CAMERA_OFFSET = 200

    # For summoning entities in debug mode
    __entity_summon_dict: dict[int, type[Entity]] = {
        p.K_2: enemies.Slime,
        p.K_3: enemies.Stalacsprite
    }
    





    def add_to_stack(self) -> None:
        super().add_to_stack()
        Music.stop()
        # Stops the main theme



    def _basic_init(self, region_name: str, show_rects = DEBUGGING, summon_ship=True) -> None:
        "Sets up attributes for the object and will be called by other initializers (Including the default initializer)"

        super().__init__()
        

        log(STATE_INFO, f"Loading region {region_name}")
        self.region = world.load_region(region_name)
        self.chunks: dict[tuple[int, int], Chunk] = {}
        tile_data = {}

        for file_name in self.region.tile_data:
            tile_data |= data.load_tile_data(file_name)
        
        self.chunk_manager = ChunkManager(self.chunks, self.region.raw_chunks, tile_data)
        
        self.entities = EntityManager(1200, camerashake_callback=self.camerashake)

        game_objects.init(self.entities, self.chunks, 1)


        for id, pos in self.region.checkpoints.items():
            if id != 0:
                CheckPoint(pos, id, self.set_checkpoint)
        
        self.debug_font = assets.DebugFont(16)

        self.camera = None
        self.show_rects = show_rects

        self.death_screen_called = False
        
        self._load_hud()


    
    

    @classmethod
    def init_for_new_save(cls, save_file_name: str) -> Self:
        """
        The first way the Play object can be initialized. This is used when the player starts
        a new save file. The name of the save file is passed in and a new SaveFile object is
        created along with a new Player object. The player will start on the first planet and
        the ship's land method will be called to show the player arriving on a new planet.
        """

        new_save_parameters = load_json("data/create_new_save.json")
        region: str = new_save_parameters["checkpoint_region"]
        checkpoint_id: int = new_save_parameters["checkpoint_id"]

        self = cls.__new__(cls)
        self._basic_init(region)

        self.player = Player(0, 0)
        self.player.snap_to_tile(self.region.checkpoints[0])
        self._load_items()
        self._load_region_entities()

        cls.save_file_name = save_file_name
        cls.save_file = SaveFile(
            region,
            (checkpoint_id, self.player.get_entity_data())
        )

        cls.save_file.add_new_region(region)

        self._summon_ship(self.region.file_name)
        self.player.snap_to_tile(self._ship_entity.get_occupying_tile()+p.Vector2(0, -2))
        self._ship_entity.land()

        return self
    

    



    @classmethod
    def init_from_save(cls, save_file: SaveFile, save_file_name: str) -> Self:
        """
        The second way the Play object can be initialized. The name of the save file and the
        SaveFile object will be passed in as arguments. The relevant entities are loaded into
        the region including the Player and ShipEntity (if needed).
        """

        self = cls.__new__(cls)

        cls.save_file = save_file
        cls.save_file_name = save_file_name


        self._basic_init(self.save_file.current_region)

        log(STATE_INFO, f"Loading checkpoint {self.save_file.last_checkpoint}")
        if self.save_file.use_checkpoint: # If the player should start at a checkpoint
            self.player = Entity.from_save(self.save_file.last_checkpoint[1])
            self.player.snap_to_tile(self.region.checkpoints[self.save_file.last_checkpoint[0]])
            # Summons the Player entity using the EntityData stored in the checkpoint and positions it at
            # the checkpoint

            self.player.velocity *= 0
            self.player.restore_health()
            # Sets the player's velocity to zero and restores their health.

            self._load_region_entities()
            self._load_items()

        else:
            for entity_data in save_file.entities:
                if isinstance(entity := Entity.from_save(entity_data), Player):
                    self.player = entity
            
            self.chunk_manager.broken_tiles = self.save_file.broken_tiles
            # The broken tiles are passed in to ensure they stay broken between play sessions.

            # The methods to lead entities and items are not called because the entity data stored
            # in the save file cover these entities.
        
        if self.player is None:
            raise ValueError(f"Player data not found in save file {save_file_name}.")
        
        cls.save_file.use_checkpoint = False

        if ship.ShipEntity.should_be_in_region(self.region.file_name):
            self._summon_ship(self.region.file_name)

        return self
        


    

    def __init__(self, region_name: str = "cave", player_data: EntityData | None = None, conn_id: int | None = None, show_rects=DEBUGGING) -> None:
        """
        The third way the Play object can be initialized when moving between regions in the same
        planet. This initializer was also used when debugging so when no other arguments are given
        it loads the the region with predetermined player stats and no save file (which may display
        a warning to the console).
        """

        self._basic_init(region_name, show_rects)

        if self.save_file is not None:
            self.save_file.current_region = region_name
            self.save_file.add_new_region(region_name)

        if player_data is None:
            self._summon_debug_player(self.region.checkpoints[0])
        else:
            self.player: Player = Entity.from_save(player_data)
            self.player.snap_to_tile(self.region.connections[conn_id].enter_pos)
            self.entities.add(self.player)
        
        
        self._load_items()
        self._load_region_entities()
        
        if ship.ShipEntity.should_be_in_region(region_name):
            self._summon_ship(region_name)






    @classmethod
    def init_for_new_planet(cls, planet_name: str, player_data: EntityData, show_rects=DEBUGGING) -> Self:
        "Used when the player travels to a new planet."

        try:
            current_landing_site = ship.ShipEntity.landing_sites["sites"][planet_name]
        except KeyError:
            raise ValueError(f"Invalid planet name '{planet_name}'.")
        
        region_name = current_landing_site["region"]

        if cls.save_file is not None:
            cls.save_file.current_region = region_name
            cls.save_file.add_new_region(region_name)


        self = cls.__new__(cls)
        self._basic_init(region_name, show_rects)

        self.player = Entity.from_save(player_data)
        self.entities.add(self.player)

        self._summon_ship(region_name)
        self.player.snap_to_tile(self._ship_entity.get_occupying_tile()+p.Vector2(0, -2))
        self.player.restore_health()

        self._ship_entity.land()
    
        
        self._load_items()
        self._load_region_entities()

        
        return self
    


    def _load_region_entities(self) -> None:
        "Loads entities that are tied to the region (the ones specified in the '.region' file.)"

        for x, y, entity_class in self.region.entities:
            entity_class(0, 0).snap_to_tile((x, y))



    def _load_items(self) -> None:
        """
        Loads 'Collectable' entities that contain items tied to the current region. The function makes sure not to create
        collectables for items the player already has. Each item in the game is given a unique id that is a tuple of the
        name of the region it is in and it's index in the list of items for that region.

        For powerups and weapons, this can be done by checking if the player already has the the item.

        Because players can collect multiple power tanks, the function will check through the player's set of collected
        powertanks to see if the id does not already exist in it.
        """

        for i, (x, y, item_class) in enumerate(self.region.items):
            id = (self.region.file_name, i)
            if issubclass(item_class, items.Item):
                if issubclass(item_class, items.PowerTank):
                    if id not in self.player.collected_powertanks and (self.save_file is None or id not in self.save_file.ship_powertanks):
                        item_class.summon_collectable((x, y), id)
                
                else:
                    if not self.player.has_item(item_class):
                        item_class.summon_collectable((x, y), id)
            
            else:
                raise ValueError(f"Invalid item class '{item_class}' found in region file")



    def _load_hud(self) -> None:
        "Assigns relevant objects to attributes for the Heads up display."

        self.health_bar = hud.HealthBar(7, 7)
        self.tank_indicator = hud.PowerTankIndicator(75, 7)
        self.weapon_mode_indicator = hud.WeaponModeIndicator()



    def _summon_debug_player(self, tile_pos: Coordinate) -> None:
        "Summons the player with pre-acquired powerups for debugging."

        self.player = Player(0, 0)
        self.player.snap_to_tile(tile_pos)
        self.player.acquire_item(items.DoubleJump, ("debug", 0))
        self.player.acquire_item(items.WallJump, ("debug", 1))
        self.player.acquire_item(items.GroundPound, ("debug", 2))
        self.player.acquire_item(items.IonBlaster, ("debug", 3))
        self.player.acquire_item(items.GravitonCleaver, ("debug", 4))



    def _summon_ship(self, region_name: str) -> None:
        """
        Summons the ship in the current region with the powertanks provided. If no
        tanks are provided the ship will it's default amount.
        """

        planet_name = region_name.split('/')[0]
        # Obtains the name of the planet from the region given

        if self.save_file is not None and len(self.save_file.ship_powertanks) != 0:
            tanks = self.save_file.ship_powertanks
        else:
            tanks = None

        self._ship_entity = ship.ShipEntity(planet_name, self.player, self.change_planet, tanks)
        self.__add_ship_collision(self._ship_entity.get_collision_tiles())




        



    def __add_ship_collision(self, tiles: list[tuple[int, int, str]]) -> None:
        "Create tiles that will provide collision for the ShipEntity."

        for x, y, code in tiles:
            chunk_pos = x//Chunk.TILES_PER_SIDE, y//Chunk.TILES_PER_SIDE
            tile_pos = x%Chunk.TILES_PER_SIDE, y%Chunk.TILES_PER_SIDE
            self.chunk_manager.add_tile(chunk_pos, tile_pos, code)



    def __acquire_test_tanks(self) -> None:
        "Gives the player 10 powertanks. Used for debugging."

        for i in range(10):
            self.player.acquire_item(items.PowerTank, (i, "test"))




    def change_planet(self, planet_name: str) -> None:
        "Changes the planet the player is currently playing on."
        if self.save_file is not None:
            self.update_save_file()
        self.state_stack.reset(Play.init_for_new_planet(planet_name, self.player.get_entity_data()), transition=Fade(1.5))

    
    def _is_changing_planets(self) -> bool:
        "Checks if the player is still in between changing planets by checking if the ship is in the idle state."

        return self._ship_entity is not None and self._ship_entity.state != ship.IDLE



    def camerashake(self, duration=1, intensity=3, direction=p.Vector2(0, 1)) -> None:
        if self.camera is not None:
            self.camera.camerashake(duration, intensity, direction)

        


    
    def userinput(self, action_keys, hold_keys) -> None:
        if hold_keys[p.K_LCTRL] and DEBUGGING: # Actions used for debugging
            if action_keys[p.K_r]: # Reset Player object position
                self.player.restore_health()
                self.player.snap_to_tile(self.region.checkpoints[0])
                    
            if action_keys[p.K_k]: # Kill Player object
                self.player.kill()

            if hold_keys[p.K_t] and action_keys[p.K_a]: # Teleport all entities to (200, 200)
                for entity in self.entities:
                    if isinstance(entity, game_objects.creature_types.Creature):
                        entity.teleport((200, 200))

            if action_keys[p.K_g]: # Toggle hit-boxes
                self.show_rects = not self.show_rects
        else:
            if action_keys[p.K_ESCAPE]: # Pause game
                from .gameplay_menus import PauseMenu
                PauseMenu().add_to_stack()

            
            if self._is_changing_planets():
                return None
            
            # The Following actions shouldn't be possible if the player is changing planets


            elif action_keys[keybinds.toggle_map]: # Open region map
                from .gameplay_menus import RegionMap
                RegionMap(self.region.mapdata.map_name, self.player.get_occupying_tile(), self.region.mapdata.map_offset).add_to_stack()


                
            if DEBUGGING: # Only when Debugging
                if action_keys[p.K_t]: # Used to test new features
                    # self.save_file.increment_time_played(2000)
                    self.__acquire_test_tanks()

                if hold_keys[p.K_p]: # Summon enemies at player position
                    for key, entity_cls in self.__entity_summon_dict.items():
                        if action_keys[key]:
                            entity_cls(*self.player.position)
                            break


                if action_keys[p.K_u]: # Take off to Planet Arenis
                    self._ship_entity.take_off("arenis")

        
            self.player.userinput(action_keys, hold_keys)
            # Processes the userinput for the Player object


    def update(self, delta_time: float) -> None:
        self.chunk_manager.update(self.player.position)
        # Update Tiles and Chunks
        
        self.entities.update(delta_time, self.player.position)
        # Update entities
        
        if self.camera is not None:
            self.camera.update(self.__get_camera_target(), delta_time, self.region.camera.boundary)
            # Update camera



        self._should_change_region()
        # Calls a new play state if the player moves to a new region

        if not (self.player.alive or self.death_screen_called):
            self._game_over()


        if self.save_file is not None:
            self.save_file.increment_time_played(delta_time)




    def __get_camera_target(self) -> None:
        "Returns what the camera's target position should be."
        
        if self._is_changing_planets():
            target_pos = self._ship_entity.position
            if self._ship_entity.state == ship.TAKE_OFF:
                target_pos += (0, -200)

        else:
            target_pos = self.player.position
            target_pos += vector_min(unit_vector(self.player.velocity)*self.CAMERA_OFFSET, self.player.velocity*0.05) + (0, -100)

        return target_pos



    

    def _should_change_region(self) -> bool:
        "Checks if the Player object moves into any region connections and change to that region if this is the case."

        for conn in self.region.connections.values():
            if self.player.rect.colliderect(conn.rect):
                self.state_stack.reset(
                    Play(conn.connecting_region, self.player.get_entity_data(), conn.connection_id, self.show_rects),
                    transition=Fade(1.5)
                )
                return True
        
        return False


    def draw(self, surface: p.Surface) -> str:
        # the camera has to be initialized in the draw method because it needs the window surface as one of the initialization arguments
        if self.camera is None:
            self.camera = Camera(surface, self.__get_camera_target(), max_target_offset=(500, 500), area_size=self.region.camera.area_size)


        # Draw all game objects using the camera
        exclude_entity_types = []
        if self._is_changing_planets() and self.player is not None:
            exclude_entity_types.append(type(self.player))
        
        self.camera.capture(
            self.chunk_manager,
            self.entities,
            self.region.background_color,
            show_rects=self.show_rects,
            show_health=DEBUGGING,
            other_rects=[conn.rect for conn in self.region.connections.values()],
            exclude_entity_types=exclude_entity_types
        )



        # Draw the heads-up display
        if self.state_stack[-1] is self:
            self.health_bar.draw(surface, health_amount=self.player.health/type(self.player).health)
            self.tank_indicator.draw(surface, len(self.player.collected_powertanks))
            if self.player.weapons[1]:
                self.weapon_mode_indicator.draw(surface, self.player.weapon_mode)





        # Text to show at the top of the screen when in debug mode
        game_time = self.save_file.hours_played if self.save_file is not None else 0.0
        return f"game time: {game_time:.5f}, region: {self.region.file_name}, chunks loaded: {len(self.chunks)}, entity count: {len(self.entities)}, player position: {self.player.position}"
    










    def set_checkpoint(self, id: int) -> None:
        "Saves the progress for a checkpoint."

        if self.save_file is not None:
            self.save_file.set_checkpoint(id, self.player.get_entity_data())
            log(STATE_INFO, f"Checkpoint set(region: {self.region.file_name}, id: {id})")


    


    def _game_over(self) -> None:
        """
        Called GameOverScreen State and reverts the player progress to
        the last checkpoint.
        """

        from .gameplay_menus import GameOverScreen

        GameOverScreen().add_to_stack()
        if self.save_file is not None:
            self.save_file.revert_to_checkpoint()
            self.update_save_file()
        
        self.death_screen_called = True




    def update_save_file(self) -> None:
        """
        Updates the entities, broken_tiles and use_checkpoint attribute of the current SaveFile, if the player character
        has not died. If the player character has died, use_checkpoint will be set to True so that the player can continue
        at their previos checkpoint.

        The SaveFile object is then stored into a file using data.save_file.

        This method should not be called if the Play object does not have a save file.
        """

        if not self.save_file.use_checkpoint:
            self.save_file.entities = self.entities.get_entity_data([CheckPoint])
            self.save_file.broken_tiles = self.chunk_manager.broken_tiles
            if self._ship_entity is not None:
                self.save_file.ship_powertanks = self._ship_entity._powertanks
        

        data.save_data(self.save_file, self.save_file_name)
        log(STATE_INFO, f"Progress saved to save file '{self.save_file_name}'")




    def quit(self) -> None:
        if self.save_file is not None:
            if not self.death_screen_called:
                self.update_save_file()
        else:
            log(WARNING, "Save file not found")