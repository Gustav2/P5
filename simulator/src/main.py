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

    kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]

    e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]

    print(f"Energy usage per DISC cycle: {e_per_cycle} J")
    print(f"Time till first DISC receive: {avg_time} sec")
    print(f"Energy per successfull DISC cycle: N/A J")
    print(f"DISC success rate: {avg_success} %")

    EnergyLogger.plot()
    topo = NetworkTopology(Network.nodes)
    topo.save("topology.png")

if __name__ == "__main__":
    main()