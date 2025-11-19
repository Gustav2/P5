import simpy, random
from statistics import mean

from .node.node import Node
from .core.network import Network
from .core.energy_logger import EnergyLogger

from .config import NODES, SIM_TIME, RANGE

def main():
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
    
    for n in nodes:
        Network.register_node(n)

    env.run(until=SIM_TIME)

    discovered_neighs = [len(n.neighbors) for n in nodes]
    avg_discoveries = mean(discovered_neighs)
    print("Average discoveries:", avg_discoveries)
    print("Discovery success rate:", avg_discoveries / (NODES - 1) * 100, "%")

    sync_tries = [
        n.sync_tries
        for n in nodes
    ]
    avg_syncs = mean(sync_tries)
    print("Average sync tries:", avg_syncs)

    acks_list = [
        n.acks_received
        for n in nodes
    ]
    avg_acks = mean(acks_list)
    print("Average acks received:", avg_acks)

    print("Sync success rate:", avg_acks / avg_syncs * 100, "%")

    EnergyLogger().plot()

if __name__ == "__main__":
    main()