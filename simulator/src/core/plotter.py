import matplotlib.pyplot as plt
import numpy as np

from statistics import mean
from scipy import stats

from ..config import ONE_DAY

class Plotter:
    def __init__(self):
        self.results = {}

    def evaluation(self, checkpoint_results_list):
        """
        Process pre-computed simulation results and aggregate them.
        
        Args:
            checkpoint_results_list: List of dicts from simulate_with_checkpoints()
                                    Each dict maps checkpoint_time -> (e_per_cycle, avg_time, avg_success, ...)
        """
        for run_index, checkpoint_data in enumerate(checkpoint_results_list):
            for checkpoint_time, (e_per_cycle, avg_time, avg_success, avg_syncs, avg_acks, sync_success_rate, success_disc_e,e_sync_per_cycle) in checkpoint_data.items():
                days = checkpoint_time / ONE_DAY

                if days not in self.results:
                    self.results[days] = {
                        'e': [], 
                        't': [], 
                        's': [], 
                        's_list': [],
                        'sync_tries': [], 
                        'acks_received': [], 
                        'sync_success': [],
                        'sync_success_list': [], 
                        'success_disc_e': [],
                        'e_sync_per_cycle': []

                    }
                
                e_per_cycle, avg_time, avg_success, avg_syncs, avg_acks, sync_success_rate, success_disc_e,e_sync_per_cycle = checkpoint_data[checkpoint_time]
                self.results[days]['e'].append(e_per_cycle)
                self.results[days]['t'].append(avg_time)
                self.results[days]['s'].append(avg_success)
                self.results[days]['s_list'].append(avg_success)
                self.results[days]['sync_tries'].append(avg_syncs)
                self.results[days]['acks_received'].append(avg_acks)
                self.results[days]['sync_success'].append(sync_success_rate)
                self.results[days]['sync_success_list'].append(sync_success_rate)
                self.results[days]['success_disc_e'].append(success_disc_e)
                self.results[days]['e_sync_per_cycle'].append(e_sync_per_cycle)
                
                #print("----------------------------")
                #print(f"Simulation duration: {days} days (Run {run_index+1})")
                #print(f"Energy Consumption per Discovery Cycle: {e_per_cycle} J")
                #print(f"Energy Consumption per Successful Discovery Cycle: {success_disc_e} J")
                #print(f"Discovery Latency: {avg_time} s")
                #print(f"Discovery Success Rate: {avg_success} %")
                #print(f"Avg SYNCs sent: {avg_syncs}")
                #print(f"Avg ACKs received: {avg_acks}")
                #print(f"Sync success rate: {sync_success_rate} %")
                #print(f"e_sync_per_cycle {sync_success_rate} %")
        
        # Convert to averages
        for days in self.results:
            self.results[days] = (
                mean(self.results[days]['e']),
                mean(self.results[days]['t']),
                mean(self.results[days]['s']),
                self.results[days]['s_list'],
                mean(self.results[days]['sync_tries']),
                mean(self.results[days]['acks_received']),
                mean(self.results[days]['sync_success']),
                self.results[days]['sync_success_list'],
                mean(self.results[days]['success_disc_e']),
                mean(self.results[days]['e_sync_per_cycle']) 
            )
        
        return self.results
    
    def plot_results(self, results): #New function bcs Andris plotting function won't work, and better to have a spearate one.
        days = list(results.keys())
        e_vals = [results[d][0] for d in days]
        t_vals = [results[d][1] for d in days]
        s_vals = [results[d][2] for d in days]
        s_list = [results[d][3] for d in days]
        sync_tries_vals = [results[d][4] for d in days]
        acks_vals = [results[d][5] for d in days]
        sync_success_vals = [results[d][6] for d in days]
        sync_success_list = [results[d][7] for d in days]
        success_disc_e = [results[d][8] for d in days]
        e_sync_per_cycle_vals = [results[d][9] for d in days]
        
        overall_mean_success = mean(s_vals)
        overall_latency = mean(t_vals)
        overall_energy = mean(e_vals)
        overall_acks_vals = mean(acks_vals)
        overall_sync_tries_vals = mean(sync_tries_vals)
        overall_sync_success_vals = mean(sync_success_vals)
        overall_success_disc_e = mean(success_disc_e)
        overall_e_sync_per_cycle = mean(e_sync_per_cycle_vals)

        print("\n==============================")
        print("      OVERALL KPI SUMMARY     ")
        print("==============================")
        print(f"Overall Discovery Success Rate:   {overall_mean_success:.2f}%")
        print(f"Overall Latency (s):              {overall_latency:.2f}")
        print(f"Overall Energy per Cycle (J):     {overall_energy:.5f}")
        print(f"Overall ACKs Received:            {overall_acks_vals:.2f}")
        print(f"Overall Sync Attempts:            {overall_sync_tries_vals:.2f}")
        print(f"Overall Sync Successes:           {overall_sync_success_vals:.2f}%")
        print(f"Energy per Successful Discovery:  {overall_success_disc_e:.5f} J")
        print(f"Energy per Successful Discovery:  {overall_success_disc_e:.5f} J")
        print(f"Energy per Sync Cycle (mean):     {overall_e_sync_per_cycle:.5f} J/cycle")
        print("==============================\n")

        # Energy Graph
        plt.figure()
        plt.plot(days, e_vals, marker='o',color='orange')
        plt.title("Energy Consumption per Discovery Cycle vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy (J)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("energy_vs_days.png")

        # Energy for successfull discovery Graph
        plt.figure()
        plt.plot(days, success_disc_e, marker='o',color='orange')
        plt.title("Energy Consumption per Successful Discovery Cycle vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy (J)")
        plt.grid(True)
        plt.savefig("energy_success_vs_days.png")

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
        plt.savefig("disc_success_vs_days.png")

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
        plt.savefig("disc_success_list_vs_days.png")

        # SYNC Tries Graph
        plt.figure()
        plt.plot(days, sync_tries_vals, marker='o', color='green')
        plt.title("Average SYNCs Sent vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Average SYNCs Sent")
        plt.grid(True)
        plt.savefig("sync_tries_vs_days.png")

        # ACKs Received Graph
        plt.figure()
        plt.plot(days, acks_vals, marker='o', color='blue')
        plt.title("Average ACKs Received vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Average ACKs Received")
        plt.grid(True)
        plt.savefig("acks_vs_days.png")

        # SYNC Success Rate Graph
        plt.figure()
        plt.plot(days, sync_success_vals, marker='o', color='purple')
        plt.title("SYNC Success Rate (All Runs) vs Duration\n(with 95% CI across runs)")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("SYNC Success Rate (%)")
        plt.grid(True)
        plt.savefig("sync_success_vs_days.png")

        # SYNC Success Rate Graph with 95% CI
        plt.figure()
        
        # Convert sync_success_list to array: shape (n_days, n_runs)
        sync_array = np.array(sync_success_list)
        means_sync = sync_array.mean(axis=1)
        stds_sync = sync_array.std(axis=1, ddof=1)
        
        alpha = 0.05
        dof = sync_array.shape[1] - 1
        t_crit = stats.t.ppf(1 - alpha/2, dof)
        margin_sync = t_crit * stds_sync / np.sqrt(sync_array.shape[1])
        lower_sync = means_sync - margin_sync
        upper_sync = means_sync + margin_sync
        
        # Optional: keep the individual run lines (faint)
        for run_index, day_success_rates in enumerate(zip(*sync_success_list)):
            plt.plot(days, day_success_rates, alpha=0.3, label=f'Run {run_index+1}')

        plt.plot(days, means_sync, marker='o', linewidth=2, label='Mean sync success rate')
        plt.fill_between(days, lower_sync, upper_sync, alpha=0.2, label='95% CI')
        plt.title("SYNC Success Rate vs Duration\n(with 95% CI across runs)")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("SYNC Success Rate (%)")
        plt.legend()
        plt.grid(True)
        plt.savefig("sync_success_list_vs_days.png")
        
        plt.figure()
        plt.plot(days, e_sync_per_cycle_vals, marker='o')
        plt.title("Energy Consumption per SYNC Cycle vs Duration")
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy per Sync Cycle (J)")
        plt.grid(True)
        plt.savefig("Energy_Consumption_per_SYNC_Cycle_vs_Duration.png")