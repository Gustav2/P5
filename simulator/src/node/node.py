import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from ..core.state import State
from .harvester import Harvester

from ..config import E_TRESHOLD, E_RX, E_TX, TX_TIME, E_IDLE, DELAY_RANGE

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y 
        self.state: State = State.Off
        self.harvester = Harvester()
        self.env = env
        self.neighbors = {}
        # TODO add random clock drift

        env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)
        
            if self.harvester.energy >= E_TRESHOLD:
                heard = yield from self.listen(1)
                if not heard:
                    yield from self.transmit()
                    yield from self.listen(5) 

            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)    

            sleep_time = random.uniform(1, 20)
            self.state = State.Off
            yield self.env.timeout(sleep_time)

            self.harvester.harvest(sleep_time)
            self._update_state()

    def listen(self, duration):
        available_sec = min(self.harvester.idle_time_available(), duration);
        energy_to_use = E_IDLE * available_sec
    
        if not self._is_available_for_action(energy_to_use):
            return False

        yield self.env.timeout(available_sec)
        self.harvester.discharge(energy_to_use)

        self._update_state()
        return Network().messages_received(self)

    def transmit(self):
        if not self._is_available_for_action(E_TX):
            return

        self.state = State.Transmit

        yield self.env.timeout(TX_TIME)
        self.harvester.discharge(E_TX)

        msg = {'type': 'BEACON', 'id': self.id, 'time': self.local_time()}
        Network().broadcast(self, msg)

        self._update_state()

    def receive(self, msg):
        if not self._is_available_for_action(E_RX):
            return
        
        delay = random.uniform(*DELAY_RANGE)
        yield self.env.timeout(delay)

        self.state = State.Receive
        yield self.env.timeout(TX_TIME)
        self.harvester.discharge(E_RX)

        sender = msg['id']
        offset_est = msg['time'] - self.local_time()
        self.neighbors[sender] = offset_est
        # TODO calc offset in time for sleeping

        self._update_state()

    def local_time(self):
        return self.env.now

    def distance(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)
    
    def _is_available_for_action(self, required_energy):
        if self.state != State.Idle:
            return False

        if self.harvester.remaining_energy() < required_energy:
            return False
        
        return True

    def _update_state(self):
        self.state = State.Idle if self.harvester.energy > E_TRESHOLD else State.Off