import matplotlib.pyplot as plt
from collections import defaultdict
import math
import os

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
    def plot(cls, filename="energy_plot.png", chunks_days = 3):
        if not cls.enabled:
            return
        
        os.makedirs("energy_plots", exist_ok=True)

        chunk_size = chunks_days * ONE_DAY
        num_chunks = math.ceil(SIM_TIME / chunk_size)

        if SIM_TIME >= ONE_DAY:
            time_divisor = ONE_DAY
            time_unit = "days"
        elif SIM_TIME >= ONE_DAY / 24:
            time_divisor = ONE_DAY / 24
            time_unit = "hours"
        else:
            time_divisor = 1000
            time_unit = "seconds"

        for chunk_idx in range(num_chunks):
            chunk_start = chunk_idx * chunk_size
            chunk_end = min((chunk_idx + 1) * chunk_size, SIM_TIME)

            plt.figure(figsize=(20, 7.5))
            
            max_energy = 0
            for node_id, records in cls.data.items():
                # Filter records within this chunk
                chunk_records = [(t, e) for t, e in records if chunk_start <= t < chunk_end]
                
                if not chunk_records:
                    continue
                    
                times, energies = zip(*chunk_records)
                max_energy = max(max_energy, max(energies))
                times_converted = [t / time_divisor for t in times]
                plt.plot(times_converted, energies, label=f"Node {node_id}")

            y_upper = max(max_energy * 1.15, E_TRESHOLD * 1.1) if max_energy > 0 else E_TRESHOLD * 1.1
            plt.ylim(0, y_upper)

            plt.axhline(y=E_TRESHOLD, color='black', linestyle='--', linewidth=1.5, label='Threshold')
            if E_MAX <= y_upper:
                plt.axhline(y=E_MAX, color='black', linestyle='--', linewidth=1.5, label='Max')

            # Set x-axis limits for this chunk
            plt.xlim(chunk_start / time_divisor, chunk_end / time_divisor)

            plt.xlabel(f"Time ({time_unit})")
            plt.ylabel("Energy (joules)")
            
            start_label = chunk_start / time_divisor
            end_label = chunk_end / time_divisor
            plt.title(f"Energy during Simulation ({start_label:.1f} - {end_label:.1f} {time_unit})")
            
            plt.legend(loc='upper left', fontsize='small', ncol=2)
            plt.grid(True)
            plt.tight_layout()

            # Save with chunk index in filename
            base_name = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'png'
            chunk_filename = os.path.join("energy_plots", f"{base_name}_{chunk_idx + 1}.{extension}")
            plt.savefig(chunk_filename)
            plt.close()