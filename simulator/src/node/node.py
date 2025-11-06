import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from ..core.state import State
from .harvester import Harvester

from ..config import *

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
            if self.local_time() >= START_SYNC_AFTER:
                soonest_meet = self._soonest_meet()
                if soonest_meet > 0:
                    meeting_in = soonest_meet

            yield self.env.timeout(meeting_in)
            self.harvester.harvest(meeting_in, self.local_time())
            self.harvester.discharge_idle(meeting_in)
            
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

        self.harvester.discharge(E_TX)
        yield self.env.timeout(TX_TIME)

        msg = {'id': self.id, 'time': self.local_time() + self.clock_drift}
        Network().broadcast(self, msg)

        if self.local_time() >= START_SYNC_AFTER:
            self.sync_tries += 1

        self._update_state()

    def receive(self, msg):
        if not self._is_available_for_action(E_RX):
            return

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        self.harvester.discharge(E_RX)
        self.state = State.Receive
        yield self.env.timeout(TX_TIME)
        
        sender = msg['id']
        time_offset = msg['time'] - self.local_time()

        meetings = self.neighbors.get(sender, {}).get("meetings", 1)
        self.neighbors[sender] = {
            "offset": time_offset,
            "last_meet": self.local_time(),
            "meetings": meetings + 1 if self.local_time() > START_SYNC_AFTER else meetings
        }

        if meetings % 2 == 0 and self.local_time() >= START_SYNC_AFTER:
            yield from self.transmit()

        self._update_state()

    def local_time(self):
        return self.env.now
    
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
            adjusted_time = MEETUP_INTERVAL + neigh["offset"]
            adjusted_meeting_point = neigh["last_meet"] + adjusted_time

            if adjusted_meeting_point < meeting_point:
                meeting_point = adjusted_meeting_point
                meet_in = adjusted_time

        return max(0, meet_in - WAKEUP_POINT_TRESHOLD / 2)