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
    
    for n in nodes:
        Network.register_node(n)

    # Run with progress bar
    with tqdm(total=SIM_TIME, desc="Simulating", unit="time") as pbar:
        last_time = 0
        while env.now < SIM_TIME:
            env.step()
            if int(env.now) > last_time:
                pbar.update(int(env.now) - last_time)
                last_time = int(env.now)

    discovered_neighs = [len(n.neighbors) for n in nodes]
    avg = mean(discovered_neighs)
    print("Avg discovered neighbors:", avg)
    print("Discovery success rate:", avg / (NODES - 1) * 100, "%")

    sync_tries = [
        n.sync_tries
        for n in nodes
    ]
    avg_syncs = mean(sync_tries)
    print("Avg sync tries:", avg_syncs)

    acks_list = [
        n.acks_received
        for n in nodes
    ]
    avg_acks = mean(acks_list)
    print("Avg acks received:", avg_acks)

    print("Sync success rate:", (avg_acks / avg_syncs * 100) if avg_syncs > 0 else 0, "%")

    EnergyLogger.plot()
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()