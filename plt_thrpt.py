#!/usr/bin/env python3
"""
Usage:
  python plot_thrpt.py <burst> <incast> <rounds>

Example:
  python plot_thrpt.py _ uniform 1
"""

import os
import re
import sys
import glob
import numpy as np
import matplotlib.pyplot as plt

import matplotlib.hatch
from matplotlib.hatch import Shapes
from matplotlib.patches import Polygon

plt.rcParams["hatch.linewidth"] = 2.0
class DiamondHatch(Shapes):
    def __init__(self, hatch, density):
        self.filled = False
        self.size = 0.6
        self.path = Polygon(
            [[0.5, 1.0], [1.0, 0.5], [0.5, 0.0], [0.0, 0.5]],
            closed=True
        ).get_path()
        self.num_rows = hatch.count("D") * density
        self.shape_vertices = self.path.vertices
        self.shape_codes = self.path.codes
        Shapes.__init__(self, hatch, density)


matplotlib.hatch._hatch_types.append(DiamondHatch)


# ── Config ─────────────────────────────────────────────────────────

PRIVATE_FOLDERS = {
    "dt":       "switch-sim-private/master/dt_logs",
    "abm":      "switch-sim-private/master/abm_logs",
    "obm":      "switch-sim-private/master/obm_logs",
    "spreal":   "switch-sim-private/master/spreal_logs",
    "optimal":  "switch-sim-private/master/optimal_logs",
    "credence": "switch-sim-private/master/credence_logs",
    "occamy":   "switch-sim-private/master/occamy_logs",
}

SHARED_FOLDERS = {
    "dt":       "switch-sim-shared/master/dt_logs",
    "abm":      "switch-sim-shared/master/abm_logs",
    "obm":      "switch-sim-shared/master/obm_logs",
    "spreal":   "switch-sim-shared/master/spreal_logs",
    "optimal":  "switch-sim-shared/master/optimal_logs",
    "credence": "switch-sim-shared/master/credence_logs",
    "occamy":   "switch-sim-shared/master/occamy_logs",
}

LABELS_ORDER = [
    "DT",
    "DT_HDW",
    "ABM",
    "OBM",
    "Optimal_HDW",
    "SP_Ideal",
    "SP",
    "Optimal",
    "Credence",
    "Occamy",
]

CUSTOM_LABELS = {
    "DT":              "DT",
    "DT_HDW":          "DT-hw",
    "ABM":             "ABM",
    "OBM":             "OBM",
    "SP":              "SP",
    "SP_Ideal":        "SP-Ideal",
    "Optimal_HDW":     "OBM-hw",
    "Optimal":         "LQD",
    "Credence":        "Credence",
    "Occamy":          "Occamy",
    "PRIVATE_LINE":    "Private buffer",
}

COLOR = {
    "DT":              "#00FFFF",
    "DT_HDW":          "#00FFFF",
    "ABM":             "#FFD700",
    "OBM":             "#FF0000",
    "SP":              "#800080",
    "SP_Ideal":        "#DA70D6",
    "Optimal_HDW":     "#FF0000",
    "Optimal":         "#32CD32",
    "Credence":        "#555555",
    "Occamy":          "#1E90FF",
    "PRIVATE_LINE":    "#000000",
}

HATCH = {
    "DT_HDW":      "o",
    "Optimal_HDW": "o",
}

ALGO_TO_LABEL = {
    "dt":       "DT",
    "abm":      "ABM",
    "obm":      "OBM",
    "spreal":   "SP",
    "optimal":  "Optimal",
    "credence": "Credence",
    "occamy":   "Occamy",
}

LABEL_TO_ALGO = {
    "DT":       "dt",
    "ABM":      "abm",
    "OBM":      "obm",
    "SP":       "spreal",
    "Optimal":  "optimal",
    "Credence": "credence",
    "Occamy":   "occamy",
}

INCAST_ORDER = ["uniform", "zipf", "skewed"]


# ── Regex ──────────────────────────────────────────────────────────

FILE_RE = re.compile(
    r"^(?:altered_)?output_(?P<algo>dt|abm|obm|spreal|optimal|credence|occamy)"
    r"_(?P<burst>\d+|n)"
    r"_(?P<incast>[A-Za-z0-9]+)"
    r"_(?P<rounds>\d+)"
    r"(?:_(?P<alpha>[\d\.]+))?"
    r"(?:\.txt)?$",
    re.I,
)

RE_TPUT_CREDENCE = re.compile(r"([\d\.]+)\s*Gbps\s*\(Aggregate\)", re.I)
RE_TPUT_OCCAMY   = re.compile(r"([\d\.]+)\s*gbps\s*per\s*port", re.I)
RE_TPUT_STD      = re.compile(r"([\d\.]+)\s*([gt])bps", re.I)

RE_DROP1  = re.compile(r"packets?[^\n]*dropped[^\d]*=\s*(\d+)", re.I)
RE_DROP2  = re.compile(r"dropped_packets?\s*=\s*(\d+)", re.I)
RE_DROP3  = re.compile(r"dropped[^0-9]*=?\s*([0-9]+)", re.I)
RE_SERVED = re.compile(r"packets\s*(?:served|sent)\s*=\s*(\d+)", re.I)
RE_TIME   = re.compile(r"(?:Over in|time|t)\s*[=:]?\s*(\d+)", re.I)


# ── CSV Helper ─────────────────────────────────────────────────────

def parse_csv_throughput(folder_type, algo_prefix, incast):
    algo_prefix = algo_prefix.lower()
    incast = incast.lower()

    candidate_names = [
        f"{folder_type}_{algo_prefix}_{incast}_throughput.csv"
    ]

    if algo_prefix == "optimal":
        candidate_names.append(
            f"{folder_type}_lqd_{incast}_throughput.csv"
        )

    candidate_paths = []

    for name in candidate_names:
        candidate_paths.append(name)
        candidate_paths.append(
            os.path.join(
                folder_type,
                "skewed",
                "master",
                f"{algo_prefix}_logs",
                name
            )
        )

    target_file = None

    for path in candidate_paths:
        if os.path.exists(path):
            target_file = path
            break

    data = {}

    if not target_file:
        print(
            f"⚠️ Missing CSV for {folder_type}, {algo_prefix}, {incast}; "
            f"using 0.0 where needed"
        )
        return data

    print(f"Reading CSV: {target_file}")

    with open(target_file, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if "burst" in line.lower():
                continue

            parts = line.split(",")

            if len(parts) < 2:
                continue

            try:
                burst_val = int(parts[0])
                tput_gbps = float(parts[1])
                data[burst_val] = tput_gbps
            except ValueError:
                continue

    return data


# ── Log Helpers ────────────────────────────────────────────────────

def parse_metrics(path):
    tput = None
    drops = None
    served = None
    time_val = None

    try:
        with open(path, "r", errors="ignore") as fh:
            for ln in fh:
                if tput is None:
                    m_cred = RE_TPUT_CREDENCE.search(ln)
                    if m_cred:
                        tput = float(m_cred.group(1))

                    if tput is None:
                        m_occ = RE_TPUT_OCCAMY.search(ln)
                        if m_occ:
                            tput = float(m_occ.group(1))

                    if tput is None:
                        m_std = RE_TPUT_STD.search(ln)
                        if m_std:
                            val, unit = m_std.groups()
                            val = float(val)

                            if unit.lower() == "g":
                                tput = val
                            else:
                                tput = val * 1000.0

                if drops is None:
                    md = RE_DROP1.search(ln) or RE_DROP2.search(ln) or RE_DROP3.search(ln)
                    if md:
                        drops = int(md.group(1))

                if served is None:
                    ms = RE_SERVED.search(ln)
                    if ms:
                        served = int(ms.group(1))

                if time_val is None:
                    mt = RE_TIME.search(ln)
                    if mt:
                        time_val = int(mt.group(1))

    except FileNotFoundError:
        return None, None, None, None

    return tput, drops, served, time_val


def find_log_file(folder, algo, burst, incast, rounds, folder_type):
    original_base = f"output_{algo}_{burst}_{incast}_{rounds}"
    altered_base = f"altered_output_{algo}_{burst}_{incast}_{rounds}"

    suffixes = [
        ".txt",
        "",
        "_16.txt",
        "_16.0.txt",
        "_16.0",
    ]

    if folder_type == "shared_buffer":
        bases = [original_base]
    else:
        bases = [altered_base, original_base]

    for base in bases:
        for suffix in suffixes:
            p = os.path.join(folder, base + suffix)
            if os.path.isfile(p):
                return p

    for base in bases:
        pattern = os.path.join(folder, base + "*")
        matches = glob.glob(pattern)

        for m in sorted(matches):
            if os.path.isfile(m):
                return m

    return None


def get_log_tput(folder_map, algo, burst, incast, rounds, folder_type):
    path = find_log_file(
        folder_map[algo],
        algo,
        burst,
        incast,
        rounds,
        folder_type=folder_type
    )

    print(
        f"{folder_type.upper()} READ: "
        f"algo={algo}, burst={burst}, incast={incast}, path={path}"
    )

    if not path:
        return 0.0, np.nan, None, None

    tp, dr, served, time_val = parse_metrics(path)

    if tp is None:
        tp = 0.0

    return tp, dr, served, time_val


def get_occamy_tput(folder_map, burst, incast, rounds, folder_type):
    occ_path = find_log_file(
        folder_map["occamy"],
        "occamy",
        burst,
        incast,
        rounds,
        folder_type=folder_type
    )

    obm_path = find_log_file(
        folder_map["obm"],
        "obm",
        burst,
        incast,
        rounds,
        folder_type=folder_type
    )

    print(
        f"{folder_type.upper()} READ: "
        f"algo=occamy, burst={burst}, incast={incast}, path={occ_path}"
    )

    if not occ_path or not obm_path:
        return 0.0, np.nan

    _, _, _, obm_time = parse_metrics(obm_path)
    _, occ_dr, occ_served, _ = parse_metrics(occ_path)

    if occ_served is not None and obm_time is not None and obm_time > 0:
        tp = (occ_served * 1500.0 * 8.0) / obm_time
    else:
        tp = 0.0

    return tp, occ_dr


def discover_ticks(burst_arg, incast_arg, rounds_arg):
    vals = set()

    wildcard = (
        "burst" if burst_arg == "_"
        else "incast" if incast_arg == "_"
        else "rounds"
    )

    for algo, folder in SHARED_FOLDERS.items():
        if not os.path.isdir(folder):
            continue

        for fn in os.listdir(folder):
            m = FILE_RE.match(fn)

            if not m:
                continue

            gd = m.groupdict()

            if burst_arg != "_" and gd["burst"] != str(burst_arg):
                continue

            if incast_arg != "_" and gd["incast"].lower() != incast_arg.lower():
                continue

            if rounds_arg != "_" and gd["rounds"] != str(rounds_arg):
                continue

            vals.add(
                gd[wildcard].lower()
                if wildcard == "incast"
                else gd[wildcard]
            )

    if wildcard == "incast":
        known = [v for v in INCAST_ORDER if v in vals]
        unknown = sorted([v for v in vals if v not in INCAST_ORDER])
        ticks = known + unknown
    else:
        clean_vals = []

        for v in vals:
            try:
                clean_vals.append(int(v))
            except ValueError:
                pass

        ticks = sorted(clean_vals)

    return wildcard, ticks


# ── Data Collection ────────────────────────────────────────────────

def collect_series(wildcard, ticks, fixed):
    """
    Bars:
      shared_buffer values for:
      DT, DT-hw, ABM, OBM, SP, SP-Ideal, OBM-hw, LQD, Credence, Occamy

    Private line:
      separate black line segment inside each x-axis tick group.

    SP:
      read from spreal_logs:
        output_spreal_<burst>_<incast>_<rounds>

    SP-Ideal:
      shared SP-Ideal = shared OBM
      private SP-Ideal = private OBM

    Normalization:
      every value divided by shared_buffer OBM-hw.
    """

    shared_bars = {lbl: [] for lbl in LABELS_ORDER}
    drops = {lbl: [] for lbl in LABELS_ORDER}

    private_points_by_tick = []

    shared_csv = {
        "DT_HDW": {},
        "Optimal_HDW": {},
    }

    private_csv = {
        "DT_HDW": {},
        "Optimal_HDW": {},
    }

    if wildcard == "burst":
        incast = fixed["incast"]

        shared_csv["DT_HDW"] = parse_csv_throughput("shared", "dt", incast)
        shared_csv["Optimal_HDW"] = parse_csv_throughput("shared", "optimal", incast)

        private_csv["DT_HDW"] = parse_csv_throughput("private", "dt", incast)
        private_csv["Optimal_HDW"] = parse_csv_throughput("private", "optimal", incast)

        print("Shared DT-hw CSV data:")
        print(shared_csv["DT_HDW"])

        print("Shared OBM-hw CSV data:")
        print(shared_csv["Optimal_HDW"])

        print("Private DT-hw CSV data:")
        print(private_csv["DT_HDW"])

        print("Private OBM-hw CSV data:")
        print(private_csv["Optimal_HDW"])

    for tick in ticks:
        burst = fixed["burst"]
        incast = fixed["incast"]
        rounds = fixed["rounds"]

        if wildcard == "burst":
            burst = tick

        if wildcard == "incast":
            incast = tick

        if wildcard == "rounds":
            rounds = tick

        burst_int = int(burst)

        # ------------------------------------------------------------
        # Shared-buffer bars from logs
        # ------------------------------------------------------------
        for algo in ["dt", "abm", "obm", "spreal", "optimal", "credence", "occamy"]:
            lbl = ALGO_TO_LABEL[algo]

            if algo == "occamy" and int(burst) == 20:
                tp, dr = get_occamy_tput(
                    SHARED_FOLDERS,
                    burst,
                    incast,
                    rounds,
                    folder_type="shared_buffer"
                )
            else:
                tp, dr, _, _ = get_log_tput(
                    SHARED_FOLDERS,
                    algo,
                    burst,
                    incast,
                    rounds,
                    folder_type="shared_buffer"
                )

            shared_bars[lbl].append(tp)

            drop_k = (
                dr / 1000.0
                if dr is not None and not (isinstance(dr, float) and np.isnan(dr))
                else np.nan
            )
            drops[lbl].append(drop_k)

        # ------------------------------------------------------------
        # SP-Ideal shared bar
        # ------------------------------------------------------------
        # SP is read from spreal_logs.
        # SP-Ideal still takes same value as shared OBM.
        shared_bars["SP_Ideal"].append(shared_bars["OBM"][-1])
        drops["SP_Ideal"].append(drops["OBM"][-1])

        # ------------------------------------------------------------
        # Shared-buffer hardware bars from CSV
        # ------------------------------------------------------------
        shared_dt_hw = shared_csv["DT_HDW"].get(burst_int, 0.0)
        shared_obm_hw = shared_csv["Optimal_HDW"].get(burst_int, 0.0)

        # If shared OBM-hw CSV is missing, fallback to shared optimal log.
        if shared_obm_hw == 0.0:
            shared_obm_hw = shared_bars["Optimal"][-1]

        shared_bars["DT_HDW"].append(shared_dt_hw)
        shared_bars["Optimal_HDW"].append(shared_obm_hw)

        drops["DT_HDW"].append(np.nan)
        drops["Optimal_HDW"].append(np.nan)

        # ------------------------------------------------------------
        # Private line points from logs
        # ------------------------------------------------------------
        private_values = {}

        for algo in ["dt", "abm", "obm", "spreal", "optimal", "credence", "occamy"]:
            lbl = ALGO_TO_LABEL[algo]

            if algo == "occamy" and int(burst) == 20:
                tp, _ = get_occamy_tput(
                    PRIVATE_FOLDERS,
                    burst,
                    incast,
                    rounds,
                    folder_type="private_buffer"
                )
            else:
                tp, _, _, _ = get_log_tput(
                    PRIVATE_FOLDERS,
                    algo,
                    burst,
                    incast,
                    rounds,
                    folder_type="private_buffer"
                )

            private_values[lbl] = tp

        # SP is read from spreal_logs.
        # SP-Ideal still takes same value as private OBM.
        private_values["SP_Ideal"] = private_values["OBM"]

        private_dt_hw = private_csv["DT_HDW"].get(burst_int, 0.0)
        private_obm_hw = private_csv["Optimal_HDW"].get(burst_int, 0.0)

        # Fallbacks for private hardware points
        if private_dt_hw == 0.0:
            private_dt_hw = private_values["DT"]

        if private_obm_hw == 0.0:
            private_obm_hw = private_values["Optimal"]

        private_values["DT_HDW"] = private_dt_hw
        private_values["Optimal_HDW"] = private_obm_hw

        # ------------------------------------------------------------
        # Normalize everything by shared OBM-hw
        # ------------------------------------------------------------
        ref = shared_obm_hw

        if ref is None or np.isnan(ref) or ref == 0:
            print(
                f"⚠️ Invalid shared OBM-hw reference for burst={burst}; "
                f"setting all normalized values to 0.0"
            )
            ref = None

        for lbl in LABELS_ORDER:
            if ref is None:
                shared_bars[lbl][-1] = 0.0
                private_values[lbl] = 0.0
            else:
                shared_bars[lbl][-1] = shared_bars[lbl][-1] / ref
                private_values[lbl] = private_values[lbl] / ref

        private_points_by_tick.append(private_values)

    return shared_bars, drops, private_points_by_tick


# ── Plotting ───────────────────────────────────────────────────────

EXPORT_DPI = 110
EXPORT_PAD = 0.02


def save_png(fig, path):
    try:
        fig.savefig(
            path,
            dpi=EXPORT_DPI,
            bbox_inches="tight",
            pad_inches=EXPORT_PAD,
            format="png",
            pil_kwargs={"compress_level": 9, "optimize": True},
        )
    except TypeError:
        fig.savefig(
            path,
            dpi=EXPORT_DPI,
            bbox_inches="tight",
            pad_inches=EXPORT_PAD,
            format="png",
        )


def grouped_bars(ax, x_ticks, data_by_label, ylabel, wildcard):
    n_ticks = len(x_ticks)
    n_bars = len(LABELS_ORDER)

    total_width = 0.85
    bar_width = total_width / n_bars
    indices = np.arange(n_ticks)

    bar_x_positions = {
        lbl: []
        for lbl in LABELS_ORDER
    }

    for i, lbl in enumerate(LABELS_ORDER):
        offset = (i - (n_bars - 1) / 2) * bar_width
        x_pos = indices + offset
        y_vals = np.array(data_by_label[lbl][:n_ticks], dtype=float)

        bar_x_positions[lbl] = x_pos

        bar_alpha = 1.0
        if lbl in ["DT_HDW", "Optimal_HDW"]:
            bar_alpha = 0.5

        hatch_pattern = HATCH.get(lbl, None)
        display_label = CUSTOM_LABELS.get(lbl, lbl)

        ax.bar(
            x_pos,
            y_vals,
            width=bar_width,
            label=display_label,
            color=COLOR[lbl],
            edgecolor="black",
            linewidth=1,
            hatch=hatch_pattern,
            alpha=bar_alpha,
        )

    ax.set_ylim(top=1.5)
    ax.set_ylabel(ylabel, fontsize=46, fontweight="normal", labelpad=14)
    ax.tick_params(axis="y", labelsize=35)
    ax.set_xticks(indices)
    ax.tick_params(axis="x", labelsize=40)

    if wildcard == "burst":
        ax.set_xlabel(
            "Burst size (% of buffer space)",
            fontsize=46,
            fontweight="normal",
        )
        ax.set_xticklabels([str(t) for t in x_ticks])

    elif wildcard == "incast":
        ax.set_xlabel("Incast distribution", fontsize=14, fontweight="bold")
        ax.set_xticklabels([str(t) for t in x_ticks], rotation=0)

    else:
        ax.set_xlabel("No. of rounds", fontsize=14, fontweight="bold")
        ax.set_xticklabels([str(t) for t in x_ticks])

    ax.yaxis.grid(True, linestyle=":", color="black")
    ax.set_axisbelow(True)

    return bar_x_positions


def build_private_line_points_by_tick(bar_x_positions, private_points_by_tick):
    """
    Build separate private-buffer line segments.

    This prevents the private line from connecting across the blank space
    between x-axis tick groups.
    """

    segments = []

    n_ticks = len(private_points_by_tick)

    for tick_idx in range(n_ticks):
        x_line = []
        y_line = []

        for lbl in LABELS_ORDER:
            x_line.append(bar_x_positions[lbl][tick_idx])
            y_line.append(private_points_by_tick[tick_idx][lbl])

        segments.append((np.array(x_line), np.array(y_line)))

    return segments


def plot_all(wildcard, ticks, shared_bars, drops, private_points_by_tick,incast_arg):
    fig1, ax1 = plt.subplots(figsize=(16, 10))

    bar_x_positions = grouped_bars(
        ax1,
        ticks,
        shared_bars,
        "Normalized Throughput",
        wildcard
    )

    private_segments = build_private_line_points_by_tick(
        bar_x_positions,
        private_points_by_tick
    )

    for seg_idx, (x_line, y_line) in enumerate(private_segments):
        ax1.plot(
            x_line,
            y_line,
            marker="o",
            linewidth=3,
            markersize=8,
            color=COLOR["PRIVATE_LINE"],
            label=CUSTOM_LABELS["PRIVATE_LINE"] if seg_idx == 0 else None,
            zorder=20,
        )

    lgd = ax1.legend(
        loc="upper left",
        frameon=True,
        fontsize=28,
        borderpad=0.3,
        ncol=3,
    )
    lgd.get_frame().set_edgecolor("black")

    fig1.tight_layout()
    save_png(fig1, f"throughput_combined_{incast_arg}.png")
    print(f"Generated throughput_combined_{incast_arg}.png")

    fig2, ax2 = plt.subplots(figsize=(16, 8))

    grouped_bars(
        ax2,
        ticks,
        drops,
        r"Packets Dropped (x$10^3$)",
        wildcard
    )

    lgd = ax2.legend(
        loc="upper left",
        frameon=True,
        fontsize=50,
        borderpad=0.3,
        ncol=4,
    )
    lgd.get_frame().set_edgecolor("black")

    fig2.tight_layout()
    save_png(fig2, "drops_combined.png")
    print("Generated drops_combined.png")


# ── Main ───────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 4:
        print("Usage: python plot_thrpt.py <burst> <incast> <rounds>")
        sys.exit(1)

    burst_arg, incast_arg, rounds_arg = sys.argv[1:4]

    underscore_count = sum(
        v == "_"
        for v in (burst_arg, incast_arg, rounds_arg)
    )

    if underscore_count != 1:
        print("Error: exactly one argument must be '_' to select the X-axis.")
        sys.exit(1)

    burst_fix = burst_arg if burst_arg == "_" else str(int(burst_arg))
    incast_fix = incast_arg if incast_arg == "_" else incast_arg.lower()
    rounds_fix = rounds_arg if rounds_arg == "_" else str(int(rounds_arg))

    wildcard, ticks = discover_ticks(burst_fix, incast_fix, rounds_fix)

    if wildcard == "burst":
        ticks = [t for t in ticks if t in [20, 30, 40, 50]]

    if not ticks:
        print(f"No matching logs found for {wildcard} variation.")
        sys.exit(0)

    fixed = {
        "burst":  burst_fix if burst_fix != "_" else None,
        "incast": incast_fix if incast_fix != "_" else None,
        "rounds": rounds_fix if rounds_fix != "_" else None,
    }

    print(f"Collecting data for {wildcard} in {ticks}...")

    shared_bars, drops, private_points_by_tick = collect_series(
        wildcard,
        ticks,
        fixed
    )

    print("\nPrivate line points by tick:")
    for tick, vals in zip(ticks, private_points_by_tick):
        print(f"{wildcard.capitalize()} {tick}:")
        for lbl in LABELS_ORDER:
            print(f"  {lbl}: {vals[lbl]}")

    plot_all(
        wildcard,
        ticks,
        shared_bars,
        drops,
        private_points_by_tick,
        incast_arg
    )


if __name__ == "__main__":
    main()