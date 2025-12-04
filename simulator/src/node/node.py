import simpy, random, math

from ..core.network import Network
from .state import State, Package
from .capacitor import Capacitor
from ..core.energy_logger import EnergyLogger

from ..config import *

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float):
        self.id = id
        self.x, self.y = x, y
        self.env = env

        self.state: State = State.Idle
        self.capacitor = Capacitor(id)
        self.clock_drift = random.uniform(*CLOCK_DRIFT_MULTIPLIER_RANGE)

        self.neighbors: dict = {}
        self.sync_cycles = []
        self.sync_with = []

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger.log(self.id, self.local_time(), self.capacitor.energy)

            # Discovery part
            listen_time = math.ceil(random.uniform(*LISTEN_TIME_RANGE))
            energy_to_use = listen_time * E_RECEIVE + E_TX + E_RX

            # Sync part
            energy_for_sync = SYNC_TIME * E_RECEIVE + E_TX + E_RX
            idle_time_for_sync = self.capacitor.time_to_charge_to(energy_for_sync)
            sync_in = self.soonest_sync()

            is_sync = False

            # Pick what's sooner and prioritize
            if sync_in != float('inf') and 0 < sync_in - idle_time_for_sync < SYNC_PREPARATION_TIME:
                is_sync = True
                listen_time = SYNC_TIME
                energy_to_use = energy_for_sync
                idle_time = sync_in
            else:
                idle_time = self.capacitor.time_to_charge_to(energy_to_use)

            yield self.env.timeout(idle_time)
            self.capacitor.harvest(idle_time)

            EnergyLogger.log(self.id, self.local_time(), self.capacitor.energy)

            if self.capacitor.remaining_energy() >= energy_to_use:
                listen_for = random.uniform(*SYNC_TIME_RANGE) if is_sync else (listen_time / 2)
                listen_process = self.env.process(self.listen(listen_for))
                yield listen_process

                messages = listen_process.value
                heard = len(messages) > 0 # type: ignore

                if is_sync:
                    self.update_upcoming_sync_nodes()
                    sync_partners = set(self.sync_with)
                    self.sync_cycles.append({
                        "nodes": len(sync_partners), 
                        "sync_received": 0, 
                        "acks_received": 0
                    })

                    for msg in messages: # type: ignore
                        if msg['from'] in sync_partners and msg['type'] in (Package.ACK, Package.SYNC):
                            heard = True
                            break
                    heard = False

                if not heard:
                    yield self.env.process(self.transmit(
                        Package.SYNC if is_sync else Package.DISC, self.sync_with[0] if is_sync else None
                    ))
                    yield self.env.process(self.listen(listen_time - listen_for))

            self.sync_with = []
            self.state = State.Idle

    def listen(self, duration):
        remaining_energy = self.capacitor.remaining_energy()
        available_time = min(math.floor(remaining_energy / E_RECEIVE), duration)
        energy_to_use = available_time * E_RECEIVE

        if self.state != State.Idle or remaining_energy < energy_to_use:
            return []

        self.state = State.Receive
        self.capacitor.discharge(energy_to_use)        
        yield self.env.timeout(duration)
        self.capacitor.harvest(duration)
        
        self.state = State.Idle

        return Network.messages_received(self)

    def transmit(self, package_type: Package, to):
        if self.capacitor.remaining_energy() < E_TX:
            return False

        self.state = State.Transmit
        self.capacitor.discharge(E_TX)
        yield self.env.timeout(PT_TIME)
        self.capacitor.harvest(PT_TIME)

        msg = {
            'type': package_type, 
            'from': self.id,
            'to': to,
            'time': self.local_time(),
        }

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        Network.broadcast(self, msg)

        return True

    def receive(self, msg):
        if self.state != State.Receive or self.capacitor.remaining_energy() < E_RX:
            return False
            
        self.capacitor.discharge(E_RX)
        yield self.env.timeout(PT_TIME)
        self.capacitor.harvest(PT_TIME)

        type = Package(msg['type'])
        sender = msg['from']
        sender_time = msg['time']
        to = msg['to']
        offset = math.floor((sender_time + self.local_time()) / 2)

        meet_in = self.soonest_sync(sender)

        if type == Package.DISC:
            if self.neighbors.get(sender) == None or meet_in < 0:
                if to != None and to != self.id:
                    return False
                
                update_table = True

                if to == None:
                    transmit_process = self.env.process(self.transmit(Package.DISC, sender))
                    yield transmit_process
                    update_table = transmit_process.value
                    
                if update_table:
                    self.neighbors[sender] = {
                        "offset": offset,
                        "last_meet": self.local_time(),
                    }
        elif type == Package.SYNC and sender in self.neighbors:
            if to == self.id or sender in self.sync_with:
                self.sync_cycles[-1]["sync_received"] += 1

                transmit_process = self.env.process(self.transmit(Package.ACK, sender))
                yield transmit_process
                if transmit_process.value:
                    self.neighbors[sender] = {
                        "offset": offset,
                        "last_meet": self.local_time(),
                    }
        elif type == Package.ACK:
            if to == self.id or sender in self.sync_with:
                self.sync_cycles[-1]["acks_received"] += 1

                self.neighbors[sender] = {
                    "offset": offset,
                    "last_meet": self.local_time(),
                }

        return True
    
    def soonest_sync(self, node_id = None):
        meet_in = float('inf')

        for id, neigh in self.neighbors.items():
            current_meet_in = neigh["offset"] + SYNC_INTERVAL - self.local_time()

            if node_id == id:
                return current_meet_in

            if current_meet_in > 0 and current_meet_in < meet_in:
                meet_in = current_meet_in

        return meet_in
    
    def update_upcoming_sync_nodes(self):
        self.sync_with = []
        
        soonest = self.soonest_sync()
        if soonest == float('inf'):
            return self.sync_with
        
        current_time = self.local_time()
        window_end = soonest + SYNC_TIME
        
        for node_id, neigh in self.neighbors.items():
            meet_in = neigh["offset"] + SYNC_INTERVAL - current_time
            
            if soonest <= meet_in <= window_end:
                self.sync_with.append(node_id)
        
        return self.sync_with

    def local_time(self):
        return math.floor(self.env.now * self.clock_drift)