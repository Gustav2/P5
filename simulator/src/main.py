import simpy, random
from statistics import mean

from .node.node import Node
from .core.network import Network

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology

from .config import NODES, SIM_TIME, RANGE

def plot(Network):
    EnergyLogger.plot()
    topo = NetworkTopology(Network.nodes)
    topo.save("topology.png")    

def simulate():
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
    
    for n in nodes:
        Network.register_node(n)

    env.run(until=SIM_TIME)

    kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]

    e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]

    #print(f"Energy usage per DISC cycle: {e_per_cycle} J")
    #print(f"Time till first DISC receive: {avg_time} sec")
    #print(f"Energy per successfull DISC cycle: N/A J")
    #print(f"DISC success rate: {avg_success} %")

    #plot(Network)
    return e_per_cycle, avg_time, avg_success


def evaluation(runs):
    #please give me a better name for these lists
    e_per_cycle_list = []
    avg_time_list = []
    avg_success_list = []

    for i in range (runs):
        e_per_cycle, avg_time, avg_success = simulate()
        e_per_cycle_list.append(e_per_cycle)
        avg_time_list.append(avg_time)
        avg_success_list.append(avg_success)

        print("----------------------------")
        print(f"Run {i+1}:")
        print(f"Energy Consumption per Discovery Cycle: {e_per_cycle} J")
        print(f"Energy per Successful Neighbour Discovery: N/A")
        print(f"Discovery Latency: {avg_time} s")
        print(f"Discovery Success Rate: {avg_success} %")

    e_per_cycle_average = mean(e_per_cycle_list)
    avg_time_average = mean(avg_time_list)
    avg_success_average = mean(avg_success_list)

    print("============================")
    print(f"Average of all runs:")
    print(f"Energy Consumption per Discovery Cycle: {e_per_cycle_average} J")
    print(f"Energy per Successful Neighbour Discovery: N/A")
    print(f"Discovery Latency: {avg_time_average} s")
    print(f"Discovery Success Rate: {avg_success_average} %")


if __name__ == "__main__":
    evaluation(2)