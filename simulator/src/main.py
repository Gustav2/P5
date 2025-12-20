import simpy, random

from statistics import mean

from .node.node import Node
from .core.network import Network
from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology
from .core.plotter import Plotter

from .config import NODES, RANGE, ONE_DAY  

def simulate_with_checkpoints(checkpoints, run):
    """Run simulation once and collect metrics at specified time intervals."""
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
    
    Network.nodes.clear()
    for n in nodes:
        Network.register_node(n)
    
    checkpoint_results = {}
    
    for checkpoint_time in sorted(checkpoints):
        env.run(until = checkpoint_time)
        kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]
        e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
        checkpoint_results[checkpoint_time] = (e_per_cycle, avg_time, avg_success)

        for n in nodes:
            n.update_clock_drift()

    total_e_used = sum(n.kpi.e_total for n in nodes)  # total energy of all nodes
    sim_days = max(checkpoints) / ONE_DAY             # duration of this run in days
    avg_energy_per_day = total_e_used / (NODES * sim_days)
    print(f"\n=== VERSION 0 ENERGY SUMMARY – RUN {run+1} ===")
    print(f"Total energy used by all nodes:           {total_e_used:.6f} J")
    print(f"Average energy per node per day:          {avg_energy_per_day:.6f} J/day")
    print("===============================================\n")
    EnergyLogger.plot()
    NetworkTopology(Network.nodes).save(filename = f"topology_run{run+1}")

    return checkpoint_results,avg_energy_per_day

def simulate(number_of_runs, duration_days, seed):
    checkpoints = [int(days * ONE_DAY) for days in duration_days]
    checkpoint_results_list = []
    avg_energy_days = []
    for run in range(number_of_runs):
        current_seed = seed + run
        random.seed(current_seed)
        Network.nodes = []
        Network.mailboxes = {}
        
        print(f"Running simulation {run + 1}/{number_of_runs}... using SEED={current_seed}")
        checkpoint_data,avg_energy_per_day = simulate_with_checkpoints(checkpoints, run)
        checkpoint_results_list.append(checkpoint_data)
        avg_energy_days.append(avg_energy_per_day)
        print(f"Simulation {run + 1} complete!")
    
    overall_avg_energy_per_day = mean(avg_energy_days)
    print("\n===== OVERALL AVERAGE ENERGY PER DAY (VERSION 0, ALL RUNS) =====")
    print(f"Average energy used per node per day across ALL runs (BASE ESR VALUE): {overall_avg_energy_per_day:.6f} J")
    print("================================================================\n")

    plotter = Plotter()
    results = plotter.evaluation(checkpoint_results_list)
    plotter.plot_results(results)

if __name__ == "__main__":
    
    number_of_runs = 1
    duration_days = list(range(1, 11))
    seed = 42

    simulate(number_of_runs, duration_days, seed)