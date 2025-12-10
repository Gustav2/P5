import simpy, random
from statistics import mean

from .node.node import Node
from .core.network import Network

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology
from .core.plotter import Plotter

from .config import NODES, SIM_TIME, RANGE, ONE_DAY

def simulate_with_checkpoints(checkpoints):
    """Run simulation once and collect metrics at specified time intervals."""
    checkpoint_results = {}
    
    for checkpoint_time in sorted(checkpoints):
        env = simpy.Environment()
        nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
        
        Network.nodes.clear()
        for n in nodes:
            Network.register_node(n)
        
        env.run(until=checkpoint_time)
        
        kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]
        e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
        success_disc_e = mean([n.kpi.get_success_disc_e() for n in nodes])
        
        # Sync metrics from node.sync_cycles
        tried_sync_with = sum(cycle["nodes"] for node in nodes for cycle in node.sync_cycles)
        total_sync = sum(cycle["sync_received"] for node in nodes for cycle in node.sync_cycles)
        total_ack = sum(cycle["acks_received"] for node in nodes for cycle in node.sync_cycles)
        
        avg_syncs = mean([cycle["sync_received"] for node in nodes for cycle in node.sync_cycles]) if total_sync > 0 else 0
        avg_acks = mean([cycle["acks_received"] for node in nodes for cycle in node.sync_cycles]) if total_ack > 0 else 0
        sync_success_rate = (total_ack / tried_sync_with * 100) if tried_sync_with > 0 else 0

        checkpoint_results[checkpoint_time] = (e_per_cycle, avg_time, avg_success, avg_syncs, avg_acks, sync_success_rate, success_disc_e)
    
    return checkpoint_results

def main():
    num_runs = 3
    duration_days = list(range(1, 11))
    checkpoints = [int(days * ONE_DAY) for days in duration_days]

    checkpoint_results_list = []

    # Run multiple simulations
    for run in range(num_runs):
        print(f"Running simulation {run + 1}/{num_runs}...")
        checkpoint_data = simulate_with_checkpoints(checkpoints)
        checkpoint_results_list.append(checkpoint_data)
        print(f"Simulation {run + 1} complete!")

    """print(f"Energy usage per DISC cycle: {e_per_cycle} J")
    print(f"Time till first DISC receive: {avg_time} sec")
    print(f"Energy per successfull DISC cycle: {success_disc_e} J")
    print(f"DISC success rate: {avg_success} %")

    tried_sync_with = sum(cycle["nodes"] for node in nodes for cycle in node.sync_cycles)
    total_sync = sum(cycle["sync_received"] for node in nodes for cycle in node.sync_cycles)
    total_ack = sum(cycle["acks_received"] for node in nodes for cycle in node.sync_cycles)

    print(f"Avg SYNCs tries: {mean(cycle["sync_received"] for node in nodes for cycle in node.sync_cycles)}")
    print(f"Avg ACKs received: {mean(cycle["acks_received"] for node in nodes for cycle in node.sync_cycles)}")
    print(f"ACKs per SYNC/ACK rate: {(total_sync + total_ack) / tried_sync_with * 100:.1f} %") # sync success rate"""

    plotter = Plotter()
    results = plotter.evaluation(checkpoint_results_list)
    plotter.plot_results(results)

    EnergyLogger.plot(chunks_days=2)
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()