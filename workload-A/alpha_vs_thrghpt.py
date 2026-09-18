#!/usr/bin/env python3
# DT • single-curve plots: wrkld a (base) and wrkld b (_wkld_b), selectable incast
import os, re, sys
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from math import isclose, ceil

DT_DIR  = "/home/dan/LQD/LQD/master/dt_logs"
OUT_DIR = "/home/dan/LQD/LQD/master/plots_thrgpt_vs_alpha"
os.makedirs(OUT_DIR, exist_ok=True)

RE_BASE = re.compile(r"^output_dt_(\d+)_([A-Za-z]+)_(\d+)_([0-9.]+)\.txt$", re.I)
RE_WKLD = re.compile(r"^output_dt_(\d+)_([A-Za-z]+)_(\d+)_([0-9.]+)_wkld_(\w+)\.txt$", re.I)
RE_GBPS = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*gbps\b", re.I)
EXCLUDE_ALPHA = {0.2}

LABEL_FSIZE = 34
TICK_FSIZE  = 30
LEG_FSIZE   = 26
LINE_W      = 3.6
MARKER_SZ   = 7.5

def _ceil_from(start, value, step):
    if value <= start:
        return start
    return start + ceil((value - start) / step) * step

def extract_throughput_gbps(path):
    try:
        with open(path, "r", errors="ignore") as f:
            txt = f.read()
    except FileNotFoundError:
        return None
    m = list(RE_GBPS.finditer(txt))
    return float(m[-1].group(1)) if m else None

def collect_series(which, incast_filter):  # which: 'a' or 'b'; incast_filter: 'uniform'|'zipf'|'skewed'|'any'
    pts = []
    if not os.path.isdir(DT_DIR): return pts
    for fn in os.listdir(DT_DIR):
        p = os.path.join(DT_DIR, fn)
        if which == "a":
            mb = RE_BASE.match(fn)
            if not mb: continue
            _, incast, _, alpha_str = mb.groups()
        else:
            mw = RE_WKLD.match(fn)
            if not mw: continue
            _, incast, _, alpha_str, tag = mw.groups()
            if tag.lower() != "b": continue

        inc = incast.lower()
        if incast_filter != "any" and inc != incast_filter:
            continue

        try:
            alpha = float(alpha_str)
        except ValueError:
            continue
        if any(isclose(alpha, x, abs_tol=1e-12) for x in EXCLUDE_ALPHA):
            continue

        thr = extract_throughput_gbps(p)
        if thr is not None:
            pts.append((alpha, thr))
    pts.sort(key=lambda x: x[0])
    return pts

def plot_one_curve(which, series, incast_filter):
    if not series:
        print(f"No DT data for wrkld {which} ({incast_filter}). Skipping."); return
    alphas = [a for a,_ in series]
    tbps   = [t/1000.0 for _,t in series]
    color  = "#1f77b4" if which=="a" else "#1f77b4"
    legend_label = "Workload A" if which == "a" else "Workload A"
    legend_loc   = "lower right" if which == "a" else "lower right"

    fig, ax = plt.subplots(figsize=(8, 6.3))
    ax.plot(alphas, tbps, marker="o", linewidth=LINE_W, markersize=MARKER_SZ,
            color=color, linestyle="-", label=legend_label)

    ax.set_xlabel("Alpha", fontsize=LABEL_FSIZE)
    ax.set_ylabel("Throughput (Tbps)", fontsize=LABEL_FSIZE, labelpad=18)
    ax.tick_params(axis="both", labelsize=TICK_FSIZE)
    ax.yaxis.grid(True, linestyle=":", color="black"); ax.set_axisbelow(True)

    # X axis (unchanged)
    step = 2
    xmax_even = int(step * ceil(max(alphas)/step))
    ax.set_xlim(0, xmax_even + 0.5)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(step))
    ax.xaxis.set_minor_locator(mticker.MultipleLocator(1))
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

    # Ensure an extra tick/line at y = 4.0
    ylo, yhi = ax.get_ylim()
    if yhi < 4.0:
        ax.set_ylim(ylo, 4.0)                 # make sure 4.0 is visible
    ticks = list(ax.get_yticks())
    if not any(abs(t - 4.0) < 1e-9 for t in ticks):
        ticks.append(4.0)
        ticks = sorted(set(round(t, 6) for t in ticks))
        ax.set_yticks(ticks)
    ax.axhline(4.0, linestyle=":", color="black", linewidth=0.8)  # guide line at 4.0

    leg = ax.legend(loc=legend_loc, frameon=True, fontsize=LEG_FSIZE)
    leg.get_frame().set_edgecolor("black")

    fig.tight_layout()
    inc_tag = incast_filter
    out = os.path.join(OUT_DIR, f"thrgpt_vs_alpha_{inc_tag}_dt_wrkld_{which}.png")
    fig.savefig(out, dpi=300, bbox_inches="tight"); plt.close(fig)
    print(f"Saved {out}")

def main():
    # Optional CLI: incast filter. Default "uniform". Accept "zipf", "skewed", "any".
    incast_filter = sys.argv[1].lower() if len(sys.argv) > 1 else "uniform"
    if incast_filter not in {"uniform","zipf","skewed","any"}:
        print("Unknown incast; use one of: uniform | zipf | skewed | any")
        sys.exit(1)

    series_a = collect_series("a", incast_filter)
    series_b = collect_series("b", incast_filter)
    plot_one_curve("a", series_a, incast_filter)
    plot_one_curve("b", series_b, incast_filter)

if __name__ == "__main__":
    main()
