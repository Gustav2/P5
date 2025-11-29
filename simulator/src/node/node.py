import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from .state import State, Package
from .harvester import Harvester
from ..config import *

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y
        self.state: State = State.Idle

        self.harvester = Harvester(id)
        self.env = env

        self.neighbors: dict = {}
        self.clock_drift = random.uniform(*CLOCK_DRIFT_MULTIPLIER_RANGE)

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            listen_time = math.ceil(random.uniform(*LISTEN_TIME_RANGE))
            energy_to_use = listen_time * E_RECEIVE + E_TX + E_RX
            idle_time = self.harvester.time_to_charge_to(energy_to_use, self.local_time())

            yield self.env.timeout(idle_time)
            self.harvester.harvest(idle_time, self.local_time())

            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            if self.harvester.remaining_energy() >= energy_to_use:
                listen_process = self.env.process(self.listen(listen_time / 2))
                yield listen_process
                heard = listen_process.value
                if not heard:
                    yield self.env.process(self.transmit(Package.DISC))
                    yield self.env.process(self.listen(listen_time / 2))

            self.state = State.Idle

    def listen(self, duration):
        energy_to_use = E_RECEIVE * duration

        if self.state != State.Idle or self.harvester.remaining_energy() < energy_to_use:
            return False

        self.state = State.Receive
        self.harvester.discharge(energy_to_use)        
        yield self.env.timeout(duration)
        self.harvester.harvest(duration, self.local_time())
        
        self.state = State.Idle

        return Network.messages_received(self)

    def transmit(self, package_type: Package):
        if self.harvester.remaining_energy() < E_TX:
            return False

        self.state = State.Transmit
        self.harvester.discharge(E_TX)
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME, self.local_time())

        msg = {
            'type': package_type, 
            'id': self.id,
            'time': self.local_time(),
        }

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        Network.broadcast(self, msg)

        return True

    def receive(self, msg):
        if self.state != State.Receive or self.harvester.remaining_energy() < E_RX:
            return False
        
        self.harvester.discharge(E_RX)
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME, self.local_time())

        type = Package(msg['type'])
        sender = msg['id']
        sender_time = msg['time']
        offset = math.floor((sender_time + self.local_time()) / 2)

        if type == Package.DISC:
            neighbor = self.neighbors.get(sender)
            last_meet = self.local_time() if neighbor == None else neighbor['last_meet']

            if(
                neighbor == None or 
                last_meet + SYNC_INTERVAL <= self.local_time()
            ):
                transmit_process = self.env.process(self.transmit(Package.DISC))
                yield transmit_process
                if transmit_process.value:
                    self.neighbors[sender] = {
                        "next_meet": offset + SYNC_INTERVAL,
                        "last_meet": self.local_time(),
                    }

        return True

    def local_time(self):
        return math.floor(self.env.now * self.clock_drift)