import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from ..core.state import State
from .harvester import Harvester

from ..config import E_TRESHOLD, E_RX, E_TX, TX_TIME, E_IDLE, DELAY_RANGE, CLOCK_DRIFT_RANGE, WAKEUP_POINT_TRESHOLD, MEETUP_INTERVAL, WAKEUP_RANGE, START_SYNC_AFTER

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y
        self.state: State = State.Off

        self.harvester = Harvester()
        self.env = env
        
        self.neighbors = {}
        self.sync_tries = 0
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

            meeting_in = random.uniform(*WAKEUP_RANGE)
            if self.local_time() >= 86_400:
                soonest_meet = self._soonest_meet()
                if soonest_meet > 0:
                    meeting_in = soonest_meet

            yield self.env.timeout(meeting_in)
            self.harvester.harvest(meeting_in, self.local_time())
            self.harvester.discharge(E_IDLE * meeting_in)
            
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

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        self.state = State.Receive
        yield self.env.timeout(TX_TIME)
        self.harvester.discharge(E_RX)

        sender = msg['id']
        time_ratio = msg['time'] / self.local_time()

        meetings = self.neighbors.get(sender, {}).get("meetings", 0)
        self.neighbors[sender] = {
            "ratio": time_ratio,
            "last_meet": self.local_time(),
            "meetings": meetings + 1 if self.local_time() > START_SYNC_AFTER else meetings
        }

        if self.local_time() > START_SYNC_AFTER:
            self.sync_tries += 1

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
        meeting_point = float('inf')
        meet_in = 0

        for _, neigh in self.neighbors.items():
            adjusted_time = MEETUP_INTERVAL * neigh["ratio"]
            adjusted_meeting_point = neigh["last_meet"] + adjusted_time

            if adjusted_meeting_point < meeting_point:
                meeting_point = adjusted_meeting_point
                meet_in = adjusted_time

        return max(0, meet_in - WAKEUP_POINT_TRESHOLD / 2)