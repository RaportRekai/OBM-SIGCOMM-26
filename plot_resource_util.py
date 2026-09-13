import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ==============================================================================
# Configuration
# ==============================================================================

EXCEL_FILE = "res.csv"

CLOCK_PERIOD_NS = 2.5

# Resource denominators from your existing script
LUT_DENOMINATOR = 11822.40
FF_DENOMINATOR = 23644.80

PORTS = [2, 4, 8, 16]
BANDWIDTHS = [10, 25, 50, 100]


# ==============================================================================
# Read Excel data
# ==============================================================================

def load_excel_data(filename):
    """
    Expected Excel columns:

        # Ports | Bandwidth | WNS | # LUT | # FF
    """

    df = pd.read_csv(filename)

    # Remove accidental spaces around column names
    df.columns = df.columns.str.strip()

    required_columns = [
        "# Ports",
        "Bandwidth",
        "WNS",
        "# LUT",
        "# FF",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required Excel columns: {missing}\n"
            f"Found columns: {list(df.columns)}"
        )

    # Convert columns to numeric values.
    # Any empty/non-numeric WNS becomes NaN.
    df["# Ports"] = pd.to_numeric(df["# Ports"], errors="coerce")
    df["Bandwidth"] = pd.to_numeric(df["Bandwidth"], errors="coerce")
    df["WNS"] = pd.to_numeric(df["WNS"], errors="coerce")
    df["# LUT"] = pd.to_numeric(df["# LUT"], errors="coerce")
    df["# FF"] = pd.to_numeric(df["# FF"], errors="coerce")

    # Remove completely invalid rows
    df = df.dropna(
        subset=[
            "# Ports",
            "Bandwidth",
            "# LUT",
            "# FF",
        ]
    )

    df["# Ports"] = df["# Ports"].astype(int)
    df["Bandwidth"] = df["Bandwidth"].astype(int)

    # --------------------------------------------------------------------------
    # Calculate normalized LUT / FF utilization
    # --------------------------------------------------------------------------

    df["LUT Utilization"] = df["# LUT"] / LUT_DENOMINATOR
    df["FF Utilization"] = df["# FF"] / FF_DENOMINATOR

    # --------------------------------------------------------------------------
    # Calculate maximum frequency from WNS
    #
    # Effective clock period:
    #
    #       T_max = constrained_period - WNS
    #
    # Frequency in MHz:
    #
    #       F = 1000 / T_ns
    # --------------------------------------------------------------------------

    df["Max Frequency MHz"] = (
        1000.0 /
        (CLOCK_PERIOD_NS - df["WNS"])
    )

    return df


# ==============================================================================
# Helper: obtain values for one bandwidth
# ==============================================================================

def get_bandwidth_values(df, bandwidth, column):
    """
    Return values for one bandwidth, sorted by port count.

    Example:
        bandwidth = 25
        column = "LUT Utilization"

    returns values for:
        2-port, 4-port, 8-port, ...
    depending on which configurations exist in Excel.
    """

    subset = df[df["Bandwidth"] == bandwidth].copy()

    subset = subset.sort_values("# Ports")

    return subset[column].tolist()


# ==============================================================================
# Resource utilization plot
# ==============================================================================

def plot_LUT(
    ax,
    design_10_g,
    design_25_g,
    design_50_g,
    design_100_g,
    resource="LUT",
    show_xlabel=False,
    show_legend=True
):
    no_ports = ["2", "4", "8", "16"]

    COLORS = {
        "10G":  "#FF0000",
        "25G":  "#FFD700",
        "50G":  "#00FFFF",
        "100G": "#32CD32",
    }

    bar_width = 0.25
    spanning_area = [4, 3, 2, 1]
    space_btw_ticks = 0.25

    t = [0] * len(spanning_area)

    for ind in range(len(spanning_area)):
        t[ind] = (
            ind * space_btw_ticks
            + sum(spanning_area[:ind]) * bar_width
            + (spanning_area[ind] * bar_width) / 2
        )

    t = np.array(t)

    x_10g = (
        t
        - np.array(
            [
                1.5 * bar_width,
                bar_width,
                0.5 * bar_width,
                0,
            ]
        )
    )

    x_25g = (
        t[:-1]
        - np.array(
            [
                0.5 * bar_width,
                0,
                -0.5 * bar_width,
            ]
        )
    )

    x_50g = (
        t[:-2]
        - np.array(
            [
                -0.5 * bar_width,
                -bar_width,
            ]
        )
    )

    x_100g = t[:-3] + 1.5 * bar_width

    ax.bar(
        x_10g,
        design_10_g,
        width=bar_width,
        label="10G",
        color=COLORS["10G"],
        edgecolor="black",
        linewidth=1,
    )

    ax.bar(
        x_25g,
        design_25_g,
        width=bar_width,
        label="25G",
        color=COLORS["25G"],
        edgecolor="black",
        linewidth=1,
    )

    ax.bar(
        x_50g,
        design_50_g,
        width=bar_width,
        label="50G",
        color=COLORS["50G"],
        edgecolor="black",
        linewidth=1,
    )

    ax.bar(
        x_100g,
        design_100_g,
        width=bar_width,
        label="100G",
        color=COLORS["100G"],
        edgecolor="black",
        linewidth=1,
    )

    ax.set_xticks(t)
    ax.set_xticklabels(no_ports, fontsize=22)

    all_values = (
        design_10_g
        + design_25_g
        + design_50_g
        + design_100_g
    )

    ax.set_ylim(0, max(all_values) + 0.1)

    if show_xlabel:
        ax.set_xlabel(
            "Number of Ports",
            fontsize=22,
        )

    ax.set_ylabel(
        f"{resource} (%)",
        fontsize=20,
    )

    ax.tick_params(
        axis="y",
        labelsize=17,
    )

    if show_legend:
        ax.legend(
            ncol=2,
            frameon=True,
            loc="upper left",
            prop={"size": 14},
        )


def plot_resource_combined(df):

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(6, 4.2),
        sharex=True,
    )

    # ==========================================================================
    # LUT data from Excel
    # ==========================================================================

    lut_10_g = get_bandwidth_values(
        df,
        10,
        "LUT Utilization",
    )

    lut_25_g = get_bandwidth_values(
        df,
        25,
        "LUT Utilization",
    )

    lut_50_g = get_bandwidth_values(
        df,
        50,
        "LUT Utilization",
    )

    lut_100_g = get_bandwidth_values(
        df,
        100,
        "LUT Utilization",
    )

    plot_LUT(
        axes[0],
        lut_10_g,
        lut_25_g,
        lut_50_g,
        lut_100_g,
        resource="LUT",
        show_xlabel=False,
        show_legend=True,
    )

    # ==========================================================================
    # FF data from Excel
    # ==========================================================================

    ff_10_g = get_bandwidth_values(
        df,
        10,
        "FF Utilization",
    )

    ff_25_g = get_bandwidth_values(
        df,
        25,
        "FF Utilization",
    )

    ff_50_g = get_bandwidth_values(
        df,
        50,
        "FF Utilization",
    )

    ff_100_g = get_bandwidth_values(
        df,
        100,
        "FF Utilization",
    )

    plot_LUT(
        axes[1],
        ff_10_g,
        ff_25_g,
        ff_50_g,
        ff_100_g,
        resource="Flip-Flop",
        show_xlabel=True,
        show_legend=False,
    )

    plt.tight_layout()

    plt.savefig(
        "lut_ff_utilization_combined.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.show()


# ==============================================================================
# Frequency plot
# ==============================================================================

def plot_freq(df):

    no_ports = ["2", "4", "8", "16"]

    COLORS = {
        "10G":  "#FF0000",
        "25G":  "#FFD700",
        "50G":  "#00FFFF",
        "100G": "#32CD32",
    }

    # ==========================================================================
    # Frequency data is now calculated from Excel WNS
    # ==========================================================================

    design_10_g = get_bandwidth_values(
        df,
        10,
        "Max Frequency MHz",
    )

    design_25_g = get_bandwidth_values(
        df,
        25,
        "Max Frequency MHz",
    )

    design_50_g = get_bandwidth_values(
        df,
        50,
        "Max Frequency MHz",
    )

    design_100_g = get_bandwidth_values(
        df,
        100,
        "Max Frequency MHz",
    )

    bar_width = 0.25

    spanning_area = [4, 3, 2, 1]
    space_btw_ticks = 0.25

    t = [0] * len(spanning_area)

    for ind in range(len(spanning_area)):
        t[ind] = (
            ind * space_btw_ticks
            + sum(spanning_area[:ind]) * bar_width
            + (spanning_area[ind] * bar_width) / 2
        )

    t = np.array(t)

    # ==========================================================================
    # Bar positions
    # ==========================================================================

    x_10g = (
        t
        - np.array(
            [
                1.5 * bar_width,
                bar_width,
                0.5 * bar_width,
                0,
            ]
        )
    )

    x_25g = (
        t[:-1]
        - np.array(
            [
                0.5 * bar_width,
                0,
                -0.5 * bar_width,
            ]
        )
    )

    x_50g = (
        t[:-2]
        - np.array(
            [
                -0.5 * bar_width,
                -bar_width,
            ]
        )
    )

    x_100g = (
        t[:-3]
        + 1.5 * bar_width
    )

    # ==========================================================================
    # Bars
    # ==========================================================================

    plt.figure(
        figsize=(6, 4.2)
    )

    plt.bar(
        x_10g,
        design_10_g,
        width=bar_width,
        label="10G",
        color=COLORS["10G"],
        edgecolor="black",
        linewidth=1,
    )

    plt.bar(
        x_25g,
        design_25_g,
        width=bar_width,
        label="25G",
        color=COLORS["25G"],
        edgecolor="black",
        linewidth=1,
    )

    plt.bar(
        x_50g,
        design_50_g,
        width=bar_width,
        label="50G",
        color=COLORS["50G"],
        edgecolor="black",
        linewidth=1,
    )

    plt.bar(
        x_100g,
        design_100_g,
        width=bar_width,
        label="100G",
        color=COLORS["100G"],
        edgecolor="black",
        linewidth=1,
    )

    # ==========================================================================
    # Required clock markers
    # ==========================================================================

    req_10g = 156.25
    req_high = 390.625

    marker_half_width = bar_width / 2

    # 10G target clock marker
    for x in x_10g:
        plt.hlines(
            req_10g,
            x - marker_half_width,
            x + marker_half_width,
            colors="black",
            linewidth=3,
            zorder=5,
        )

    # Port 2: 25G + 50G + 100G
    group0_x_positions = np.array(
        [
            x_25g[0],
            x_50g[0],
            x_100g[0],
        ]
    )

    plt.hlines(
        req_high,
        group0_x_positions.min() - bar_width / 2,
        group0_x_positions.max() + bar_width / 2,
        colors="black",
        linewidth=3,
        zorder=5,
    )

    # Port 4: 25G + 50G
    group1_x_positions = np.array(
        [
            x_25g[1],
            x_50g[1],
        ]
    )

    plt.hlines(
        req_high,
        group1_x_positions.min() - bar_width / 2,
        group1_x_positions.max() + bar_width / 2,
        colors="black",
        linewidth=3,
        zorder=5,
    )

    # Port 8: 25G
    group2_x_positions = np.array(
        [
            x_25g[2],
        ]
    )

    plt.hlines(
        req_high,
        group2_x_positions.min() - bar_width / 2,
        group2_x_positions.max() + bar_width / 2,
        colors="black",
        linewidth=3,
        zorder=5,
    )

    # ==========================================================================
    # Styling
    # ==========================================================================

    plt.xticks(
        t,
        no_ports,
        fontsize=21,
    )

    plt.yticks(
        fontsize=21,
    )

    all_freqs = (
        design_10_g
        + design_25_g
        + design_50_g
        + design_100_g
    )

    plt.ylim(
        0,
        max(all_freqs) + 200,
    )

    plt.xlabel(
        "Number of Ports",
        fontsize=21,
    )

    plt.ylabel(
        "Clock Speed (MHz)",
        fontsize=21,
    )

    # ==========================================================================
    # Legends
    # ==========================================================================

    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    bw_handles = [
        Patch(
            facecolor=COLORS["10G"],
            edgecolor="black",
            label="10G",
        ),
        Patch(
            facecolor=COLORS["25G"],
            edgecolor="black",
            label="25G",
        ),
        Patch(
            facecolor=COLORS["50G"],
            edgecolor="black",
            label="50G",
        ),
        Patch(
            facecolor=COLORS["100G"],
            edgecolor="black",
            label="100G",
        ),
    ]

    legend_bw = plt.legend(
        handles=bw_handles,
        ncol=2,
        frameon=True,
        loc="upper right",
        prop={"size": 14},
    )

    plt.gca().add_artist(
        legend_bw
    )

    req_handle = [
        Line2D(
            [0],
            [0],
            color="black",
            linewidth=1.5,
            label="Target clock \nspeed",
        )
    ]

    plt.legend(
        handles=req_handle,
        frameon=True,
        loc="upper left",
        prop={"size": 14},
    )

    plt.savefig(
        "max_freq_plot.png",
        dpi=300,
        bbox_inches="tight",
    )

    plt.show()


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    df = load_excel_data(
        EXCEL_FILE
    )

    print("\nLoaded implementation results:")
    print(df)

    print("\nCalculated frequencies:")
    print(
        df[
            [
                "# Ports",
                "Bandwidth",
                "WNS",
                "Max Frequency MHz",
            ]
        ].to_string(index=False)
    )

    plot_freq(df)
    plot_resource_combined(df)