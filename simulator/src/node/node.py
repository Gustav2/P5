import simpy
import random

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from .state import State
from .harvester import Harvester
from ..config import *

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y
        self.state: State = State.Off

        self.harvester = Harvester()
        self.env = env
        
        self.neighbors: dict = {}
        self.sync_tries = 0
        self.clock_drift = random.uniform(*CLOCK_DRIFT_RANGE)

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)

            wakeup_in = random.uniform(*WAKEUP_RANGE)
            soonest_meet = self._soonest_meet()
            if soonest_meet < wakeup_in and soonest_meet > 0:
                wakeup_in = soonest_meet

            yield self.env.timeout(wakeup_in)
            self.harvester.harvest(wakeup_in, self.local_time())
            self.harvester.discharge_idle(wakeup_in)

            self._update_state()

            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)

            if self.harvester.energy > E_TRESHOLD:
                # TODO use agreement instead of random waking point for discoveries and syncs
                heard = yield self.env.process(
                    self.listen(random.uniform(*WAKEUP_RANGE))
                )
                if not heard:
                    # TODO add SYNC message under certain conditions
                    yield self.env.process(self.transmit())
                    yield self.env.process(self.listen(WAKEUP_POINT_TRESHOLD))

    def listen(self, duration):
        available_sec = min(self.harvester.idle_time_available(), duration)
        energy_to_use = E_IDLE * available_sec

        if not self._is_available_for_action(energy_to_use):
            return False

        self.harvester.discharge(energy_to_use)

        yield self.env.timeout(available_sec)
        self._update_state()

        return Network.messages_received(self)

    def transmit(self, msg_type="BEACON"):
        if not self._is_available_for_action(E_TX):
            return

        self.state = State.Transmit
        self.harvester.discharge(E_TX)
        yield self.env.timeout(TX_TIME)

        if msg_type == "SYNC":
            self.sync_tries += 1

        # TODO agree on who sent and who receive
        msg = {
            'type': msg_type,
            'id': self.id,
            'time': self.local_time() + self.clock_drift
        }

        Network.broadcast(self, msg)
        self._update_state()

    def receive(self, msg):
        if not self._is_available_for_action(E_RX):
            return

        self.state = State.Receive
        self.harvester.discharge(E_RX)

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        yield self.env.timeout(TX_TIME)

        msg_type = msg['type']
        sender = msg['id']
        time_offset = msg['time'] - self.local_time() + self.clock_drift

        self.neighbors[sender] = {
            "offset": time_offset,
            "last_meet": self.local_time(),
            # TODO calc the amount of successfull syncs
        }

        if self._soonest_meet(sender) <= SYNC_TRESHOLD and msg_type == "SYNC":
            yield self.env.process(self.transmit("ACK"))

        self._update_state()

    def local_time(self):
        return self.env.now

    def _is_available_for_action(self, required_energy):
        if self.state != State.Idle:
            return False
        return self.harvester.remaining_energy() >= required_energy

    def _update_state(self):
        self.state = State.Idle if self.harvester.energy > E_TRESHOLD else State.Off

    def _soonest_meet(self, node_id = None):
        meeting_point = float('inf')
        meet_in = 0

        for id, neigh in self.neighbors.items():
            adjusted_time = MEETUP_INTERVAL + neigh["offset"]
            adjusted_meeting_point = neigh["last_meet"] + adjusted_time

            if adjusted_meeting_point < meeting_point:
                meeting_point = adjusted_meeting_point
                meet_in = adjusted_time - self.local_time()

            if id == node_id:
                return meet_in

        return max(0, meet_in)