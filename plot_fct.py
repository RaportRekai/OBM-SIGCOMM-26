import re
import numpy as np
import matplotlib.pyplot as plt
import os

# ============================================================
# Configuration
# ============================================================

ABM_FILE = "stats_abm.txt"
LQD_FILE = "stats_lqd.txt"

LOADS = [0.3, 0.6, 0.9]

BAR_WIDTH = 0.36


# ============================================================
# Extract the LAST occurrence of each Websearch workload
# ============================================================

def extract_p99_short_fct(filename):
    """
    Returns:
        {
            0.3: p99_value,
            0.6: p99_value,
            0.9: p99_value
        }

    If the same workload appears multiple times, the LAST
    occurrence in the file is used.
    """

    results = {}

    # Matches:
    # workloads/websearch-trace-100G-load-0.3.csv.processed
    workload_pattern = re.compile(
        r"websearch-trace-100G-load-(0\.3|0\.6|0\.9)\.csv\.processed"
    )

    # Matches:
    # p99 FCT short flows: 126.776us
    p99_pattern = re.compile(
        r"p99 FCT short flows:\s*([0-9.]+)us"
    )

    current_load = None

    with open(filename, "r") as f:
        for line in f:

            # Did we encounter a Websearch workload?
            workload_match = workload_pattern.search(line)

            if workload_match:
                current_load = float(workload_match.group(1))
                continue

            # Look for p99 belonging to that workload
            if current_load is not None:
                p99_match = p99_pattern.search(line)

                if p99_match:
                    value = float(p99_match.group(1))

                    # Overwrite previous value.
                    # Therefore the LAST occurrence wins.
                    results[current_load] = value

                    current_load = None

    return results




def plot_fct(abm_values, lqd_values, output_name="abm_lqd_p99_fct"):

    """

    Plot ABM vs LQD FCT for network loads 0.3, 0.6, and 0.9.

    Example:

        abm_values = [250, 630, 1140]

        lqd_values = [160, 450, 950]

        plot_fct(abm_values, lqd_values)

    """

    loads = [0.3, 0.6, 0.9]

    x = np.arange(len(loads))

    width = 0.36

    fig, ax = plt.subplots(figsize=(6.5, 5.5))

    # Bars

    ax.bar(

        x - width / 2,

        abm_values,

        width,

        label="ABM",

        color="#FFD700",

        edgecolor="black",

        linewidth=0.8

    )

    ax.bar(

        x + width / 2,

        lqd_values,

        width,

        label="LQD",

        color="#32CD32",

        edgecolor="black",

        linewidth=0.8

    )

    # Axes

    ax.set_xlabel("Network Load", fontsize=22)

    ax.set_ylabel("99-perc. FCT (µs)", fontsize=22)

    ax.set_xticks(x)

    ax.set_xticklabels(

        ["0.3", "0.6", "0.9"],

        fontsize=20

    )

    # Y-axis: 0, 200, 400, ..., 1200

    ax.set_ylim(0, 1400)

    ax.set_yticks(np.arange(0, 1201, 200))

    ax.tick_params(axis="y", labelsize=20)

    # Grid

    ax.grid(

        axis="y",

        linestyle=":",

        linewidth=0.6,

        alpha=0.5

    )

    ax.set_axisbelow(True)

    # Legend

    ax.legend(

        loc="upper left",

        fontsize=18,

        ncol=2,

        frameon=True,

        edgecolor="gray",

        columnspacing=1.0,

        handlelength=1.6

    )

    plt.tight_layout()

    # Save both formats

    plt.savefig(

        f"{output_name}.pdf",

        bbox_inches="tight"

    )

    plt.savefig(

        f"{output_name}.png",

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



# ============================================================
# Read files
# ============================================================
ABM_FILE = os.path.join('./obm-sim-websearch-priority-shared', ABM_FILE)
LQD_FILE = os.path.join('./obm-sim-websearch-priority-shared', LQD_FILE)
abm = extract_p99_short_fct(ABM_FILE)
lqd = extract_p99_short_fct(LQD_FILE)

print("Last ABM values:", abm)
print("Last LQD values:", lqd)


# Make sure all loads were found
for load in LOADS:
    if load not in abm:
        raise ValueError(
            f"Could not find Websearch load {load} in {ABM_FILE}"
        )

    if load not in lqd:
        raise ValueError(
            f"Could not find Websearch load {load} in {LQD_FILE}"
        )


abm_values = [abm[load] for load in LOADS]
lqd_values = [lqd[load] for load in LOADS]

plot_fct(abm_values, lqd_values, output_name="abm_lqd_p99_fct_priority")


ABM_FILE = os.path.join('./obm-sim-websearch-n-priority-shared', ABM_FILE)
LQD_FILE = os.path.join('./obm-sim-websearch-n-priority-shared', LQD_FILE)
abm = extract_p99_short_fct(ABM_FILE)
lqd = extract_p99_short_fct(LQD_FILE)

print("Last ABM values:", abm)
print("Last LQD values:", lqd)


# Make sure all loads were found
for load in LOADS:
    if load not in abm:
        raise ValueError(
            f"Could not find Websearch load {load} in {ABM_FILE}"
        )

    if load not in lqd:
        raise ValueError(
            f"Could not find Websearch load {load} in {LQD_FILE}"
        )


abm_values = [abm[load] for load in LOADS]
lqd_values = [lqd[load] for load in LOADS]

plot_fct(abm_values, lqd_values, output_name="abm_lqd_p99_fct_n_priority")
