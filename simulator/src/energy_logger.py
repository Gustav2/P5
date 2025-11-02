import matplotlib.pyplot as plt
from collections import defaultdict

from .config import E_TRESHOLD, E_MAX

class EnergyLogger:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.data = defaultdict(list)  # {node_id: [(time, energy), ...]}

    def log(self, node_id, time, energy):
        if self.enabled:
            self.data[node_id].append((time, energy))

    def plot(self, filename="energy_plot.png"):
        if not self.enabled:
            print("EnergyLogger is disabled.")
            return

        plt.figure(figsize=(15, 10))
        for node_id, records in self.data.items():
            times, energies = zip(*records)
            plt.plot(times, energies, label=f"Node {node_id}")

        plt.axhline(y=E_TRESHOLD, color='red', linestyle='--', linewidth=1, label='Energy Threshold')   
        plt.axhline(y=E_MAX, color='red', linestyle='--', linewidth=1, label='Energy Max')   

        plt.xlabel("Time")
        plt.ylabel("Energy (microA)")
        plt.title("Energy over Time for All Nodes")
        plt.legend(loc='upper right', fontsize='small', ncol=2)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filename)