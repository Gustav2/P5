import simpy, random
from statistics import mean

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

    env.run(until=SIM_TIME)

    discovered_neighs = [len(n.neighbors) for n in nodes]
    avg = mean(discovered_neighs)
    print("Avg discovered neighbors:", avg)
    print("Success rate:", avg / (NODES - 1) * 100, "%")

    EnergyLogger.plot()
    topo = NetworkTopology(Network.nodes)
    topo.save("topology.png")

if __name__ == "__main__":
    main()