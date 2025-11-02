import simpy, random, math
from enum import Enum

from .network import Network

from .config import E_HARVEST_RATE, E_TRESHOLD, E_RX, E_TX, TX_TIME, E_IDLE, E_MAX, DELAY_RANGE

class State(Enum):
    Off = 0
    Idle = 1
    Receive = 2
    Transmit = 3

class Node:
    def __init__(self, env: simpy.Environment, id: int, x: float, y: float, logger):
        self.id = id
        self.x, self.y = x, y 
        self.state: State = State.Off
        self.env = env
        self.energy = 0
        self.harvest_incline_rate = random.uniform(random.random(), random.random()) # Random incline
        self.neighbors = {}
        self.logger = logger

        env.process(self.run())

    def run(self):
        while True:
            if self.logger:
                self.logger.log(self.id, self.env.now, self.energy)
        
            if self.energy >= E_TRESHOLD:
                heard = yield from self.listen(1)
                if not heard:
                    yield from self.transmit()
                    yield from self.listen(55) 

            if self.logger:
                self.logger.log(self.id, self.env.now, self.energy)        

            sleep_time = random.uniform(1, 20)
            self.state = State.Off
            yield self.env.timeout(sleep_time)
            self.harvest(sleep_time)

    def harvest(self, time):
        rate = E_HARVEST_RATE * self.harvest_incline_rate * time
        self.energy = max(0, min(self.energy + rate, E_MAX))
        self.state = State.Idle if self.energy > E_TRESHOLD else State.Off

    def listen(self, duration):
        if self.state != State.Idle:
            return False
        if self.energy <= E_TRESHOLD:
            return False

        remaining = self.energy - E_TRESHOLD
        if remaining <= 0:
            return False

        max_sec = remaining / E_IDLE
        available_sec = min(duration, max_sec)

        if E_IDLE * available_sec > remaining:
            available_sec = remaining / E_IDLE

        yield self.env.timeout(available_sec)

        used = E_IDLE * available_sec
        self.energy -= used

        # Not quite good, but because of floating points it goes lower sometimes
        self.energy = max(0.0, self.energy)

        self.state = State.Idle if self.energy > E_TRESHOLD else State.Off
        return Network.messages_received(self)

    def transmit(self):
        if self.state != State.Idle:
            return

        if (self.energy - E_TRESHOLD) < E_TX:
            return

        self.state = State.Transmit

        yield self.env.timeout(TX_TIME)
        self.energy -= E_TX

        msg = {'type': 'BEACON', 'id': self.id, 'time': self.local_time()}
        Network().broadcast(self, msg)

        self.state = State.Idle if self.energy > E_TRESHOLD else State.Off

    def receive(self, msg):
        if self.state != State.Idle:
            return

        if (self.energy - E_TRESHOLD) < E_RX:
            return

        delay = random.uniform(*DELAY_RANGE)
        yield self.env.timeout(delay)
        self.state = State.Receive

        # TODO consider decoding time
        sender = msg['id']
        offset_est = msg['time'] - self.local_time()
        self.neighbors[sender] = offset_est
        # TODO calc offset in time for sleeping

        self.energy -= E_RX
        self.state = State.Idle if self.energy > E_TRESHOLD else State.Off

    def update_energy_state(self):
        # TODO
        return

    def local_time(self):
        return self.env.now

    def distance(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)