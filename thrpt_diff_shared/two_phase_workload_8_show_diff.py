#!/usr/bin/env python3
"""
two_phase_workload.py
─────────────────────
Phase A:
  • Only ingress 0 and 1 send 1500-B packets to egress 0 each timestep.
  • Stop when bytes_to_egress[0] reaches floor(1.8 × PORT_BUFFER) aligned to 1500 B.

Phase B:
  • For uniform, only the last N/2 ingress ports are active.
  • First N/2 ingress ports idle in Phase B.
  • Active ingress i sends packets to egress = INCAST_LIST[i].
  • Packet size is sampled from PHASEB_SIZES.
  • For each egress k in INCAST_LIST, cap aggregate bytes at floor(burst% × PORT_BUFFER)
    aligned to 1500 B.

Invariant:
  • Never write a timestep where all ingresses are idle.

CSV:
  • Columns: t, i, dest_port, size  (-1 for idle)
  • file: output_new_{label}.csv
"""

from __future__ import annotations

import sys
import csv
import os
import random


# ─────────── Constants ───────────
N_PORTS       = 8
PORT_BUFFER   = 2 * 1024 * 1024      # bytes per egress
PACKET_BYTES  = 1500                 # Phase A packet size


# ─────────── Incast mappings ───────────
# 0-indexed mapping:
# ingress i → egress INCAST_LIST[i]
#
# -1 means that ingress is idle in Phase B.

INCAST_LIST_LOAD = {
    # Uniform low-priority phase:
    # ingress 0..3 idle
    # ingress 4..7 active
    #
    # Since priority is based on ingress/VOQ index:
    # ingress 4,5,6,7 are low-priority VOQs.
    "uniform": [[-1, -1, -1, -1, 2, 2, 3, 3],[-1, -1, 2, 2, 4, 4, 3, 3],[1, 1, 2, 2, 3, 3, 4, 4]],

    # Existing mappings kept unchanged
    "zipf":    [1, 1, 1, 1, 2, 2, 3, 3],
    "skewed":  [1, 1, 1, 1, 1, 2, 2, 2],
}


# ─────────── Phase-B packet sampler ───────────
# You currently had both as 1500.
# Change this to (1440, 200) if you want the old mixed-size behavior.
PHASEB_SIZES = (1500, 1500)


def sample_phaseB_pkt() -> int:
    return PHASEB_SIZES[0] if random.random() < 0.5 else PHASEB_SIZES[1]


def _bytes_quota_aligned(percent: float) -> int:
    """
    floor(percent * PORT_BUFFER) to a multiple of PACKET_BYTES.
    """
    raw = int(PORT_BUFFER * percent / 100.0)
    return (raw // PACKET_BYTES) * PACKET_BYTES


def write_csv(dest_port, size, label: str):
    path = f"output_new_{label}_incast_val{sys.argv[4]}.csv"

    # Explicitly clear any existing file
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    T, L = len(dest_port[0]), len(dest_port)

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "i", "dest_port", "size"])

        for t in range(T):
            for i in range(L):
                eg = dest_port[i][t]
                w.writerow([t, i, eg, size[i][t] if eg >= 0 else -1])

    print(f"✓  {path}")


def generate_two_phase():
    # ── CLI
    if len(sys.argv) < 5:
        print("Usage: two_phase_workload.py <burst_percent> <incast_tag> <rounds_tag> <incast_val>")
        sys.exit(1)

    burst_percent = int(sys.argv[1])
    incast_tag    = sys.argv[2]
    rounds_tag    = sys.argv[3]
    incast_val = int(sys.argv[4])

    if incast_tag not in INCAST_LIST_LOAD:
        raise ValueError(
            f"Unknown incast_tag={incast_tag}. "
            f"Choose from {list(INCAST_LIST_LOAD.keys())}"
        )

    INCAST_LIST = INCAST_LIST_LOAD[incast_tag][incast_val]

    assert len(INCAST_LIST) == N_PORTS, "INCAST_LIST length must equal N_PORTS"

    label = f"{burst_percent}_{incast_tag}_{rounds_tag}"

    # ── Storage
    dest_port = [[] for _ in range(N_PORTS)]
    size      = [[] for _ in range(N_PORTS)]

    # ─────────────────────────────────────────────
    # Phase A:
    # ingress 0 and ingress 1 send to egress 0.
    # ─────────────────────────────────────────────
    phaseA_quota = _bytes_quota_aligned(200.0)  # 200% of buffer
    egress_bytes = [0] * N_PORTS

    while egress_bytes[0] + 2 * PACKET_BYTES <= phaseA_quota:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS

        row_dest[0] = 0
        row_size[0] = PACKET_BYTES

        row_dest[1] = 0
        row_size[1] = PACKET_BYTES

        egress_bytes[0] += 2 * PACKET_BYTES

        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

    # If exactly one more 1500-B packet fits, emit one more step.
    remaining = phaseA_quota - egress_bytes[0]

    if PACKET_BYTES <= remaining < 2 * PACKET_BYTES:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS

        row_dest[0] = 0
        row_size[0] = PACKET_BYTES

        egress_bytes[0] += PACKET_BYTES

        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

    # ─────────────────────────────────────────────
    # Phase B:
    # For uniform, only last N/2 ingress ports send.
    # Ports with INCAST_LIST[i] == -1 stay idle.
    # ─────────────────────────────────────────────
    burst_quota = {}
    burst_sent  = {}

    # Ignore inactive ports marked as -1.
    egress_set = sorted(k for k in set(INCAST_LIST) if k != -1)

    for k in egress_set:
        burst_quota[k] = _bytes_quota_aligned(float(burst_percent))
        burst_sent[k]  = 0

    while True:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS
        active   = 0

        for i in range(N_PORTS):
            k = INCAST_LIST[i]

            # Inactive ingress in Phase B
            if k == -1:
                continue

            remaining = burst_quota[k] - burst_sent[k]

            if remaining < min(PHASEB_SIZES):
                continue

            pkt = sample_phaseB_pkt()

            if pkt > remaining:
                # Try the smallest packet size as fallback
                fallback = min(PHASEB_SIZES)

                if fallback <= remaining:
                    pkt = fallback
                else:
                    continue

            row_dest[i] = k
            row_size[i] = pkt
            burst_sent[k] += pkt
            active += 1

        # Prevent writing all-idle rows.
        if active == 0:
            break

        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

        # If all egresses reached quota, stop.
        if all(burst_sent[k] >= burst_quota[k] for k in egress_set):
            break

    write_csv(dest_port, size, label)


if __name__ == "__main__":
    generate_two_phase()