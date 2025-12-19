import simpy, random, os, time
from statistics import mean

from .core.node import Node
from .core.network import Network
from .results.energy_logger import EnergyLogger
from .results.network_topology import NetworkTopology
from .results.plotter import Plotter

from .config import NODES, ONE_DAY, SIM_DAYS, SEED, RUNS

def simulate_with_checkpoints(checkpoints, run):
    """Run simulation once and collect metrics at specified time intervals."""
    env = simpy.Environment()
    nodes = [Node(env, i) for i in range(NODES)]
    
    Network.nodes.clear()
    for n in nodes:
        Network.register_node(n)
    
    checkpoint_results = {}
    discovery_progress = {}  # NEW: Track discovery progress
    
    for checkpoint_time in sorted(checkpoints):
        env.run(until = checkpoint_time)

        current_day = checkpoint_time / ONE_DAY 
        print(f" Day {current_day:.0f}/{len(checkpoints)} completed", end='\r')

        kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]
        sync_success = [n.kpi.actual_disc_success_rate() for n in nodes]
        e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
        
        # ---------- ADDED: extra KPIs ----------
        success_disc_e = mean([n.kpi.get_success_disc_e() for n in nodes])

        sync_tries = [n.sync_tries for n in nodes]
        avg_syncs = mean(sync_tries)

        acks_list = [n.acks_received for n in nodes]
        avg_acks = mean(acks_list)

        sync_success_rate = (avg_acks / avg_syncs * 100) if avg_syncs > 0 else 0
        total_e_used_cp = sum(n.kpi.e_total for n in nodes)
        total_e_discovery_cp = sum(n.kpi.disc_e_receive + n.kpi.disc_e_send for n in nodes)
        total_e_sync_cp = total_e_used_cp - total_e_discovery_cp
        sync_cycles_cp = sum(n.kpi.disc_received + n.kpi.disc_sent for n in nodes)
        e_sync_per_cycle_cp = total_e_sync_cp / sync_cycles_cp if sync_cycles_cp > 0 else 0
        
        # ---------- NEW: Track discovery progress ----------
        max_discoverable = NODES - 1  # Each node can discover all others except itself
        node_discovery_percentages = [(len(n.neighbors) / max_discoverable * 100) for n in nodes]
        avg_discovery_pct = mean(node_discovery_percentages)
        min_discovery_pct = min(node_discovery_percentages)
        max_discovery_pct = max(node_discovery_percentages)
        
        discovery_progress[checkpoint_time] = {
            'avg': avg_discovery_pct,
            'min': min_discovery_pct,
            'max': max_discovery_pct,
            'all': node_discovery_percentages.copy()
        }
        # --------------------------------------------------

        checkpoint_results[checkpoint_time] = (
            e_per_cycle,
            avg_time,
            avg_success,
            avg_syncs,
            avg_acks,
            sync_success_rate,
            success_disc_e,
            e_sync_per_cycle_cp,
        )
        
        for n in nodes:
            n.update_clock_drift()
    
    total_e_used = sum([n.kpi.e_total for n in nodes])
    total_e_discovery = sum([n.kpi.disc_e_receive + n.kpi.disc_e_send for n in nodes])
    total_e_sync = total_e_used - total_e_discovery
    sync_cycles = sum([n.kpi.disc_received + n.kpi.disc_sent for n in nodes])
    e_sync_per_cycle = total_e_sync / sync_cycles
    sim_days = max(checkpoints) / ONE_DAY

    avg_energy_per_day = total_e_used / NODES / sim_days
    average_energy_simulation = total_e_used / NODES
    
    print("\n=== ENERGY SUMMARY FOR THIS RUN ===")
    print(f"Total energy used by all nodes: {total_e_used:.5f} J")
    print(f"Average energy consumption for each node troughout all the simulation: {average_energy_simulation:.5f} J")
    print(f"Average energy used per node per day: {avg_energy_per_day:.5f} J/day")
    print("===================================")

    #EnergyLogger.plot(filename = f"v1_energy_plot_run_{run+1}")
    #NetworkTopology(Network.nodes).save(filename = f"v1_topology_run{run+1}")
    print(f"Simulation {run + 1} complete!\n\n")

    return checkpoint_results, avg_energy_per_day, e_sync_per_cycle, discovery_progress

def simulate(number_of_runs, duration_days, seed):
    checkpoints = [int(days * ONE_DAY) for days in duration_days]
    checkpoint_results_list = []
    avg_energy_days = []
    e_sync_per_cycle_runs = []
    discovery_data_all_runs = []  # NEW: Store discovery data from all runs

    for run in range(number_of_runs):
        current_seed = seed + run
        random.seed(current_seed)
        Network.nodes = []
        Network.mailboxes = {}
        
        print(f"Running simulation {run + 1}/{number_of_runs}... using SEED={current_seed}")
        checkpoint_data, avg_energy_per_day, e_sync_per_cycle, discovery_progress = simulate_with_checkpoints(checkpoints, run)
        checkpoint_results_list.append(checkpoint_data)
        discovery_data_all_runs.append(discovery_progress)  # NEW: Store discovery data
        avg_energy_days.append(avg_energy_per_day)
        e_sync_per_cycle_runs.append(e_sync_per_cycle)

    overall_avg_energy_per_day = mean(avg_energy_days)
    version_0_energyValue = 13.06808
    print("\n===== OVERALL AVERAGE ENERGY PER DAY (ALL RUNS) =====")
    print(f"Average energy used per node per day across ALL runs:", overall_avg_energy_per_day, "J")
    print(f"ESR:", (1 - (overall_avg_energy_per_day / version_0_energyValue)), "J")
    print("=====================================================\n")

    plotter = Plotter()
    results = plotter.evaluation(checkpoint_results_list)

    plotter.plot_results(results)
    plotter.plot_discovery_progress(discovery_data_all_runs, duration_days)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    figures_dir = os.path.join(current_dir, "../figures/")
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir)

    number_of_runs = RUNS
    duration_days = list(range(1, SIM_DAYS + 1))
    seed = SEED

    start_time = time.time()
    simulate(number_of_runs, duration_days, seed)
    end_time = time.time()
    print(f"Total simulation time: {end_time - start_time:.2f} seconds")