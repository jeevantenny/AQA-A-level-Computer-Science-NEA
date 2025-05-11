import pygame as p

from .state import State
from file_processing.assets import load_texture
from test_file import true_blur, blur


class BlurState(State):
    def __init__(self) -> None:
        super().__init__()
        intensity = 5
        self.w = 240
        self.image = p.transform.scale(load_texture("game_objects/tiles/steel_frame.png"), (self.w, self.w))
        self.blurred = true_blur(self.image, intensity)
        self.blurred2 = blur(self.image, intensity)
    


    def draw(self, surface: p.Surface):
        surface.blit(self.blurred, (100, 100))
        surface.blit(self.image, (100 + self.w, 100))
        surface.blit(self.blurred2, (100 + self.w*2, 100))