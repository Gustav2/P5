import random, math

from ..config import *

class Harvester:
    def __init__(self, id, initial_energy = 0):
        self.energy = initial_energy
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
        harvest_rate = self.harvest_rate()
        if harvest_rate <= 0:
            return ONE_DAY / 24
        return math.ceil((joules - self.remaining_energy()) / harvest_rate)

    def remaining_energy(self):
        return max(0, self.energy - E_TRESHOLD)
    
    def harvest_rate(self):     
        return (0.9083 * self.lux - 9.2714) / 10**6 / 1_000 - E_IDLE 