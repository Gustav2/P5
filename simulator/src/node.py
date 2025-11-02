import simpy, random, math

from .network import Network

from .config import E_HARVEST_RATE, E_THRESHOLD, LISTEN_TIME, E_RX, E_TX, TX_TIME

class Node:
    def __init__(self, env: simpy.Environment, node_id: int, x: float, y: float):
        self.env = env
        self.id = node_id
        self.x, self.y = x, y
        self.energy = random.uniform(0.5, 1.0)
        self.offset = random.uniform(-1, 1)
        self.neighbors = {}
        self.predicted_offset = 0.0
        env.process(self.run())

    def local_time(self):
        return self.env.now + self.offset

    def distance(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def harvest(self, dt):
        rate = random.uniform(*E_HARVEST_RATE)
        self.energy = min(1.2, self.energy + rate * dt)

    def run(self):
        while True:
            # harvest until threshold
            while self.energy < E_THRESHOLD:
                yield self.env.timeout(1.0)
                self.harvest(1.0)

            # wake up
            start = self.env.now
            heard = yield from self.listen(LISTEN_TIME)
            if not heard:
                yield from self.transmit_beacon()
                yield from self.listen(LISTEN_TIME)

            # consume energy
            awake_time = self.env.now - start
            self.energy -= awake_time * 0.02  # base cost
            self.energy = max(0, self.energy)
            # go back to "sleep" to recharge
            sleep_time = random.uniform(1,5)
            # bias next wake to align with known offsets
            sleep_time = max(0, sleep_time + self.predicted_offset)
            yield self.env.timeout(sleep_time)

    def listen(self, duration):
        self.energy -= E_RX
        yield self.env.timeout(duration)
        return Network.messages_received(self)

    def transmit_beacon(self):
        self.energy -= E_TX
        msg = {'type': 'BEACON', 'id': self.id, 'time': self.local_time()}
        yield self.env.timeout(TX_TIME)
        Network.broadcast(self, msg)

    def receive(self, msg):
        sender = msg['id']
        offset_est = msg['time'] - self.local_time()
        self.neighbors[sender] = offset_est
	    # update phase bias (toward average neighbor offset)
        self.predicted_offset = 0.8*self.predicted_offset + 0.2*offset_est