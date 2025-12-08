from .core.energy_logger import EnergyLogger
from .core.network_topology import NetworkTopology
from .core.plotter import Plotter

def plot(Network):
    EnergyLogger.plot()
    topo = NetworkTopology(Network.nodes)
    topo.save("topology.png")    


if __name__ == "__main__":

    durations_to_test = list(range(3, 10)) #Careful with the days, the simulation will take a very very long time, and eat your computer's resources ASAP
    number_of_cycles = 4 #Also be careful lol

    plotter = Plotter()
    results = plotter.evaluation(runs=number_of_cycles, duration_days=durations_to_test)
    plotter.plot_results(results)
    
    #res = evaluation(number_of_cycles,durations_to_test)
    #plot_results(res)

    #results = evaluate_multiple_durations(durations_to_test, runs_per_duration=4)