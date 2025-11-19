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

        self.is_sync = False
        self.pending_sync_with = set()
        self.sync_tries = 0
        self.acks_received = 0
        self.last_beacon = 0
        
        self.neighbors: dict = {}
        self.clock_drift = random.uniform(*CLOCK_DRIFT_RANGE)

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)

            wakeup_in = random.uniform(*WAKEUP_RANGE)
            soonest_meet = self._soonest_meet()

            if soonest_meet < wakeup_in and soonest_meet > 0:
                self.is_sync = True
                wakeup_in = soonest_meet
            else:
                self.is_sync = False
                self.pending_sync_with.clear()

            yield self.env.timeout(wakeup_in)
            self.harvester.harvest(wakeup_in, self.local_time())
            self.harvester.discharge_idle(wakeup_in)

            if self.is_sync:
                closest_id = min(self.neighbors.keys(),
                                key=lambda id: self._soonest_meet(id))
                self.pending_sync_with = {closest_id}

            self._update_state()

            EnergyLogger().log(self.id, self.env.now, self.harvester.energy)

            if self.harvester.energy > E_TRESHOLD:
                heard = yield self.env.process(
                    self.listen(random.uniform(1, WAKEUP_POINT_TRESHOLD))
                )
                if not heard:
                    yield self.env.process(self.transmit("SYNC" if self.is_sync else "BEACON"))
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
        elif msg_type == 'BEACON':
            self.last_beacon = self.local_time();

        msg = {
            'type': msg_type,
            'id': self.id,
            'time': self.local_time() + self.clock_drift,
        }

        if msg_type == "SYNC" or msg_type == "ACK":
            print(msg_type, "Sent", "From:", self.id)

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
        sender_time = msg['time']
        time_offset = sender_time - self.local_time()

        self._update_state()

        # TODO instead of ACK in BEACON, node, who sent, can just wake up around meet up interval, and hope there will be someone 
        if msg_type == "BEACON":
            if sender not in self.neighbors:
                self.neighbors[sender] = {
                    "offset": time_offset,
                    "last_meet": self.local_time(),
                }
                yield self.env.process(self.transmit("BEACON"))
            else:
                meet_in = self._soonest_meet(sender)
                if meet_in <= 0:
                    self.neighbors[sender] = {
                        "offset": time_offset,
                        "last_meet": self.local_time(),
                    }
                    yield self.env.process(self.transmit("BEACON"))

        elif msg_type == "SYNC":
            print("SYNC Received:", self.id, "From:", sender)
            if self.is_sync and sender in self.neighbors:
                time_to_meet = self._soonest_meet(sender)
                # ! Here is an issue, the time_to_meet is too big somehow
                if -SYNC_TRESHOLD <= time_to_meet <= SYNC_TRESHOLD:
                    old_last_meet = self.neighbors[sender]["last_meet"]

                    self.neighbors[sender]["offset"] = time_offset
                    self.neighbors[sender]["last_meet"] = self.local_time()

                    print(sender_time)
                    print(f"  [SYNC] Node {self.id} updated last_meet for {sender}: {old_last_meet} -> {self.local_time()}")

                    yield self.env.process(self.transmit("ACK"))

        elif msg_type == "ACK":
            print("ACK Received:", self.id, "From:", sender)
            if sender in self.pending_sync_with:
                old_last_meet = self.neighbors[sender]["last_meet"]

                self.acks_received += 1
                self.pending_sync_with.remove(sender)
                self.neighbors[sender]["last_meet"] = self.local_time()

                print(f"  [ACK] Node {self.id} updated last_meet for {sender}: {old_last_meet} -> {self.local_time()}")

        self._update_state()

    def local_time(self):
        return self.env.now

    def _is_available_for_action(self, required_energy):
        if self.state != State.Idle:
            return False
        return self.harvester.remaining_energy() >= required_energy

    def _update_state(self):
        self.state = State.Idle if self.harvester.energy > E_TRESHOLD else State.Off

    def _soonest_meet(self, node_id=None):
        meet_in = float('inf')

        for id, neigh in self.neighbors.items():
            adjusted_time = MEETUP_INTERVAL + neigh["offset"]
            adjusted_meeting_point = neigh["last_meet"] + adjusted_time
            current_meet_in = adjusted_meeting_point - self.local_time()

            if node_id == id:
                return max(0, current_meet_in)

            if current_meet_in < meet_in:
                meet_in = current_meet_in
    
        return max(0, meet_in)