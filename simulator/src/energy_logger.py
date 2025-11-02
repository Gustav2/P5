import matplotlib.pyplot as plt
from collections import defaultdict

from .config import E_TRESHOLD, E_MAX

class EnergyLogger:
    enabled = True
    data = defaultdict(list)

    @classmethod
    def log(cls, node_id, time, energy):
        if cls.enabled:
            cls.data[node_id].append((time, energy))

    @classmethod
    def disable(cls):
        cls.enabled = False

    @classmethod
    def plot(cls, filename="energy_plot.png"):
        if not cls.enabled:
            print("EnergyLogger is disabled.")
            return

        plt.figure(figsize=(15, 10))
        for node_id, records in cls.data.items():
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