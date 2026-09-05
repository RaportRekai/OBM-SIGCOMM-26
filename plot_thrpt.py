#!/usr/bin/env python3
"""
plot_fct.py
───────────
Parse stats files from two folders:

  private_buffer/
  shared_buffer/

and draw combined grouped charts.

Normalization:
  Everything is normalized to shared_buffer OBM.

Plot style:
  shared_buffer  → grouped bars
  private_buffer → black line segments inside each x-tick group

Important:
  The private_buffer line does NOT connect across different x-axis ticks.
  It only connects algorithm points within the same x-tick group.

Metrics:
  • Normalized 99-percentile FCT      short / medium / long
  • Normalized 99.9-percentile FCT    short / medium / long
  • Normalized Average Throughput     long flows only

Added:
  • stats_spreal.txt plotted beside SP Ideal
  • stats_spreal.txt renamed to SP
  • stats_sp.txt renamed to SP Ideal
  • Single combined legend box
  • Black line legend entry represents Private buffer
"""

import os
import re
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from collections import defaultdict
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


# ── Display mapping ──────────────────────────────────────────────
ALGO_META = {
    "dt":        ("DT",       "#00FFFF"),
    "abm":       ("ABM",      "#FFD700"),
    "obm":       ("OBM",      "#FF0000"),

    "spreal":    ("SP",       "#800080"),
    "lqd_ideal": ("SP-Ideal", "#DA70D6"),

    "lqd":       ("LQD",      "#32CD32"),
    "credence":  ("Credence", "#555555"),
    "occamy":    ("Occamy",   "#1E90FF"),
}

ORDERED_LABELS = [
    "DT",
    "ABM",
    "OBM",
    "SP-Ideal",
    "SP",
    "LQD",
    "Credence",
    "Occamy",
]

BASELINE_LABEL = "OBM"

DATASET_XLABEL = {
    "incast": "Incast Degree",
    "websearch": "Network Load",
}


# ——— Fonts for paper plots ———
YLABEL_FONTSIZE = 46
XLABEL_FONTSIZE = 48
YTICK_FONTSIZE  = 53
XTICK_FONTSIZE  = 53
LEGEND_FONTSIZE = 38
TICK_LENGTH     = 12
TICK_WIDTH      = 2.4

MAX_YTICKS = 9


WORKLOAD_RE = re.compile(
    r"workloads/(?P<kind>incast|websearch)-trace-100G-(?P<axis>degree|load)-(?P<val>[0-9.]+)\.csv\.processed",
    re.I,
)


def make_agg():
    return defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        "short": {},
        "medium": {},
        "long": {},
    })))


def parse_file(path, algo_key, agg):
    """
    Fill:

    agg[dataset][x][algo]['short'/'medium'/'long'][metric] = value
    """
    algo_label, _ = ALGO_META[algo_key]

    dataset = None
    xval = None

    with open(path, "r", errors="ignore") as fh:
        for ln in fh:
            m = WORKLOAD_RE.search(ln)

            if m:
                dataset = m.group("kind").lower()
                xval = float(m.group("val"))
                continue

            if not dataset:
                continue

            def extract(pattern, flow_key, metric_key):
                sm = re.search(pattern, ln, re.I)
                if sm:
                    agg[dataset][xval][algo_label][flow_key][metric_key] = float(sm.group(1))

            extract(r"Average FCT short flows:\s*([\d.]+)\s*us", "short", "avg")
            extract(r"p99 FCT short flows:\s*([\d.]+)\s*us", "short", "p99")
            extract(r"p99\.9 FCT short flows:\s*([\d.]+)\s*us", "short", "p999")

            extract(r"Average FCT medium flows:\s*([\d.]+)\s*us", "medium", "avg")
            extract(r"p99 FCT medium flows:\s*([\d.]+)\s*us", "medium", "p99")
            extract(r"p99\.9 FCT medium flows:\s*([\d.]+)\s*us", "medium", "p999")

            extract(r"Average FCT long flows:\s*([\d.]+)\s*us", "long", "avg")
            extract(r"p99 FCT long flows:\s*([\d.]+)\s*us", "long", "p99")
            extract(r"p99\.9 FCT long flows:\s*([\d.]+)\s*us", "long", "p999")

            tm = re.search(
                r"Average\s+recv\s+throughput\s*\(long\):\s*([\d.]+)\s*Gbps",
                ln,
                re.I,
            )

            if tm:
                agg[dataset][xval][algo_label]["long"]["tput_avg_gbps"] = float(tm.group(1))


def compact_even_ticks(ax, max_ticks: int, bottom: float = 0.0):
    ax.set_ylim(bottom=bottom)

    locator = MaxNLocator(
        nbins=max_ticks,
        steps=[1, 2, 2.5, 5, 10],
    )

    ax.yaxis.set_major_locator(locator)

    ticks = [t for t in ax.get_yticks() if t >= bottom]

    if len(ticks) < 2:
        ax.tick_params(
            axis="y",
            labelsize=YTICK_FONTSIZE,
            length=TICK_LENGTH,
            width=TICK_WIDTH,
        )
        return

    delta = ticks[1] - ticks[0]

    ax.set_ylim(
        top=ticks[-1] + 1.8*delta,
        bottom=bottom,
    )

    ax.yaxis.set_major_locator(locator)

    ticks2 = [t for t in ax.get_yticks() if t >= bottom]

    if len(ticks2) >= 2:
        ax.set_yticks(ticks2[:-1])

    ax.tick_params(
        axis="y",
        labelsize=YTICK_FONTSIZE,
        length=TICK_LENGTH,
        width=TICK_WIDTH,
    )


def _any_finite(series):
    for lbl in ORDERED_LABELS:
        arr = np.asarray(series.get(lbl, []), dtype=float)
        if np.isfinite(arr).any():
            return True
    return False


def _normalize_series(series, ref_vals):
    """
    Normalize every algorithm series by ref_vals.

    Current mode:
    ref_vals comes from shared_buffer OBM.
    """
    out = {}
    ref = np.asarray(ref_vals, dtype=float)

    for lbl, ys in series.items():
        arr = np.asarray(ys, dtype=float)

        with np.errstate(divide="ignore", invalid="ignore"):
            out_arr = np.where(
                np.isfinite(ref) & (ref != 0),
                arr / ref,
                np.nan,
            )

        out[lbl] = out_arr.tolist()

    return out


def _legend_loc_for(dataset: str, flow: str, metric: str) -> str:
    if metric == "p99" and flow == "short" and dataset in ("websearch", "incast"):
        return "upper right"

    return "upper left"


def grouped_bars_with_separate_private_lines(
    ax,
    x_ticks,
    shared_data_by_label,
    private_data_by_label,
    colors,
    ylabel,
    dataset,
):
    """
    Draw:

    shared_buffer  → grouped bars
    private_buffer → black line segment inside each x-tick group only

    This avoids connecting the final algorithm point of one x-tick group
    to the first algorithm point of the next x-tick group.
    """
    n = len(ORDERED_LABELS)

    group_gap = 0.10
    group_width = 1.0 - group_gap

    shrink = 0.90
    bar_w = (group_width / n) * shrink
    block_w = n * bar_w

    x_centers = np.arange(len(x_ticks), dtype=float)

    group_left = x_centers - group_width / 2.0
    block_left = group_left + (group_width - block_w) / 2.0

    # ── shared_buffer bars ─────────────────────────────
    for j, lbl in enumerate(ORDERED_LABELS):
        y = np.asarray(
            shared_data_by_label.get(lbl, []),
            dtype=float,
        )

        lefts = block_left + j * bar_w

        if len(y) > 0 and np.isfinite(y).any():
            ax.bar(
                lefts,
                y,
                align="edge",
                width=bar_w,
                color=colors[lbl],
                edgecolor="black",
                linewidth=1.8,
                alpha=0.85,
            )

    # ── private_buffer line: separated per x-tick group ────────────
    for i, _xv in enumerate(x_ticks):
        line_x = []
        line_y = []

        for j, lbl in enumerate(ORDERED_LABELS):
            y_arr = np.asarray(
                private_data_by_label.get(lbl, []),
                dtype=float,
            )

            if i >= len(y_arr):
                continue

            y_val = y_arr[i]

            if not np.isfinite(y_val):
                continue

            # Same x-position as the center of the matching algorithm bar
            x_pos = block_left[i] + j * bar_w + bar_w / 2.0

            line_x.append(x_pos)
            line_y.append(y_val)

        if len(line_x) > 0:
            ax.plot(
                line_x,
                line_y,
                marker="o",
                linewidth=4.0,
                markersize=12,
                color="black",
                markerfacecolor="white",
                markeredgecolor="black",
                markeredgewidth=1.8,
            )

    ax.set_ylabel(
        ylabel,
        fontsize=YLABEL_FONTSIZE,
        labelpad=16,
    )

    ax.set_xlabel(
        DATASET_XLABEL[dataset],
        fontsize=XLABEL_FONTSIZE,
        labelpad=10,
    )

    ax.set_xticks(x_centers)
    ax.set_xticklabels(
        [str(t) for t in x_ticks],
        fontsize=XTICK_FONTSIZE,
    )

    ax.tick_params(
        axis="x",
        labelsize=XTICK_FONTSIZE,
        length=TICK_LENGTH,
        width=TICK_WIDTH,
    )

    ax.yaxis.grid(
        True,
        linestyle=":",
        color="#999999",
        linewidth=1.2,
    )

    ax.set_axisbelow(True)


def combined_legend(ax, colors, loc="upper left"):
    """
    Single combined legend box:
      - algorithm colors correspond to shared_buffer bars
      - black line corresponds to private_buffer
    """

    algo_handles = [
        Patch(
            facecolor=colors[lbl],
            edgecolor="black",
            label=lbl,
        )
        for lbl in ORDERED_LABELS
    ]

    private_line_handle = Line2D(
        [0],
        [0],
        color="black",
        marker="o",
        markerfacecolor="white",
        markeredgecolor="black",
        linewidth=4.0,
        markersize=12,
        label="Private buffer",
    )

    handles = algo_handles + [private_line_handle]

    lgd = ax.legend(
        handles=handles,
        loc=loc,
        frameon=True,
        fontsize=LEGEND_FONTSIZE,
        ncol=3,
        columnspacing=1.2,
        handlelength=1.8,
        borderpad=0.5,
        labelspacing=0.5,
    )

    lgd.get_frame().set_edgecolor("black")
    lgd.get_frame().set_linewidth(1.4)


def build_series(agg, dataset, xvals, flow, metric):
    """
    Build:

    series[label] = [values across xvals]
    """
    series = {
        lbl: []
        for lbl in ORDERED_LABELS
    }

    for lbl in ORDERED_LABELS:
        for xv in xvals:
            v = (
                agg[dataset][xv]
                .get(lbl, {})
                .get(flow, {})
                .get(metric, np.nan)
            )

            series[lbl].append(v)

    return series


def plot_all_combined(agg_private, agg_shared, outdir, dpi: int):
    colors = {
        label: color
        for _key, (label, color) in ALGO_META.items()
    }

    all_datasets = sorted(
        set(agg_private.keys()) | set(agg_shared.keys())
    )

    for dataset in all_datasets:
        if dataset not in ("incast", "websearch"):
            continue

        xvals = sorted(
            set(agg_private.get(dataset, {}).keys()) |
            set(agg_shared.get(dataset, {}).keys())
        )

        if not xvals:
            continue

        # ==========================================================
        # LONG-FLOW AVERAGE THROUGHPUT ONLY
        # ==========================================================
        private_tput = build_series(
            agg_private,
            dataset,
            xvals,
            "long",
            "tput_avg_gbps",
        )

        shared_tput = build_series(
            agg_shared,
            dataset,
            xvals,
            "long",
            "tput_avg_gbps",
        )

        if not _any_finite(private_tput) and not _any_finite(shared_tput):
            continue

        # Normalize both to shared-buffer OBM throughput
        ref_vals = shared_tput.get(BASELINE_LABEL, [])

        private_tput_norm = _normalize_series(
            private_tput,
            ref_vals,
        )

        shared_tput_norm = _normalize_series(
            shared_tput,
            ref_vals,
        )

        fig, ax = plt.subplots(
            figsize=(16.5, 12.5),
        )

        grouped_bars_with_separate_private_lines(
            ax,
            xvals,
            shared_tput_norm,
            private_tput_norm,
            colors,
            "Normalized Average Throughput",
            dataset,
        )

        combined_legend(
            ax,
            colors,
        )

        compact_even_ticks(
            ax,
            MAX_YTICKS,
            bottom=0,
        )

        fig.tight_layout()

        fn = (
            f"throughput_avg_long_{dataset}"
            f"_shared_bars_private_separate_lines"
            f"_norm_shared_{BASELINE_LABEL}.png"
        )

        fig.savefig(
            os.path.join(outdir, fn),
            dpi=dpi,
            bbox_inches="tight",
        )

        plt.close(fig)

def infer_algo_key_from_filename(path):
    base = os.path.basename(path).lower()

    if "stats_" not in base:
        return None

    if "stats_credence" in base:
        return "credence"
    if "stats_occamy" in base:
        return "occamy"
    if "stats_abm" in base:
        return "abm"
    if "stats_obm" in base:
        return "obm"

    if "stats_spreal" in base:
        return "spreal"

    # IMPORTANT: check lqd_ideal before lqd
    if "stats_lqd_ideal" in base:
        return "lqd_ideal"

    if "stats_lqd" in base:
        return "lqd"

    if "stats_dt" in base:
        return "dt"

    return None


def parse_folder(folder, files, agg):
    """
    Parse files from a folder.

    If files is None, use default stats_<algo>.txt names.
    """
    parsed_any = False

    if files is None:
        files = [
            f"stats_{algo_key}.txt"
            for algo_key in ALGO_META.keys()
        ]

    for fname in files:
        path = os.path.join(folder, fname)

        algo_key = infer_algo_key_from_filename(path)

        if not algo_key:
            continue

        if not os.path.isfile(path):
            print(f"Warning: missing file: {path}")
            continue

        print(f"Parsing {path} as {ALGO_META[algo_key][0]}")

        parse_file(path, algo_key, agg)
        parsed_any = True

    return parsed_any


def print_parsed_values(name, agg):
    print(f"\n========== {name} PARSED VALUES ==========")

    for dataset in sorted(agg.keys()):
        for xval in sorted(agg[dataset].keys()):
            print(f"\n{dataset}  x={xval}")

            for lbl in ORDERED_LABELS:
                short_p99 = (
                    agg[dataset][xval]
                    .get(lbl, {})
                    .get("short", {})
                    .get("p99", None)
                )

                print(f"  {lbl:10s} short p99 = {short_p99}")

def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--private-dir",
        default="obm-sim-swift-incast-priority-private",
        help="Folder containing private-buffer stats files.",
    )

    ap.add_argument(
        "--shared-dir",
        default="obm-sim-swift-incast-priority-shared",
        help="Folder containing shared-buffer stats files.",
    )

    ap.add_argument(
        "--files",
        nargs="*",
        default=None,
        help=(
            "Optional list of stats filenames to read from both folders. "
            "Default: stats_dt.txt stats_abm.txt stats_obm.txt "
            "stats_spreal.txt stats_sp.txt stats_lqd.txt "
            "stats_credence.txt stats_occamy.txt"
        ),
    )

    ap.add_argument(
        "--outdir",
        default=".",
        help="Where to write PNGs.",
    )

    ap.add_argument(
        "--dpi",
        type=int,
        default=180,
        help="PNG DPI.",
    )

    args = ap.parse_args()

    agg_private = make_agg()
    agg_shared = make_agg()

    parsed_private = parse_folder(
        args.private_dir,
        args.files,
        agg_private,
    )

    parsed_shared = parse_folder(
        args.shared_dir,
        args.files,
        agg_shared,
    )

    parsed_private = parse_folder(
    args.private_dir,
    args.files,
    agg_private,
)

    parsed_shared = parse_folder(
        args.shared_dir,
        args.files,
        agg_shared,
    )

    print_parsed_values("PRIVATE", agg_private)
    print_parsed_values("SHARED", agg_shared)

    if not parsed_private:
        print(f"No private_buffer data parsed from: {args.private_dir}")

    if not parsed_shared:
        print(f"No shared_buffer data parsed from: {args.shared_dir}")

    if not parsed_private and not parsed_shared:
        print("No data parsed. Check folder paths and stats filenames.")
        return

    if not parsed_shared:
        print(
            "Error: this version requires shared_buffer data because "
            "shared_buffer OBM is the normalization baseline."
        )
        return

    os.makedirs(args.outdir, exist_ok=True)

    plot_all_combined(
        agg_private,
        agg_shared,
        args.outdir,
        dpi=args.dpi,
    )

    print(
        f"Done. PNGs written to: {args.outdir} "
        f"(DPI={args.dpi})"
    )


if __name__ == "__main__":
    main()