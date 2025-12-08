import matplotlib.pyplot as plt
import simpy, random
from statistics import mean
import numpy as np
from numpy.polynomial import polynomial as P
from scipy.optimize import curve_fit

from .node.node import Node
from .core.network import Network

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology

from .config import NODES, SIM_TIME, RANGE,ONE_DAY

def plot(Network):
    EnergyLogger.plot()
    topo = NetworkTopology(Network.nodes)
    topo.save("topology.png")    

def simulate_with_checkpoints(checkpoints):
    """Run simulation once and collect metrics at specified time intervals."""
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
    
    for n in nodes:
        Network.register_node(n)

    checkpoint_results = {}
    
    for checkpoint_time in sorted(checkpoints):
        env.run(until = checkpoint_time)
        kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]
        e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
        checkpoint_results[checkpoint_time] = (e_per_cycle, avg_time, avg_success)
    
    return checkpoint_results

def evaluation(runs, duration_days):
    results = {}
    checkpoints = [days * ONE_DAY for days in duration_days]
    
    for i in range(runs):
        checkpoint_data = simulate_with_checkpoints(checkpoints)
        
        for days, checkpoint_time in zip(duration_days, checkpoints):
            if days not in results:
                results[days] = {'e': [], 't': [], 's': [], 's_list': []}
            
            e_per_cycle, avg_time, avg_success = checkpoint_data[checkpoint_time]
            results[days]['e'].append(e_per_cycle)
            results[days]['t'].append(avg_time)
            results[days]['s'].append(avg_success)
            results[days]['s_list'].append(avg_success)
            
            print("----------------------------")
            print(f"Simulation duration: {days} days (Run {i+1})")
            print(f"Energy Consumption per Discovery Cycle: {e_per_cycle} J")
            print(f"Discovery Latency: {avg_time} s")
            print(f"Discovery Success Rate: {avg_success} %")
    
    # Convert to averages
    for days in results:
        results[days] = (
            mean(results[days]['e']),
            mean(results[days]['t']),
            mean(results[days]['s']),
            results[days]['s_list']
        )
    
    return results

def plot_results(results): #New function bcs Andris plotting function won't work, and better to have a spearate one.
    days = list(results.keys())
    e_vals = [results[d][0] for d in days]
    t_vals = [results[d][1] for d in days]
    s_vals = [results[d][2] for d in days]
    s_list = [results[d][3] for d in days]

    # Energy Graph
    plt.figure()
    plt.plot(days, e_vals, marker='o',color='orange')
    plt.title("Energy Consumption per Discovery Cycle vs Duration")
    plt.xlabel("Simulation Duration (days)")
    plt.ylabel("Energy (J)")
    plt.grid(True)
    plt.savefig("energy_vs_days.png")

    # Latency Graph
    plt.figure()
    plt.plot(days, t_vals, marker='o',color='red')
    plt.title("Discovery Latency vs Duration")
    plt.xlabel("Simulation Duration (days)")
    plt.ylabel("Latency (s)")
    plt.grid(True)
    plt.savefig("latency_vs_days.png")

    # Success Rate Graph
    plt.figure()
    plt.plot(days, s_vals, marker='o')
    plt.title("Discovery Success Rate vs Duration")
    plt.xlabel("Simulation Duration (days)")
    plt.ylabel("Success Rate (%)")
    plt.grid(True)
    plt.savefig("success_vs_days.png")

    # Success of all runs graph with regression
    plt.figure()
    
    # Plot each run as a separate line
    for run_index, day_success_rates in enumerate(zip(*s_list)):
        plt.plot(days, day_success_rates, alpha=0.6, label=f'Run {run_index+1}')
    
    # Fit exponential decay regression on all individual data points
    all_runs_data = []
    x_vals = []
    for day, success_rates in zip(days, s_list):
        for success_rate in success_rates:
            x_vals.append(day)
            all_runs_data.append(success_rate)
    
    # Fit exponential decay regression: y = a * (1 - exp(-b*x)) + c
    def exponential_model(x, a, b, c):
        return a * (1 - np.exp(-b * x)) + c
    
    try:
        popt, _ = curve_fit(exponential_model, x_vals, all_runs_data, p0=[100, 0.1, 0], maxfev=5000)
        x_smooth = np.linspace(min(days), max(days), 100)
        y_smooth = exponential_model(x_smooth, *popt)
        plt.plot(x_smooth, y_smooth, 'r-', linewidth=2.5, label='Exponential fit')
    except:
        plt.plot([], [], 'r-', linewidth=2.5, label='Exponential fit (failed)')
    
    plt.title("Discovery Success Rate (All Runs) vs Duration")
    plt.xlabel("Simulation Duration (days)")
    plt.ylabel("Success Rate (%)")
    plt.legend()
    plt.grid(True)
    plt.savefig("success_list_vs_days.png")

if __name__ == "__main__":

    durations_to_test = list(range(1,61)) #Careful with the days, the simulation will take a very very long time, and eat your computer's resources ASAP
    number_of_cycles=3 #Also be careful lol
    res=evaluation(number_of_cycles,durations_to_test)
    plot_results(res)

    #results = evaluate_multiple_durations(durations_to_test, runs_per_duration=4)

