import simpy, random
from statistics import mean

from .node import Node
from .network import Network
from .energy_logger import EnergyLogger

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
    print("Success rate:", avg / NODES * 100, "%")

    EnergyLogger().plot()

if __name__ == "__main__":
    main()