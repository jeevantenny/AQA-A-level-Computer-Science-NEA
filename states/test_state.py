import pygame as p
from math import sin, pi

from .state import State
from ui import UI_SCALE_VALUE, FONT_SIZE, format_text

from file_processing import assets
from file_processing.assets import load_texture, set_stretchable_texture





class TestState(State):
    def __init__(self) -> None:
        super().__init__()

        self.guidline = p.Surface((41, 2))
        
        self.text_box = p.transform.scale_by(format_text("This is the test text for today. Thank you. So this NEA thing might have been a bit bigger than I anticipated. I hope i can finish it. This has literally become my life's work!", assets.SystemFont(8), 100, 2, "black"), 5)

        color = True

        for y in range(2):
            for x in range(41):
                self.guidline.set_at((x, y), (255*color, )*3)
                color = not color
        
        self.guidline = p.transform.scale_by(self.guidline, UI_SCALE_VALUE*2)

        self.text_surface1 = assets.SystemFont(FONT_SIZE*UI_SCALE_VALUE*2).render("The big dog JUMPED... idk", False, "black")
        self.text_surface2 = p.font.Font("assets/fonts/DePixelHalbfett.ttf", 8*UI_SCALE_VALUE*2).render("The big dog JUMPED... idk", False, "black")
    


    def draw(self, surface: p.Surface):
        surface.fill("grey")

        surface.fill("white", (0, 0, 500, 500))
        surface.blit(self.text_box, (0, 0))


        