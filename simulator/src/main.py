import simpy, random

from statistics import mean

from .node.node import Node
from .core.network import Network
from .core.plotter import Plotter

from .config import NODES, RANGE, ONE_DAY

def simulate_with_checkpoints(checkpoints):
    """Run simulation once and collect metrics at specified time intervals."""
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
    
    Network.nodes.clear()
    for n in nodes:
        Network.register_node(n)
    
    checkpoint_results = {}
    
    for checkpoint_time in sorted(checkpoints):
        env.run(until=checkpoint_time)
        
        kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]
        e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
        success_disc_e = mean([n.kpi.get_success_disc_e() for n in nodes])
        sync_tries = [n.sync_tries for n in nodes]
        avg_syncs = mean(sync_tries)
        acks_list = [n.acks_received for n in nodes]
        avg_acks = mean(acks_list)
        sync_success_rate = (avg_acks / avg_syncs * 100) if avg_syncs > 0 else 0
        
        checkpoint_results[checkpoint_time] = (e_per_cycle, avg_time, avg_success, avg_syncs, avg_acks, sync_success_rate, success_disc_e)
    
    return checkpoint_results

def simulate(runs, duration):
    checkpoints = [int(days * ONE_DAY) for days in duration]
    checkpoint_results_list = []

    for run in range(runs):
        current_seed = SEED+run
        random.seed(current_seed)
        Network.nodes = []
        Network.mailboxes = {}
        
        print(f"Running simulation {run + 1}/{number_of_runs}... using SEED={current_seed}")
        checkpoint_data = simulate_with_checkpoints(checkpoints)
        checkpoint_results_list.append(checkpoint_data)
        print(f"Simulation {run + 1} complete!")

    plotter = Plotter()
    results = plotter.evaluation(checkpoint_results_list)
    plotter.plot_results(results)

if __name__ == "__main__":
    
    number_of_runs = 3
    duration_days = list(range(1, 91))
    SEED = 42

    simulate(number_of_runs, duration_days)

"""
def main():
    durations_to_test = list(range(1, 90))
    number_of_cycles = 2

    plotter = Plotter()
    results = plotter.evaluation(runs=number_of_cycles, duration_days=durations_to_test)
    plotter.plot_results(results)

    EnergyLogger.plot()
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()"""