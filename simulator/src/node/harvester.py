import random, math

from ..config import LIGHT_RANGE_LUX, E_MAX, E_IDLE, E_TRESHOLD, SUNRISE_TIME, SUNSET_TIME

class Harvester:
    def __init__(self, initial_energy = 0):
        self.energy = initial_energy
        self.lux = random.uniform(*LIGHT_RANGE_LUX)

    def harvest(self, time, local_time): 
        daytime = local_time % 86_400
        if daytime < SUNRISE_TIME or daytime > SUNSET_TIME:
            return
        
        normalized_time = (daytime - SUNRISE_TIME) / (SUNSET_TIME - SUNRISE_TIME)
        daytime_lux = self.lux * max(0, math.sin(math.pi * normalized_time))

        harvest_rate = max(0, (0.9083 * daytime_lux - 9.2714) / 100_000)
        self.energy = min(self.energy + harvest_rate * time, E_MAX)

    def discharge(self, joules: float):
        if joules > self.remaining_energy():
            raise ValueError("Not enough energy to use")
        self.energy -= joules

    def discharge_idle(self, duration: float):
        self.energy = max(0, self.energy - duration * E_IDLE)

    def idle_time_available(self):
        remaining = self.remaining_energy();
        return 0 if remaining == 0 else math.floor(remaining / E_IDLE)

    def remaining_energy(self):
        return max(0, self.energy - E_TRESHOLD)