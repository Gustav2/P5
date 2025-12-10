import matplotlib.pyplot as plt
import simpy, random
from statistics import mean
import numpy as np
from scipy import stats

from ..node.node import Node
from .network import Network

from ..config import NODES, RANGE,ONE_DAY,SEED

class Plotter:
    def __init__(self):
        self.results = {}

    def evaluation(self, runs, duration_days):
        checkpoints = [days * ONE_DAY for days in duration_days]

        for i in range(runs):
            current_seed=SEED+i
            random.seed(current_seed)
            Network.nodes = []
            Network.mailboxes = {}
            print(f"[INFO] Run {i+1} using SEED={current_seed}")
            checkpoint_data = self.simulate_with_checkpoints(checkpoints)
            
            for days, checkpoint_time in zip(duration_days, checkpoints):
                if days not in self.results:
                    self.results[days] = {'e': [], 't': [], 's': [], 's_list': []}
                
                e_per_cycle, avg_time, avg_success = checkpoint_data[checkpoint_time]
                self.results[days]['e'].append(e_per_cycle)
                self.results[days]['t'].append(avg_time)
                self.results[days]['s'].append(avg_success)
                self.results[days]['s_list'].append(avg_success)
                
                print("----------------------------")
                print(f"Simulation duration: {days} days (Run {i+1})")
                print(f"Energy Consumption per Discovery Cycle: {e_per_cycle} J")
                print(f"Discovery Latency: {avg_time} s")
                print(f"Discovery Success Rate: {avg_success} %")
        
        # Convert to averages
        for days in self.results:
            self.results[days] = (
                mean(self.results[days]['e']),
                mean(self.results[days]['t']),
                mean(self.results[days]['s']),
                self.results[days]['s_list']
            )
        
        return self.results

    def simulate_with_checkpoints(self, checkpoints):
        """Run simulation once and collect metrics at specified time intervals."""
        env = simpy.Environment()
        nodes = [Node(env, i, random.uniform(0,RANGE), random.uniform(0,RANGE)) for i in range(NODES)]
        
        for n in nodes:
            Network.register_node(n)

        checkpoint_results = {}
        
        for checkpoint_time in sorted(checkpoints):
            env.run(until = checkpoint_time)
            kpis = [n.kpi.get_disc_kpis(n.neighbors) for n in nodes]
            e_per_cycle, avg_time, avg_success = [mean(metric) for metric in zip(*kpis)]
            checkpoint_results[checkpoint_time] = (e_per_cycle, avg_time, avg_success)
        
        return checkpoint_results

    def plot_results(self, results): #New function bcs Andris plotting function won't work, and better to have a spearate one.
        days = list(results.keys())
        e_vals = [results[d][0] for d in days]
        t_vals = [results[d][1] for d in days]
        s_vals = [results[d][2] for d in days]
        s_list = [results[d][3] for d in days]
        overall_mean_success = mean(s_vals)
        overall_latency= mean(t_vals)
        overall_energy= mean(e_vals)
        print("\n==============================")
        print(f"Overall Discovery Success Rate: {overall_mean_success:.2f}%")
        print(f"Overall Latency {overall_latency:.2f}")
        print(f"Overall Energy: {overall_energy:.2f}")
        print("==============================\n")
        # Energy Graph
        plt.figure()
        plt.plot(days, e_vals, marker='o',color='orange')
        plt.title("Energy Consumption per Discovery Cycle vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy (J)")
        plt.grid(True)
        plt.savefig("energy_vs_days.png")

        # Latency Graph
        plt.figure()
        plt.plot(days, t_vals, marker='o',color='red')
        plt.title("Discovery Latency vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Latency (s)")
        plt.grid(True)
        plt.savefig("latency_vs_days.png")

        # Success Rate Graph
        plt.figure()
        plt.plot(days, s_vals, marker='o')
        plt.title("Discovery Success Rate vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Success Rate (%)")
        plt.grid(True)
        plt.savefig("success_vs_days.png")

        # Success of all runs graph, with 95% CI
        plt.figure()

        # s_list is a list of length n_days, each entry is a list of success rates over runs for that day
        # Shape it into (n_days, n_runs)
        s_array = np.array(s_list)              # shape: (n_days, n_runs)
        n_runs = s_array.shape[1]

        # Mean per day (across runs)
        means = s_array.mean(axis=1)
        print("Mean:",means)
        # Sample standard deviation per day (ddof=1 → unbiased estimate)
        stds = s_array.std(axis=1, ddof=1)

        # 95% CI using t-distribution
        alpha = 0.05
        dof = n_runs - 1
        t_crit = stats.t.ppf(1 - alpha/2, dof)  # two-sided critical t value

        # Margin of error
        margin = t_crit * stds / np.sqrt(n_runs)
        lower = means - margin
        upper = means + margin

        # Optional: keep the individual run lines (faint)
        for run_index, day_success_rates in enumerate(zip(*s_list)):
            plt.plot(days, day_success_rates, alpha=0.3, label=f'Run {run_index+1}')

        # Plot mean success rate
        plt.plot(days, means, marker='o', linewidth=2, label='Mean success rate')

        # Plot 95% CI as shaded band
        plt.fill_between(days, lower, upper, alpha=0.2, label='95% CI')
        plt.title("Discovery Success Rate (All Runs) vs Duration\n(with 95% CI across runs)")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Success Rate (%)")
        plt.legend()
        plt.grid(True)
        plt.savefig("success_list_vs_days.png")