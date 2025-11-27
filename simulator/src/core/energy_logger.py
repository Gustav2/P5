import matplotlib.pyplot as plt
from collections import defaultdict
import math

from ..config import *

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
            return

        width = math.floor(SIM_TIME / ONE_DAY)
        plt.figure(figsize=(max(20, width * 30), 7.5))
        
        for node_id, records in cls.data.items():
            times, energies = zip(*records)
            plt.plot(times, energies, label=f"Node {node_id}")

        plt.axhline(y=E_TRESHOLD, color='black', linestyle='--', linewidth=1.5, label='Threshold')   
        plt.axhline(y=E_MAX, color='black', linestyle='--', linewidth=1.5, label='Max')

        plt.xlabel("Time (miliseconds)")
        plt.ylabel("Energy (joules)")
        plt.title("Energy during Simulation")
        plt.legend(loc='upper left', fontsize='small', ncol=2)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(filename)