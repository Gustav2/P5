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

    print(f"Avg discovered neighbors: {mean(discovered_neighs)}")
    print(F"Discovery success rate: {mean(discovered_neighs) / (NODES - 1) * 100:.1f} %\n")

    total_initiated = sum(n.syncs_initiated for n in nodes)
    tried_sync_with = sum(cycle["nodes"] for node in nodes for cycle in node.sync_cycles)
    total_sync = sum(cycle["sync_received"] for node in nodes for cycle in node.sync_cycles)
    total_ack = sum(cycle["acks_received"] for node in nodes for cycle in node.sync_cycles)

    print(f"Total SYNCs received: {total_sync}")
    print(f"Total ACKs received: {total_ack}")
    print(f"ACKs per SYNC/ACK rate: {(total_sync + total_ack) / tried_sync_with * 100:.1f} %")
    print(f"ACKs per SYNCs rate: {(total_sync + total_ack) / total_initiated * 100:.1f}%")

    EnergyLogger.plot(chunks_days=2)
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()