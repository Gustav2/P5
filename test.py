import simpy, random, math
from statistics import mean

RANGE = 150     # meters
TX_TIME = 0.05  # seconds
LISTEN_TIME = 0.1
E_THRESHOLD = 1.0
E_HARVEST_RATE = (0.001, 0.005)  # per second, random
E_TX, E_RX = 0.05, 0.02

class Node:
    def __init__(self, env, node_id, x, y):
        self.env = env
        self.id = node_id
        self.x, self.y = x, y
        self.energy = random.uniform(0.5, 1.0)
        self.offset = random.uniform(-1, 1)
        self.neighbors = {}
        self.predicted_offset = 0.0  # phase adjustment (sec)
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
        return radio.check_for_msgs(self)

    def transmit_beacon(self):
        self.energy -= E_TX
        msg = {'type': 'BEACON', 'id': self.id, 'time': self.local_time()}
        yield self.env.timeout(TX_TIME)
        radio.broadcast(self, msg)

    def receive(self, msg):
        sender = msg['id']
        offset_est = msg['time'] - self.local_time()
        self.neighbors[sender] = offset_est
	    # update phase bias (toward average neighbor offset)
        self.predicted_offset = 0.8*self.predicted_offset + 0.2*offset_est

class Radio:
    def __init__(self, env, nodes, range_=RANGE, p_loss=0.1):
        self.env = env
        self.nodes = nodes
        self.range = range_
        self.p_loss = p_loss
        self.mailboxes = {n.id: [] for n in nodes}

    def broadcast(self, sender, msg):
        for n in self.nodes:
            if n.id == sender.id:
                continue
            if sender.distance(n) <= self.range and random.random() > self.p_loss:
                delay = random.uniform(0.01, 0.05)
                self.env.process(self.deliver(n, msg, delay))

    def deliver(self, node, msg, delay):
        yield self.env.timeout(delay)
        node.receive(msg)
        self.mailboxes[node.id].append(msg)

    def check_for_msgs(self, node):
        msgs = self.mailboxes[node.id]
        self.mailboxes[node.id] = []
        return len(msgs) > 0

def simulate(n=20, sim_time=500000):
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,200), random.uniform(0,200)) for i in range(n)]
    global radio
    radio = Radio(env, nodes)
    env.run(until=sim_time)
    neighs = [len(n.neighbors) for n in nodes]
    print("Avg discovered neighbors:", mean(neighs))
    for n in nodes[:5]:
        print(f"Node {n.id} knows {len(n.neighbors)} nodes")

simulate()
