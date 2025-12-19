import matplotlib.pyplot as plt
import numpy as np

from statistics import mean
from scipy import stats

from ..config import ONE_DAY, RUNS, NODES

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
        plt.title("Energy Consumption per DISC Cycle as a function of Simulation Duration", fontsize=14, fontweight='bold')
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy (J)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("figures/v1_energy_consumption_disc_cycle_vs_duration.png", dpi=300, bbox_inches='tight')

        # Energy for successfull discovery Graph
        #plt.figure()
        #plt.plot(days, success_disc_e, marker='o',color='orange')
        #plt.title("Energy Consumption per Successful Discovery Cycle vs Duration", fontsize=14, fontweight='bold')
        #plt.xlabel("Simulation Duration (days)")
        #plt.ylabel("Energy (J)")
        #plt.grid(True)
        #plt.tight_layout()
        #plt.savefig("figures/energy_success_vs_days.png", dpi=300, bbox_inches='tight')

        # Latency Graph
        #plt.figure()
        #plt.plot(days, t_vals, marker='o',color='red')
        #plt.title("Discovery Latency vs Duration", fontsize=14, fontweight='bold')
        #plt.xlabel("Simulation Duration (days)")
        #plt.ylabel("Latency (s)")
        #plt.grid(True)
        #plt.tight_layout()
        #plt.savefig("figures/latency_vs_days.png", dpi=300, bbox_inches='tight')

        # Success Rate Graph
        #plt.figure()
        #plt.plot(days, s_vals, marker='o')
        #plt.title("Discovery Success Rate vs Duration", fontsize=14, fontweight='bold')
        #plt.xlabel("Simulation Duration (days)")
        #plt.ylabel("Success Rate (%)")
        #plt.grid(True)
        #plt.tight_layout()
        #plt.savefig("figures/success_vs_days.png", dpi=300, bbox_inches='tight')

        # Success of all runs graph, with 95% CI
        plt.figure()

        # s_list is a list of length n_days, each entry is a list of success rates over runs for that day
        # Shape it into (n_days, n_runs)
        s_array = np.array(s_list)              # shape: (n_days, n_runs)
        n_runs = s_array.shape[1]

        # Mean per day (across runs)
        means = s_array.mean(axis=1)

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
        plt.title("Discovery Success Rate as a function of Simulation Duration\n(with 95% CI across runs)", fontsize=14, fontweight='bold')
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("DISC Success Rate (%)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("figures/v1_disc_success_vs_duration.png", dpi=300, bbox_inches='tight')

        # SYNC Tries Graph
        #plt.figure()
        #plt.plot(days, sync_tries_vals, marker='o', color='green')
        #plt.title("Average SYNCs Sent vs Duration", fontsize=14, fontweight='bold')
        #plt.xlabel("Simulation Duration (days)")
        #plt.ylabel("Average SYNCs Sent")
        #plt.grid(True)
        #plt.tight_layout()
        #plt.savefig("figures/sync_tries_vs_days.png", dpi=300, bbox_inches='tight')

        # ACKs Received Graph
        #plt.figure()
        #plt.plot(days, acks_vals, marker='o', color='blue')
        #plt.title("Average SYNC ACKs Received vs Duration", fontsize=14, fontweight='bold')
        #plt.xlabel("Simulation Duration (days)")
        #plt.ylabel("Average SYNC ACKs Received")
        #plt.grid(True)
        #plt.tight_layout()
        #plt.savefig("figures/acks_vs_days.png", dpi=300, bbox_inches='tight')

        # SYNC Success Rate Graph
        #plt.figure()
        #plt.plot(days, sync_success_vals, marker='o', color='purple')
        #plt.title("Discovery Success Rate vs Duration", fontsize=14, fontweight='bold')
        #plt.xlabel("Simulation Duration (days)")
        #plt.ylabel("SYNC Success Rate (%)")
        #plt.grid(True)
        #plt.tight_layout()
        #plt.savefig("figures/sync_success_vs_days.png", dpi=300, bbox_inches='tight')

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
        plt.title("SYNC Success Rate as a function of Simulation Duration\n(with 95% CI across runs)", fontsize=14, fontweight='bold')
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("SYNC Success Rate (%)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("figures/v1_sync_success_vs_duration.png", dpi=300, bbox_inches='tight')

        # Energy Consumption per SYNC Cycle Graph
        plt.figure()
        plt.plot(days, e_sync_per_cycle_vals, marker='o')
        plt.title("Energy Consumption per SYNC Cycle as a function of Simulation Duration", fontsize=14, fontweight='bold')
        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy per Sync Cycle (J)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("figures/v1_energy_consumption_sync_cycle_vs_duration.png", dpi=300, bbox_inches='tight')

    def plot_discovery_progress(self, discovery_data_all_runs, duration_days):
        """
        Plot discovery progress averaged across all runs.
        
        Args:
            discovery_data_all_runs: List of discovery_progress dicts from each run
            duration_days: List of checkpoint days
        """
        days = np.array(duration_days)
        
        # Aggregate data across runs
        avg_discovery = []
        min_discovery = []
        max_discovery = []
        std_discovery = []
        
        for day in duration_days:
            checkpoint_time = int(day * ONE_DAY)
            
            # Collect avg discovery from all runs for this checkpoint
            run_avgs = [run_data[checkpoint_time]['avg'] for run_data in discovery_data_all_runs]
            run_mins = [run_data[checkpoint_time]['min'] for run_data in discovery_data_all_runs]
            run_maxs = [run_data[checkpoint_time]['max'] for run_data in discovery_data_all_runs]
            
            avg_discovery.append(mean(run_avgs))
            min_discovery.append(mean(run_mins))
            max_discovery.append(mean(run_maxs))
            std_discovery.append(np.std(run_avgs))
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot average discovery line
        ax.plot(days, avg_discovery, 'b-', linewidth=2.5, label='Average Discovery', zorder=10)
        
        # Add shaded region for min-max range
        #ax.fill_between(days, min_discovery, max_discovery, alpha=0.2, color='blue', label='Min-Max Range')
        
        # Add standard deviation band
        avg_array = np.array(avg_discovery)
        std_array = np.array(std_discovery)
        #ax.fill_between(days, avg_array - std_array, avg_array + std_array, alpha=0.15, color='green', label='±1 Std Dev')
        
        # Formatting
        ax.set_xlabel('Duration (Days)')
        ax.set_ylabel('Total Nodes Discovered (%)')
        ax.set_title(f'Total Node Discovery Progress Over Time\n({RUNS} runs, {NODES} nodes)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower right')
        #ax.set_ylim(0, 105)
        #ax.set_xlim(days[0], days[-1])
        
        plt.tight_layout()
        plt.savefig('figures/v1_discovery_progress.png', dpi=300, bbox_inches='tight')
        
        # Print summary statistics
        print(f"\n=== Discovery Progress Summary ===")
        print(f"Final average discovery: {avg_discovery[-1]:.2f}%")
        print(f"Final min discovery: {min_discovery[-1]:.2f}%")
        print(f"Final max discovery: {max_discovery[-1]:.2f}%")
        print(f"Standard deviation at end: {std_discovery[-1]:.2f}%")
        print("==================================\n")