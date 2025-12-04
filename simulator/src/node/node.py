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
        self.clock_drift = random.uniform(*CLOCK_DRIFT_MULTIPLIER_RANGE)

        self.neighbors: dict = {}
        self.listen_process = None
        self.is_sync = False
        self.sync_tries = 0
        self.acks_received = 0

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            # Discovery part
            listen_time = math.ceil(random.uniform(*LISTEN_TIME_RANGE))
            energy_to_use = listen_time * E_RECEIVE + E_TX + E_RX

            # Sync part
            energy_for_sync = SYNC_TIME * E_RECEIVE + E_TX + E_RX
            idle_time_for_sync = self.harvester.time_to_charge_to(energy_for_sync, self.local_time())
            sync_in = self.soonest_sync()

            # Pick what's sooner and prioritize
            if sync_in != float('inf') and sync_in - idle_time_for_sync < SYNC_PREPARATION_TIME:
                self.is_sync = True
                listen_time = SYNC_TIME
                energy_to_use = energy_for_sync
                idle_time = sync_in
            else:
                self.is_sync = False
                idle_time = self.harvester.time_to_charge_to(energy_to_use, self.local_time())

            yield self.env.timeout(idle_time)
            self.harvester.harvest(idle_time, self.local_time())

            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            if self.harvester.remaining_energy() >= energy_to_use:
                listen_for = random.uniform(*SYNC_TIME_RANGE) if self.is_sync else (listen_time / 2)
                self.listen_process = self.env.process(self.listen(listen_for))

                heard = True
                try:
                    yield self.listen_process
                    heard = self.listen_process.value
                except simpy.Interrupt:
                    pass
                finally:
                    self.listen_process = None
                
                if not heard:
                    yield self.env.process(self.transmit(Package.SYNC if self.is_sync else Package.DISC))
                    
                    self.listen_process = self.env.process(self.listen(listen_time - listen_for))
                    try:
                        yield self.listen_process
                    except simpy.Interrupt:
                        pass
                    finally:
                        self.listen_process = None

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

        if package_type == Package.SYNC:
            self.sync_tries += 1

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
            if(
                self.neighbors.get(sender) == None or 
                self.soonest_sync(sender) < 0
            ):
                transmit_process = self.env.process(self.transmit(Package.DISC))
                yield transmit_process
                if transmit_process.value:
                    self.neighbors[sender] = {
                        "delay": offset,
                        "last_meet": self.local_time(),
                    }
                    if self.listen_process:
                        self.listen_process.interrupt('discovered')
        elif type == Package.SYNC and sender in self.neighbors:
            time_to_meet = self.soonest_sync(sender)
            if -SYNC_TIME/2 <= time_to_meet <= SYNC_TIME/2:
                transmit_process = self.env.process(self.transmit(Package.ACK))
                yield transmit_process
                if transmit_process.value:
                    self.neighbors[sender] = {
                        "delay": offset,
                        "last_meet": self.local_time(),
                    }
                    if self.listen_process:
                        self.listen_process.interrupt('ack_sent')
        elif type == Package.ACK:
            if -SYNC_TIME/2 < self.soonest_sync(sender) < SYNC_TIME/2:
                self.acks_received += 1
                self.neighbors[sender] = {
                    "delay": offset,
                    "last_meet": self.local_time(),
                }
                if self.listen_process:
                    self.listen_process.interrupt('ack_received')

        return True
    
    def soonest_sync(self, node_id = None):
        meet_in = float('inf')

        for id, neigh in self.neighbors.items():
            current_meet_in = neigh["delay"] + SYNC_INTERVAL - self.local_time()

            if node_id == id:
                return current_meet_in

            if current_meet_in > 0 and current_meet_in < meet_in:
                meet_in = current_meet_in

        return meet_in

    def local_time(self):
        return math.floor(self.env.now * self.clock_drift)