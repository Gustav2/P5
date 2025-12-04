import simpy, random
from statistics import mean
from tqdm import tqdm

from .node.node import Node
from .core.network import Network

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology

from .config import NODES, SIM_TIME, RANGE

def main():
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]

    chunk_size = SIM_TIME // 20 
    with tqdm(total=SIM_TIME, desc="Simulating", unit="time") as pbar:
        for t in range(0, SIM_TIME, chunk_size):
            env.run(until=min(t + chunk_size, SIM_TIME))
            pbar.update(chunk_size)

    discovered_neighs = [len(n.neighbors) for n in nodes]
    avg = mean(discovered_neighs)

    total_syncs = sum(n.sync_tries for n in nodes)
    total_acks_sent = sum(n.acks_sent for n in nodes)
    total_acks_received = sum(n.acks_received for n in nodes)

    print(f"Avg discovered neighbors: {avg}")
    print(F"Discovery success rate: {avg / (NODES - 1) * 100} %\n")
    print(f"Total SYNCs sent: {total_syncs}")
    print(f"Total ACKs sent: {total_acks_sent}")
    print(f"Total ACKs received: {total_acks_received}\n")
    print(f"Avg ACKs per SYNC: {(total_acks_received / total_syncs * 100) if total_syncs > 0 else 0} %")

    #EnergyLogger.plot(chunks_days=2)
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()