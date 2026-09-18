#!/usr/bin/env python3
"""
traffic_generator_avg_incast.py
────────────────────────────────
• 16 ingress / egress ports
• PORT_BUFFER   = 2 MiB  (per-port memory quota)
• BURST_PERCENT = [10, 20, 30, 40, 50]
• ROUNDS        = 10  (merged into one timeline per scenario)
• Fixed 1500-byte packets

Lane-reuse: the instant a port hits its byte quota, every lane mapped to it
switches to the next still-unsatisfied port in the original incast order.

**Early-termination rule (new):**
A round ends immediately when **more than 10 input lanes are idle** in the
same timestep (i.e. their destination port is -1).  The generator then
proceeds to the next round, even if some ports have not yet reached
their quota.

After each scenario the script prints, for every egress k,

    average_inc_k =  ( Σ  lanes_pointing_to_k  ) / (# timesteps k was hit)

i.e. the mean number of active lanes ***only*** across the timesteps
in which port k received at least one packet.
"""
from __future__ import annotations
import csv
from typing import List, Tuple, Sequence
import sys
import bisect
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt

# Usage = <burst_percent> <incast> <rounds>
# ─────────── Scenario constants ───────────
N_PORTS          = 16
PORT_BUFFER      = 2 * 1024 * 1024               # bytes (per port)
BURST_PERCENT    = [int(sys.argv[1])]            # 5 scenarios (here, single via argv)
ROUNDS           = int(sys.argv[3])              # merged
PACKET_BYTES     = 1500
IDLE_THRESHOLD   = 10                            # >10 idle lanes ends round
INCAST_VECTOR_SET = {
    'zipf':[8,6,3,8,6,3,8,6,3,8,6,3,8,6,3,2],
    'uniform':[4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
    'skewed':[2, 3, 11, 2, 3, 11, 2, 3, 11, 2, 3, 11, 2, 3, 11, 16]
}
INCAST_VECTOR = INCAST_VECTOR_SET[sys.argv[2]]


def make_sampler(values: Sequence[int], cdf: Sequence[float]):
    if len(values) != len(cdf):
        raise ValueError("values and cdf must be the same length")
    if any(cdf[i] >= cdf[i + 1] for i in range(len(cdf) - 1)) or cdf[-1] != 1.0:
        raise ValueError("cdf must be strictly increasing and end at 1.0")

    values_np = np.asarray(values)
    cdf_np    = np.asarray(cdf)

    def sample_one() -> int:
        """Draw one packet size from the empirical distribution."""
        u   = np.random.random()
        idx = bisect.bisect_left(cdf_np, u)
        return int(values_np[idx])

    return sample_one


# SIZES = [80, 160, 240, 560, 800, 1040, 1200, 1440]
# CDF   = [0.08, 0.20, 0.45, 0.55, 0.60, 0.64, 0.68, 1.00]
SIZES = [1500, 1500]
CDF = [0.5, 1]
sample_packet = make_sampler(SIZES, CDF)


# ─────────── Helper: incast → conveyor stream ───────────
def _flatten_incast(incast: List[int]) -> List[int]:
    stream: List[int] = []
    for eg, cnt in enumerate(incast):
        stream.extend([eg] * cnt)
    return stream


# ─────────── Core generator (lane-reuse, multi-round) ───────────
def generate_traffic(
    incast: List[int],
    limit_bytes: int,
    N: int,
    rounds: int,
) -> Tuple[List[List[int]], List[List[int]]]:
    """Return (dest_port matrix [lane][t], size matrix [lane][t])."""
    conveyor      = _flatten_incast(incast)
    PORTS         = len(incast)
    dest_port: List[List[int]] = [[] for _ in range(N)]
    size: List[List[int]] = [[] for _ in range(N)]

    for _ in range(rounds):
        bytes_sent   = [0] * PORTS
        active_ports = {i for i, c in enumerate(incast) if c}
        conveyor_idx = 0
        lane_map     = [-1] * N                        # current egress/lane

        def next_port() -> int:
            nonlocal conveyor_idx
            while conveyor_idx < len(conveyor):
                eg = conveyor[conveyor_idx]
                conveyor_idx += 1
                if bytes_sent[eg] < limit_bytes:
                    return eg
            return -1                                  # conveyor exhausted

        # initial assignment
        for lane in range(N):
            lane_map[lane] = next_port()

        # timestep loop
        while active_ports:
            idle_count = 0
            for lane in range(N):
                eg = lane_map[lane]

                # idle lane
                if eg == -1:
                    dest_port[lane].append(-1)
                    size[lane].append(-1)
                    idle_count += 1
                    continue

                remaining = limit_bytes - bytes_sent[eg]
                if remaining < PACKET_BYTES:           # port quota reached
                    bytes_sent[eg] = limit_bytes
                    active_ports.discard(eg)
                    lane_map[lane] = eg = next_port()
                    if eg == -1:
                        dest_port[lane].append(-1)
                        size[lane].append(-1)
                        idle_count += 1
                        continue
                    remaining = limit_bytes - bytes_sent[eg]

                dest_port[lane].append(eg)
                # With the remaining logic above, pkt will be one of SIZES.
                pkt = 1500#min(sample_packet(), max(remaining, 64))
                size[lane].append(pkt)
                bytes_sent[eg] += pkt

            # drop trailing all-idle timestep, if any
            if sum([dest_port[i][-1] for i in range(N)]) == -1 * N:
                for i in range(N):
                    dest_port[i].pop()
                    size[i].pop()

            # ── Early-termination check ──────────────────────────
            if idle_count > IDLE_THRESHOLD:
                break

    return dest_port, size


# ─────────── CSV writer ───────────
def write_csv(dest_port: List[List[int]], size: List[List[int]], label: str):
    path = f"output_new_{label}.csv"
    T, N = len(dest_port[0]), len(dest_port)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "i", "dest_port", "size"])
        for t in range(T):
            for i in range(N):
                eg = dest_port[i][t]
                w.writerow([t, i, eg, size[i][t] if eg >= 0 else -1])


# ─────────── Average-incast calculator ───────────
def report_average_incast(dest_port: List[List[int]], ports: int):
    T, L = len(dest_port[0]), len(dest_port)
    served_ts  = [0] * ports   # timesteps where port k is hit ≥1×
    lane_total = [0] * ports   # total lanes over those timesteps

    for t in range(T):
        hits = [0] * ports
        for lane in range(L):
            eg = dest_port[lane][t]
            if eg >= 0:
                hits[eg] += 1
        for k, h in enumerate(hits):
            if h:
                served_ts[k] += 1
                lane_total[k] += h

    print("Average incast (lanes while port active)")
    for k in range(ports):
        if served_ts[k]:
            avg = lane_total[k] / served_ts[k]
            print(f"  Port {k:2d}: {avg:.2f} lanes  "
                  f"(active {served_ts[k]} timesteps)")
        else:
            print(f"  Port {k:2d}: never served")


# ─────────── Packet-size histogram (new) ───────────
def plot_packet_size_histogram(size_matrix: List[List[int]], label: str):
    # Flatten sizes across all lanes/timesteps, ignore idle (-1)
    flat = [s for lane in size_matrix for s in lane if s > 0]
    if not flat:
        print("No packets generated; skipping histogram.")
        return

    counts = Counter(flat)
    xs = sorted(counts.keys())
    ys = [counts[x] for x in xs]

    plt.figure(figsize=(8, 5))
    plt.bar([str(x) for x in xs], ys)
    plt.xlabel("Packet size (bytes)")
    plt.ylabel("Count")
    plt.title(f"Packet Size Distribution — {label}")
    plt.tight_layout()
    out = f"packet_size_histogram_{label}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"✓  Saved histogram: {out}")


# ─────────── Scenario driver ───────────
if __name__ == "__main__":
    for idx, pct in enumerate(BURST_PERCENT):
        quota = (PORT_BUFFER * pct // 100 // PACKET_BYTES) * PACKET_BYTES

        dest, size = generate_traffic(
            INCAST_VECTOR,
            quota,
            N_PORTS,
            rounds=ROUNDS,
        )
        label = f'{sys.argv[1]}_{sys.argv[2]}_{sys.argv[3]}'
        write_csv(dest, size, label)
        print(f"\n✓  output_new_{label}.csv  (quota {quota} B, {ROUNDS} rounds)")
        report_average_incast(dest, len(INCAST_VECTOR))

        # NEW: plot packet size distribution
        plot_packet_size_histogram(size, label)

    print("\nAll scenarios complete.")
