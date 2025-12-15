import random, math

from ..config import *

class Capacitor:
    def __init__(self, id: int):
        self.energy = 0

        if id < LOW_POWERED_NODES:
            self.lux = random.uniform(*LOW_LIGHT_RANGE_LUX)
        else:
            self.lux = random.uniform(*HIGH_LIGHT_RANGE_LUX)
            
    def harvest(self, time):
        self.energy = min(self.energy + self.harvest_rate() * time, E_MAX)

    def discharge(self, joules: float):
        if joules > self.remaining_energy():
            raise ValueError("Not enough energy to use")
        self.energy -= joules

    def time_to_charge_to(self, joules: float):
        if self.remaining_energy() >= joules:
            return 0
        return math.ceil((joules - self.remaining_energy()) / self.harvest_rate())

    def remaining_energy(self):
        return max(0, self.energy - E_TRESHOLD)
    
    def harvest_rate(self):
        # We already include IDLE discrage into harvesting
        harvest_rate = (0.9083 * self.lux - 9.2714) / 10 ** 6 / 1_000
        return harvest_rate