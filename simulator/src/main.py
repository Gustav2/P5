import simpy, random
from statistics import mean

from .node import Node
from .network import Network

from .config import NODES, SIM_TIME, RANGE

def main():
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
    
    for n in nodes:
        Network.register_node(n)

    env.run(until=SIM_TIME)

    discovered_neighs = [len(n.neighbors) for n in nodes]
    print("Avg discovered neighbors:", mean(discovered_neighs))

    for n in nodes:
        print(f"Node {n.id} knows {len(n.neighbors)} nodes")

if __name__ == "__main__":
    main()