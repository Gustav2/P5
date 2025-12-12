import simpy, random, math

from ..core.network import Network
from .state import State, Package
from .capacitor import Capacitor
from .kpi import KPI
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
        self.is_sync = False
        self.syncs_initiated = 0
        self.sync_cycles = []
        self.sync_with = []

        self.listen_time = 0
        self.kpi = KPI()

        Network.register_node(self)
        self.env.process(self.run())

    def run(self):
        while True:
            EnergyLogger.log(self.id, self.local_time(), self.capacitor.energy)

            # Discovery part
            listen_time = math.ceil(random.uniform(*LISTEN_TIME_RANGE))
            energy_to_use = listen_time * E_RECEIVE + E_TX + E_RX

            # Sync part
            next_sync_with = self.get_upcoming_sync_nodes()
            energy_for_sync = SYNC_TIME * E_RECEIVE + E_TX + len(next_sync_with) * E_RX
            idle_time_for_sync = self.capacitor.time_to_charge_to(energy_for_sync)
            sync_in = self.soonest_sync()

            self.is_sync = False

            # Pick what's sooner and prioritize
            if sync_in != float('inf') and 0 < sync_in - idle_time_for_sync < SYNC_PREPARATION_TIME:
                self.is_sync = True
                listen_time = SYNC_TIME
                energy_to_use = energy_for_sync
                idle_time = sync_in
            else:
                idle_time = self.capacitor.time_to_charge_to(energy_to_use)

            self.listen_time = listen_time

            yield self.env.timeout(idle_time)
            self.capacitor.harvest(idle_time)

            EnergyLogger.log(self.id, self.local_time(), self.capacitor.energy)

            if self.capacitor.remaining_energy() >= energy_to_use:
                if not self.is_sync:
                    self.kpi.start_discovery(listen_time, self.local_time())
                
                listen_for = random.uniform(*SYNC_TIME_RANGE) if self.is_sync else (listen_time / 2)
                listen_process = self.env.process(self.listen(listen_for))
                yield listen_process

                messages = listen_process.value
                heard = len(messages) > 0 # type: ignore

                if self.is_sync:
                    self.sync_with = next_sync_with
                    if len(self.sync_with) == 0:
                        self.is_sync = False
                    else:
                        self.syncs_initiated += 1
                        sync_partners = set(self.sync_with)
                        self.sync_cycles.append({
                            "nodes": len(sync_partners), 
                            "sync_received": 0, 
                            "acks_received": 0
                        })

                        heard = False
                        
                        for msg in messages: # type: ignore
                            if msg['from'] in sync_partners and msg['type'] == Package.SYNC:
                                heard = True
                                break

                if not heard:
                    yield self.env.process(self.transmit(Package.SYNC if self.is_sync else Package.DISC, None))
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
        
        self.kpi.add_e(energy_to_use)
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

        self.kpi.add_e(E_TX)
        self.state = State.Idle

        return True

    def receive(self, msg):
        if self.state != State.Receive or self.capacitor.remaining_energy() < E_RX:
            return False
        
        self.state = State.Decode
            
        self.capacitor.discharge(E_RX)
        yield self.env.timeout(PT_TIME)
        self.capacitor.harvest(PT_TIME)

        type = Package(msg['type'])
        sender = msg['from']
        to = msg['to']
        sender_time = msg['time']

        self.state = State.Receive
        self.kpi.add_e(E_RX)

        if type == Package.DISC and not self.is_sync:
            if self.neighbors.get(sender) == None or self.soonest_sync(sender) < 0:
                update_table = to == None or to == self.id

                if to == self.id:
                    self.kpi.receive_disc_ack(self.listen_time, self.local_time())
                
                if to == None:
                    yield self.env.process(self.transmit(Package.DISC, sender))
                    self.kpi.send_disc_ack(self.listen_time, self.local_time())

                if update_table:
                    self.update_neighbor(sender, sender_time)
        elif type == Package.SYNC and self.is_sync and len(self.sync_cycles):
                self.sync_cycles[-1]["sync_received"] += 1

                yield self.env.timeout(random.uniform(*ACK_SEND_DELAY_RANGE))
                transmit_process = self.env.process(self.transmit(Package.ACK, sender))

                yield transmit_process
                if transmit_process.value:
                    self.update_neighbor(sender, sender_time)
        elif type == Package.ACK and self.is_sync and len(self.sync_with): #(to == self.id or sender in self.sync_with):
                if len(self.sync_cycles):
                    self.sync_cycles.append({
                        "nodes": len(self.sync_with), 
                        "sync_received": 0, 
                        "acks_received": 0
                    })
                self.sync_cycles[-1]["acks_received"] += 1
                self.update_neighbor(sender, sender_time)

        return True
    
    def soonest_sync(self, node_id=None):
        meet_in = float('inf')
        current_time = self.local_time()

        for id, neigh in self.neighbors.items():
            drift_rate = self.estimate_drift(id)
            
            my_sync_time = neigh["last_meet_mine"] / drift_rate + SYNC_INTERVAL - SYNC_TIME / 2
            current_meet_in = my_sync_time - current_time

            if node_id == id:
                return current_meet_in

            if current_meet_in > 0 and current_meet_in < meet_in:
                meet_in = current_meet_in

        return meet_in
        
    def update_neighbor(self, sender, sender_time):
        my_time = self.local_time()
        
        if self.neighbors.get(sender) is None:
            self.neighbors[sender] = {
                "meet_points": [(my_time, sender_time)],
                "last_meet_mine": my_time,
                "last_meet_their": sender_time,
            }
        else:
            neigh = self.neighbors[sender]
            neigh["meet_points"].append((my_time, sender_time))
            
            if len(neigh["meet_points"]) > 8:
                neigh["meet_points"].pop(0)
            
            neigh["last_meet_mine"] = my_time
            neigh["last_meet_their"] = sender_time

    def estimate_drift(self, id):
        points = self.neighbors[id]["meet_points"]
        if len(points) < 2:
            return 1.0
        
        n = len(points)
        sum_x = sum(p[0] for p in points)
        sum_y = sum(p[1] for p in points)
        sum_xy = sum(p[0] * p[1] for p in points)
        sum_xx = sum(p[0] ** 2 for p in points)
        
        denominator = n * sum_xx - sum_x ** 2
        if denominator == 0:
            return 1.0
        
        drift_rate = (n * sum_xy - sum_x * sum_y) / denominator
        
        if drift_rate <= 0 or drift_rate > 2.0:
            return 1.0
        
        return drift_rate

    def get_upcoming_sync_nodes(self):
        result: list[int] = []
        
        soonest = self.soonest_sync()
        if soonest == float('inf'):
            return []
        
        current_time = self.local_time()
        
        for node_id, neigh in self.neighbors.items():
            drift_rate = neigh.get("drift_rate", 1.0)
            
            my_sync_time = neigh["last_meet_mine"] / drift_rate + SYNC_INTERVAL - SYNC_TIME / 2
            meet_in = my_sync_time - current_time
            
            if soonest <= meet_in <= soonest + SYNC_TIME:
                result.append(node_id)

        return result

    def local_time(self):
        return math.floor(self.env.now * self.clock_drift)