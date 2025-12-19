import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import pickle


class ComparisonPlotter:
    def __init__(self, results_no_drift, results_drift):
        """
        Args:
            results_no_drift: output of Plotter.evaluation() with clock drift disabled
            results_drift:    output of Plotter.evaluation() with clock drift enabled
        """
        self.no_drift = results_no_drift
        self.drift = results_drift
        self.scale = 50

        # Ensure same ordering
        common_days = set(results_no_drift.keys()) & set(results_drift.keys())

        if not common_days:
            raise ValueError("No common checkpoints between drift and no-drift results")

        self.days = sorted(common_days)

    def _compute_ci(self, value_lists):
        """
        Compute mean and 95% CI across runs.
        value_lists shape: (n_days, n_runs)
        """
        arr = np.array(value_lists)
        means = arr.mean(axis=1)
        stds = arr.std(axis=1, ddof=1)

        n = arr.shape[1]
        t_crit = stats.t.ppf(0.975, n - 1)
        margin = t_crit * stds / np.sqrt(n)

        return means, means - margin, means + margin

    # ------------------------------------------------------------------

    def plot_discovery_success_comparison(self):
        """
        Overlay DISC success rate with and without clock drift
        """

        # Extract success lists
        s_no_drift = [self.no_drift[d][3] for d in self.days]
        s_drift = [self.drift[d][3] for d in self.days]

        mean_nd, low_nd, up_nd = self._compute_ci(s_no_drift)
        mean_d, low_d, up_d = self._compute_ci(s_drift)

        plt.figure()

        # No drift
        plt.plot(self.days, mean_nd, linewidth=2, label="No clock drift")
        plt.fill_between(self.days, low_nd, up_nd, alpha=0.2)

        # With drift
        plt.plot(self.days, mean_d, linestyle="--", linewidth=2, label="Clock drift enabled")
        plt.fill_between(self.days, low_d, up_d, alpha=0.2)

        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("DISC Success Rate (%)")
        plt.title("Impact of Clock Drift on Discovery Success Rate", fontweight="bold")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        plt.savefig(
            "figures/v1_compare_disc_success_clock_drift.png",
            dpi=300,
            bbox_inches="tight"
        )

    # ------------------------------------------------------------------

    def plot_sync_success_comparison(self):
        """
        Overlay SYNC success rate with and without clock drift
        """

        sync_no_drift = [self.no_drift[d][7] for d in self.days]
        sync_drift = [self.drift[d][7] for d in self.days]

        mean_nd, low_nd, up_nd = self._compute_ci(sync_no_drift)
        mean_d, low_d, up_d = self._compute_ci(sync_drift)

        plt.figure()

        plt.plot(self.days, mean_nd, linewidth=2, label="No clock drift")
        plt.fill_between(self.days, low_nd, up_nd, alpha=0.2)

        plt.plot(self.days, mean_d, linestyle="--", linewidth=2, label="Clock drift enabled")
        plt.fill_between(self.days, low_d, up_d, alpha=0.2)

        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("SYNC Success Rate (%)")
        plt.title("Impact of Clock Drift on SYNC Success Rate", fontweight="bold")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        plt.savefig(
            "figures/v1_compare_sync_success_clock_drift.png",
            dpi=300,
            bbox_inches="tight"
        )

    # ------------------------------------------------------------------

    def plot_energy_per_cycle_comparison(self):
        """
        Overlay energy consumption per DISC cycle
        """

        e_no_drift = [self.no_drift[d][0] / self.scale for d in self.days]
        e_drift = [self.drift[d][0] / self.scale for d in self.days]

        plt.figure()

        plt.plot(self.days, e_no_drift, linewidth=2, label="No clock drift")
        plt.plot(self.days, e_drift, linestyle="--", linewidth=2, label="Clock drift enabled")

        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy per DISC Cycle (J)")
        plt.title("Impact of Clock Drift on Energy Consumption", fontweight="bold")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        plt.savefig(
            "figures/v1_compare_energy_disc_cycle_clock_drift.png",
            dpi=300,
            bbox_inches="tight"
        )

    def plot_energy_per_cycle_comparison(self):
        """
        Overlay energy consumption per DISC cycle
        """

        e_no_drift = [self.no_drift[d][9] / self.scale for d in self.days]
        e_drift = [self.drift[d][9] / self.scale for d in self.days]

        plt.figure()

        plt.plot(self.days, e_no_drift, linewidth=2, label="No clock drift")
        plt.plot(self.days, e_drift, linestyle="--", linewidth=2, label="Clock drift enabled")

        plt.xlabel("Simulation Duration (days)")
        plt.ylabel("Energy per SYNC Cycle (J)")
        plt.title("Impact of Clock Drift on Energy Consumption", fontweight="bold")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        plt.savefig(
            "figures/v1_compare_energy_sync_cycle_clock_drift.png",
            dpi=300,
            bbox_inches="tight"
        )


with open("results/results_drift_off.pkl", "rb") as f:
    results_no_drift = pickle.load(f)

with open("results/results_drift_on.pkl", "rb") as f:
    results_drift = pickle.load(f)

cmp = ComparisonPlotter(results_no_drift, results_drift)

cmp.plot_discovery_success_comparison()
cmp.plot_sync_success_comparison()
cmp.plot_energy_per_cycle_comparison()

print("Comparison plots saved.")