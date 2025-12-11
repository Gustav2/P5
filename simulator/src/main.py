import simpy, random
from statistics import mean
from tqdm import tqdm

from .node.node import Node
from .core.network import Network

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology

from .config import NODES, SIM_TIME, RANGE, ONE_DAY

def main():
    env = simpy.Environment()
    nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]

    chunk_size = SIM_TIME // 20 
    with tqdm(total=SIM_TIME, desc="Simulating", unit="time") as pbar:
        for t in range(0, SIM_TIME, chunk_size):
            env.run(until=min(t + chunk_size, SIM_TIME))
            pbar.update(chunk_size)

    kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]

    e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
    success_disc_e = mean([n.kpi.get_success_disc_e() for n in nodes])

    total_e_used = sum([node.kpi.e_total for node in nodes])

    print(f"Avg energy used per day: {total_e_used / NODES / (SIM_TIME / ONE_DAY)} J")
    print(f"Energy usage per DISC cycle: {e_per_cycle} J")
    print(f"Time till first DISC receive: {avg_time} sec")
    print(f"Energy per successfull DISC cycle: {success_disc_e} J")
    print(f"DISC success rate: {avg_success} %")

    tried_sync_with = sum(cycle["nodes"] for node in nodes for cycle in node.sync_cycles)
    total_packages_sent = 0
    for node in nodes:
        for cycle in node.sync_cycles:
            total_packages_sent += min(cycle["sync_received"] + cycle["acks_received"], cycle["nodes"])


    print(f"Sync success rate: {total_packages_sent / tried_sync_with * 100:.2f}%")

    EnergyLogger.plot(chunks_days=2)
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()