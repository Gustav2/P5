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

    meetings_list = [
        info["meetings"]
        for n in nodes
        for info in n.neighbors.values()
    ]
    avg_meetings = mean(meetings_list)
    print("Average meetings amounts:", avg_meetings)

    sync_tries = [
        n.sync_tries
        for n in nodes
    ]
    avg_syncs = mean(sync_tries)
    print("Sync success rate:", (avg_meetings / avg_syncs * 100) if avg_syncs > 0 else 0, "%")

    EnergyLogger().plot()

if __name__ == "__main__":
    main()