import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from .state import State
from .harvester import Harvester
from .kpi import KPI
from ..config import *

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y
        self.state: State = State.Idle

        self.clock_drift = random.randint(*NODE_START_TIMES)

        self.kpi = KPI()

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
            energy_to_use = self.listen_time * E_RECEIVE + E_TX + E_RX
            idle_time = self.harvester.time_to_charge_to(energy_to_use, self.local_time())

            yield self.env.timeout(idle_time)
            self.harvester.harvest(idle_time, self.local_time())

            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            if self.harvester.remaining_energy() >= energy_to_use:
                self.kpi.start_discovery(self.local_time())
                yield self.env.process(self.listen(self.listen_time))
                yield self.env.process(self.transmit())
                self.kpi.send_discovery(self.listen_time)

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
        self.kpi.add_e(energy_to_use)

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

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        Network.broadcast(self, msg)

        self.kpi.add_e(E_TX)
        self.state = State.Idle

    def receive(self, msg):
        if self.state != State.Receive or self.harvester.remaining_energy() < E_RX:
            return False
        
        self.harvester.discharge(E_RX)
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME, self.local_time())

        sender = msg['id']
        sender_time = msg['time']
        time_offset = sender_time - self.local_time()

        self.neighbors[sender] = {
            "offset": time_offset,
            "last_meet": self.local_time(),
        }
        self.kpi.receive_discovery(self.listen_time, self.local_time())

        self.kpi.add_e(E_RX)
        self.state = State.Receive

    def update_clock_drift(self):
        self.clock_drift += random.randint(0, CLOCK_DRIFT_PER_DAY)

    def local_time(self):
        if CLOCK_DRIFT_ENABLED:
            #print(math.floor(self.env.now + self.clock_drift))
            return math.floor(self.env.now + self.clock_drift)
        else:
            return math.floor(self.env.now)