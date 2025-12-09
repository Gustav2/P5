from .core.network import Network
from .core.plotter import Plotter

from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology

def main():
    durations_to_test = list(range(1, 90))
    number_of_cycles = 2

    plotter = Plotter()
    results = plotter.evaluation(runs=number_of_cycles, duration_days=durations_to_test)
    plotter.plot_results(results)

    EnergyLogger.plot()
    NetworkTopology(Network.nodes).save()

if __name__ == "__main__":
    main()