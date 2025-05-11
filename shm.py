import pygame as p
from math import cos, pi, asin
from math_functions import sign

from states import State
from game_objects.entities import Entity
from file_processing.assets import DebugFont


Entity.init_class([])



class SHMState(State):
    def __init__(self):
        super().__init__()

        self.pendulum = Pendulum(400, 100, 50, 50, Bob(200, 200))

        self.font = DebugFont(24)


    def update(self, delta_time):
        self.pendulum.x = p.display.get_window_size()[0]//2
        self.pendulum.update(delta_time)


    def draw(self, surface):
        surface.fill((200, 200, 200))
        self.pendulum.draw(surface)

        data_scale = 0.1

        data_list = {
            "Length": self.pendulum.length*data_scale,
            "Amplitude": self.pendulum.amplitude*data_scale,
            "Angular Frequancy": self.pendulum.angular_frequancy,
            "Displacement": self.pendulum.displacement*data_scale,
            "Velocity": self.pendulum.velocity*data_scale,
            "Acceleration": self.pendulum.acceleration*data_scale
        }


        for i, (name, data) in enumerate(data_list.items()):
            surface.blit(self.font.render(f"{name}: {data:.2f}", True, "black"), (50, 70 + 25*i))






class Bob(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (200, 200), p.Surface((200, 200)))

        self.raduis = 20
        self.mass = 20




    
    def draw(self, surface, offset = (0, 0)):
        p.draw.circle(surface, (100, 100, 25), self.position + offset, self.raduis)





class Pendulum:
    def __init__(self, x: int, y: int, length: int, amplitude: int, bob: Bob):
        self.x = x
        self.y = y
        self.length = length
        self.amplitude = amplitude
        self.bob = bob

        # self.bob.rect.center = self.position + self.direction*self.length

        self.time_passed = 0.0


    @property
    def angular_frequancy(self):
        return (2000/self.length)**0.5


    @property
    def displacement(self):
        return self.amplitude*cos(self.time_passed*self.angular_frequancy)
    


    @property
    def velocity(self):
        return self.angular_frequancy*(self.amplitude**2 - self.displacement**2)**0.5
    

    @property
    def acceleration(self):
        return -(self.angular_frequancy**2)*self.displacement
    

    @property
    def direction(self):
        return asin(self.displacement/self.length)
    

    @property
    def direction_v(self):
        vector = p.Vector2(0, 1)
        vector.rotate_ip(self.direction*(180/pi))
        return vector



    @property
    def position(self):
        return p.Vector2(self.x, self.y)


    def update(self, delta_time: float):
        self.time_passed += delta_time

        self.bob.rect.center = self.position + self.length*self.direction_v

        self.length += 20*delta_time

        








    
    def draw(self, surface: p.Surface):
        p.draw.line(surface, "black", self.position, self.bob.position, 5)
        p.draw.rect(surface, "black", (self.x - 10, self.y - 10, 20, 10))
        self.bob.draw(surface)