import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from ..core.state import State
from .harvester import Harvester

from ..config import E_TRESHOLD, E_RX, E_TX, TX_TIME, E_IDLE, DELAY_RANGE, CLOCK_DRIFT_RANGE, WAKEUP_POINT_TRESHOLD, MEETUP_INTERVAL, WAKEUP_RANGE

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y 
        self.state: State = State.Off

        self.harvester = Harvester()
        self.env = env
        
        self.neighbors = {}
        self.clock_drift = random.uniform(*CLOCK_DRIFT_RANGE)

        env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)
        
            if self.harvester.energy >= E_TRESHOLD:
                heard = yield from self.listen(1)
                if not heard:
                    yield from self.transmit()
                    yield from self.listen(WAKEUP_POINT_TRESHOLD) 

            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)    

            # TODO add E consumption with the same amount as Idle
            soonest_meet = self._soonest_meet()
            meeting_in = soonest_meet if soonest_meet > 0 else random.uniform(*WAKEUP_RANGE)
            yield self.env.timeout(meeting_in)
            self.harvester.harvest(meeting_in)
            
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

        msg = {'id': self.id, 'time': self.local_time() + self.clock_drift}
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
        if sender in self.neighbors:
            meetings = self.neighbors[sender]["meetings"] + 1
            self.neighbors[sender] = {
                "ratio": msg['time'] / self.local_time(),
                "last_meet": self.local_time(),
                "meetings": meetings
            }
        else:
            self.neighbors[sender] = {
                "ratio": msg['time'] / self.local_time(),
                "last_meet": self.local_time(),
                "meetings": 1
            }
            
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

    def _soonest_meet(self):
        meet_in = 0

        if not len(self.neighbors.items()):
            return 0

        for _, neigh in self.neighbors.items():
            meeting_point = neigh["last_meet"] + MEETUP_INTERVAL * neigh["ratio"]
            if meeting_point < meet_in:
                meet_in = meeting_point
        
        return max(0, meet_in - WAKEUP_POINT_TRESHOLD / 2)