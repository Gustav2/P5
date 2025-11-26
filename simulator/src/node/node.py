import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from .state import State
from .harvester import Harvester
from ..config import *

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y
        self.state: State = State.Idle

        self.harvester = Harvester(id)
        self.env = env
        self.listen_time = 0

        self.neighbors: dict = {}
        self.clock_drift = random.uniform(*CLOCK_DRIFT_MULTIPLIER_RANGE)

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            self.listen_time = math.ceil(random.uniform(*LISTEN_TIME_RANGE))
            energy_to_use = self.listen_time * E_LISTEN + E_TX + E_RX
            idle_time = self.harvester.time_to_charge_to(energy_to_use, self.local_time())

            yield self.env.timeout(idle_time)
            self.harvester.harvest(idle_time, self.local_time())

            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            if self.harvester.remaining_energy() >= energy_to_use:
                yield self.env.process(self.listen(self.listen_time))
                yield self.env.process(self.transmit())

            self.state = State.Idle

    def listen(self, duration):
        energy_to_use = E_LISTEN * duration

        if self.state != State.Idle or self.harvester.remaining_energy() < energy_to_use:
            return False

        self.state = State.Listen
        self.harvester.discharge(energy_to_use)        
        yield self.env.timeout(duration)
        self.harvester.harvest(duration, self.local_time())
        
        self.state = State.Idle

        return Network.messages_received(self)

    def transmit(self):
        if self.state != State.Idle or self.harvester.remaining_energy() < E_TX:
            return False

        self.state = State.Transmit
        self.harvester.discharge(E_TX)
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME, self.local_time())

        msg = {
            'id': self.id,
            'time': self.local_time(),
        }

        Network.broadcast(self, msg)

        self.state = State.Idle

    def receive(self, msg):
        if self.state != State.Listen or self.harvester.remaining_energy() < E_RX:
            return False
        
        self.state = State.Receive
        self.harvester.discharge(E_RX)
        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME, self.local_time())

        sender = msg['id']
        sender_time = msg['time']
        time_offset = sender_time - self.local_time()

        self.neighbors[sender] = {
            "offset": time_offset,
            "last_meet": self.local_time(),
        }

        self.state = State.Idle

    def local_time(self):
        return math.floor(self.env.now * self.clock_drift)