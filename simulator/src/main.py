import simpy, random
from statistics import mean

from .node.node import Node
from .core.network import Network

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology

from .config import NODES, SIM_TIME, RANGE,ONE_DAY

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


def evaluation(runs,duration_days):
    original_sim_time = SIM_TIME
    #please give me a better name for these lists
    #I like the names, dont udermine your work :)
    for days in duration_days:
        sim_time_ms = days * ONE_DAY #Need to override the SIM_TIME value from config, if we dont do that, the simulation will only run for 1 set interval of time. Need to show to Andris so he doesnt have a crashout....
        globals()['SIM_TIME'] = sim_time_ms

        e_per_cycle_list = []
        avg_time_list = []
        avg_success_list = []

        for i in range (runs):
            e_per_cycle, avg_time, avg_success = simulate()
            e_per_cycle_list.append(e_per_cycle)
            avg_time_list.append(avg_time)
            avg_success_list.append(avg_success)

            print("----------------------------")
            print(f"Simulation duration: {days} days")
            print(f"Run {i+1}:")
            print(f"Energy Consumption per Discovery Cycle: {e_per_cycle} J")
            print(f"Energy per Successful Neighbour Discovery: N/A")
            print(f"Discovery Latency: {avg_time} s")
            print(f"Discovery Success Rate: {avg_success} %")

        e_per_cycle_average = mean(e_per_cycle_list)
        avg_time_average = mean(avg_time_list)
        avg_success_average = mean(avg_success_list)

        print("============================")
        print(f"Averages for {days} days of simulation:")
        print(f"Average of all runs:")
        print(f"Energy Consumption per Discovery Cycle: {e_per_cycle_average} J")
        print(f"Energy per Successful Neighbour Discovery: N/A")
        print(f"Discovery Latency: {avg_time_average} s")
        print(f"Discovery Success Rate: {avg_success_average} %")
    
    globals()['SIM_TIME'] = original_sim_time #We set the value back to the original, since everything else runs on that set time, we just "except" this for our use, to then set it back


if __name__ == "__main__":
    durations_to_test = [14, 25] #Careful with the days, the simulation will take a very very long time, and eat your computer's resources ASAP
    number_of_cycles=1 #Also be careful lol
    evaluation(number_of_cycles,durations_to_test)

    #results = evaluate_multiple_durations(durations_to_test, runs_per_duration=4)

