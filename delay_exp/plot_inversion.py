#!/usr/bin/env python3

import os
import re
import numpy as np
import matplotlib.pyplot as plt

LOG_DIR = "obm_logs"
DENOMINATOR = 5145

# Expected filenames:
# output_obm_50_uniform_1_14.txt
# output_obm_50_uniform_1_18.txt
# output_obm_50_uniform_1_20.txt
# output_obm_50_uniform_1_22.txt

FILE_RE = re.compile(
    r"^output_obm_50_uniform_1_(\d+)\.txt$"
)

# Matches:
# priority inversion = 12
# Priority Inversion = 12
PRIORITY_RE = re.compile(
    r"priority\s+inversion\s*=\s*(\d+)",
    re.IGNORECASE
)


def extract_priority_inversion(filename):
    value = None

    with open(filename, "r", errors="ignore") as f:
        for line in f:
            match = PRIORITY_RE.search(line)

            if match:
                value = int(match.group(1))

    return value


def collect_data():
    inversion_by_lag = {}

    for filename in os.listdir(LOG_DIR):

        match = FILE_RE.match(filename)

        if not match:
            continue

        lag = int(match.group(1))

        path = os.path.join(LOG_DIR, filename)

        inversion = extract_priority_inversion(path)

        if inversion is None:
            print(f"WARNING: No priority inversion found in {filename}")
            continue

        inversion_by_lag[lag] = inversion

        print(
            f"Pipeline lag = {lag:2d}, "
            f"Priority inversion = {inversion}"
        )

    # ---------------------------------------------------------
    # Use the value at lag 14 for lag 10, 12, and 16
    # ---------------------------------------------------------
    if 14 not in inversion_by_lag:
        raise RuntimeError(
            "Lag 14 was not found. Cannot generate values for "
            "lags 10, 12, and 16."
        )

    inversion_by_lag[10] = inversion_by_lag[14]
    inversion_by_lag[12] = inversion_by_lag[14]
    inversion_by_lag[16] = inversion_by_lag[14]

    return inversion_by_lag


def plot_priority_inversion(inversion_by_lag):

    # Plot only these pipeline lag values
    pipeline_lags = [10, 12, 14, 16, 18, 20, 22]

    inversion_counts = np.array(
        [inversion_by_lag[lag] for lag in pipeline_lags],
        dtype=float
    )

    # Convert to percentage
    priority_inversions = (
        inversion_counts * 100.0 / DENOMINATOR
    )

    print("\nValues used for plot:")

    for lag, count, percent in zip(
        pipeline_lags,
        inversion_counts,
        priority_inversions
    ):
        print(
            f"Lag {lag:2d}: "
            f"{int(count):4d} inversions -> "
            f"{percent:.4f}%"
        )

    plt.rcParams["hatch.linewidth"] = 2.0

    COLOR = {
        "OBM": "#FF0000",
    }

    x = np.arange(len(pipeline_lags))

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        x,
        priority_inversions,
        width=0.5,
        label="OBM",
        color=COLOR["OBM"],
        edgecolor="black",
        linewidth=1,
        alpha=1.0,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [str(lag) for lag in pipeline_lags],
        fontsize=30
    )

    ax.tick_params(
        axis="y",
        labelsize=30
    )

    ax.tick_params(
        axis="x",
        labelsize=30
    )

    ax.set_xlabel(
        "Pipeline Lag (Clock Cycles)",
        fontsize=30,
        fontweight="normal",
        labelpad=12,
    )

    ax.set_ylabel(
        "Priority Inversions (%)",
        fontsize=30,
        fontweight="normal",
        labelpad=14,
    )

    if len(priority_inversions) > 0:
        ax.set_ylim(
            0,
            max(priority_inversions) * 1.25
        )

    ax.yaxis.grid(
        True,
        linestyle=":",
        color="black"
    )

    ax.set_axisbelow(True)

    lgd = ax.legend(
        loc="upper left",
        frameon=True,
        fontsize=24,
        borderpad=0.3,
        ncol=1,
    )

    lgd.get_frame().set_edgecolor("black")

    fig.tight_layout()

    fig.savefig(
        "inversion_vs_pipeline_lag.png",
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.02,
    )

    plt.show()


def main():

    inversion_by_lag = collect_data()

    plot_priority_inversion(
        inversion_by_lag
    )


if __name__ == "__main__":
    main()