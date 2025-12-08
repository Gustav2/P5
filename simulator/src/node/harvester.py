import random, math

from ..config import *

class Harvester:
    def __init__(self, id, initial_energy = 0):
        self.energy = initial_energy
        
        self.rng = random.Random(SEED)
        if id < LOW_POWERED_NODES:
            self.lux = self.rng.uniform(*LOW_LIGHT_RANGE_LUX)
        else:
            self.lux = self.rng.uniform(*HIGH_LIGHT_RANGE_LUX)

        #random.seed(SEED)
        #if id < LOW_POWERED_NODES:
        #    self.lux = random.uniform(*LOW_LIGHT_RANGE_LUX)
        #else:
        #    self.lux = random.uniform(*HIGH_LIGHT_RANGE_LUX)
            
    def harvest(self, time, local_time):
        self.energy = min(self.energy + self.harvest_rate(local_time) * time, E_MAX)

    def discharge(self, joules: float):
        if joules > self.remaining_energy():
            raise ValueError("Not enough energy to use")
        self.energy -= joules

    def time_to_charge_to(self, joules: float, local_time):
        if self.remaining_energy() >= joules:
            return 0
        harvest_rate = self.harvest_rate(local_time)
        if harvest_rate <= 0:
            return ONE_DAY / 24
        return math.ceil((joules - self.remaining_energy()) / harvest_rate)

    def remaining_energy(self):
        return max(0, self.energy - E_TRESHOLD)
    
    def harvest_rate(self, local_time):
        daytime_lux = self.lux

        if IS_DAY_CYCLE:
            daytime = local_time % 86_400
            if daytime < SUNRISE_TIME or daytime > SUNSET_TIME:
                return 0
            
            normalized_time = (daytime - SUNRISE_TIME) / (SUNSET_TIME - SUNRISE_TIME)
            daytime_lux = self.lux * max(0, math.sin(math.pi * normalized_time))

        # We already include IDLE discrage into harvesting
        harvest_rate = (0.9083 * daytime_lux - 9.2714) / 100_000 / 1_000 - E_IDLE
        
        return harvest_rate