import simpy, random, math

from ..core.network import Network
from ..core.energy_logger import EnergyLogger
from .state import State, Package
from .harvester import Harvester
from .kpi import KPI

from ..config import *

class Node:
    def __init__(self, env: simpy.Environment, id: int):
        self.id = id
        self.state: State = State.Idle
        self.harvester = Harvester(id)
        self.env = env
        self.clock_drift = random.randint(*NODE_START_TIMES)

        self.kpi = KPI()
        self.listen_time = 0
        self.listen_for = 0

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
            idle_time_for_sync = self.harvester.time_to_charge_to(energy_for_sync)
            (sync_with, sync_in) = self.soonest_sync()

            # Pick what's sooner and prioritize
            if sync_in != float('inf') and sync_in - idle_time_for_sync < SYNC_PREPARATION_TIME:
                self.is_sync = True
                listen_time = SYNC_TIME
                energy_to_use = energy_for_sync
                idle_time = sync_in
            else:
                self.is_sync = False
                idle_time = self.harvester.time_to_charge_to(energy_to_use)

            self.listen_time = listen_time

            yield self.env.timeout(idle_time)
            self.harvester.harvest(idle_time)

            EnergyLogger().log(self.id, self.local_time(), self.harvester.energy)

            if self.harvester.remaining_energy() >= energy_to_use:
                if not self.is_sync:
                    self.kpi.start_discovery(self.local_time())

                listen_for = random.uniform(*SYNC_TIME_RANGE) if self.is_sync else (listen_time / 2)
                self.listen_process = self.env.process(self.listen(listen_for))
                # [1]: Node 40 listens after it woke up

                heard = True
                try:
                    yield self.listen_process
                    heard = self.listen_process.value
                except simpy.Interrupt:
                    pass
                finally:
                    self.listen_process = None
                
                if not heard:
                    yield self.env.process(
                        self.transmit(Package.SYNC if self.is_sync else Package.DISC, 
                        sync_with if self.is_sync else None
                    ))
                    # [2]: Node 40 transmits DISC to 39

                    if not self.is_sync:
                        self.kpi.send_discovery(listen_for)
                    
                    self.listen_process = self.env.process(self.listen(listen_time - listen_for))
                    # [3]: Node 40 listens after transmitting DISC
                    try:
                        yield self.listen_process
                    except simpy.Interrupt:
                        pass
                    finally:
                        self.listen_process = None

            self.state = State.Idle

    def listen(self, duration):
        available_seconds = math.floor(self.harvester.remaining_energy() / E_RECEIVE)
        energy_to_use = E_RECEIVE * min(duration, available_seconds)

        if self.harvester.remaining_energy() < energy_to_use:
            return False

        self.state = State.Receive
        self.harvester.discharge(energy_to_use)        
        yield self.env.timeout(min(duration, available_seconds))
        self.harvester.harvest(min(duration, available_seconds))
        
        self.kpi.add_e(energy_to_use)
        self.state = State.Idle

        return Network.messages_received(self)

    def transmit(self, package_type: Package, to):
        if self.harvester.remaining_energy() < E_TX:
            return False

        self.state = State.Transmit
        self.harvester.discharge(E_TX)
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME)

        if package_type == Package.SYNC:
            self.sync_tries += 1

        msg = {
            'type': package_type, 
            'id': self.id,
            'to': to,
            'time': self.local_time(),
        }

        if msg['type'] == Package.DISC and msg['to'] == None:
            self.kpi.actual_send_disc()

        self.kpi.add_e(E_TX)

        yield self.env.timeout(random.uniform(*DELAY_RANGE))
        Network.broadcast(self, msg)

        return True

    def receive(self, msg):
        if self.state != State.Receive or self.harvester.remaining_energy() < E_RX:
            return False
        
        self.harvester.discharge(E_RX)
        yield self.env.timeout(PT_TIME)
        self.harvester.harvest(PT_TIME)

        type = Package(msg['type'])
        sender = msg['id']
        sender_time = msg['time']
        receiver = msg['to']
        #offset = math.floor((sender_time + self.local_time()) / 2)
        offset = self.local_time()

        (_, time_to_meet) = self.soonest_sync(sender)

        self.kpi.add_e(E_RX)

        if type == Package.DISC:
            self.kpi.receive_discovery(self.listen_for, self.local_time())
            if(self.id == receiver or self.neighbors.get(sender) == None or time_to_meet < 0):
                self.kpi.receive_disc_ack(self.listen_time)
                self.neighbors[sender] = {
                    "delay": offset,
                    "last_meet": self.local_time(),
                }
                #if receiver == None:
                #    print(f"Node {self.id:02d} received    DISC     from {sender:02d}  at time {self.local_time()}")
                if receiver == self.id:
                    self.kpi.actual_disck_success()
                #    print(f"Node {self.id:02d} received    ACK DISC from {sender:02d}  at time {self.local_time()}")
                if receiver == None:
                    yield self.env.process(self.transmit(Package.DISC, sender))
                    # [3]: Node 08 transmits DISC to 20 (82482247)
                
                if self.listen_process:
                    #print("dicovery interrupting")
                    self.listen_process.interrupt('discovered')
        elif type == Package.SYNC and sender in self.neighbors:
            if self.id == receiver:
                transmit_process = self.env.process(self.transmit(Package.ACK, sender))
                yield transmit_process
                if transmit_process.value:
                    self.neighbors[sender] = {
                        "delay": offset,
                        "last_meet": self.local_time(),
                    }
                    if self.listen_process:
                        #print("ack sent interrupt")
                        self.listen_process.interrupt('ack_sent')
        elif type == Package.ACK:
            if self.id == receiver:
                self.acks_received += 1
                self.neighbors[sender] = {
                    "delay": offset,
                    "last_meet": self.local_time(),
                }
                if self.listen_process:
                    #print("ack receive interrupt")
                    self.listen_process.interrupt('ack_received')

        return True
    
    def soonest_sync(self, node_id = None):
        meet_in = float('inf')
        meet_with = -1

        for id, neigh in self.neighbors.items():
            current_meet_in = neigh["delay"] + SYNC_INTERVAL - self.local_time()

            if node_id == id:
                return (node_id, current_meet_in)

            if current_meet_in > 0 and current_meet_in < meet_in:
                meet_in = current_meet_in
                meet_with = id

        return (meet_with, meet_in)
    
    def update_clock_drift(self):
        self.clock_drift += random.randint(0, CLOCK_DRIFT_PER_DAY)

    def local_time(self):
        if CLOCK_DRIFT_ENABLED:
            #print(math.floor(self.env.now + self.clock_drift))
            return math.floor(self.env.now + self.clock_drift)
        else:
            return math.floor(self.env.now)