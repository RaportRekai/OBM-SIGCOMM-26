#!/usr/bin/env python3
"""
two_phase_workload.py
─────────────────────
Phase A:
  • Only ingress 0 and ingress 7 send 1500-B packets to egress 0 each timestep.
  • Stop when bytes_to_egress[0] reaches floor(1.8 × PORT_BUFFER) aligned to 1500 B.

Phase B:
  • Ingress 7 keeps sending to egress 0.
  • All other ingresses follow INCAST_LIST based on uniform / zipf / skewed.
  • Per-egress quota is still burst% × PORT_BUFFER aligned to 1500 B.
Invariant:
  • Never write a timestep where all ingresses are idle.
CSV:
  • Columns: t, i, dest_port, size  (-1 for idle), file: output_new_{label}.csv
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

# Special ports
PHASEA_INGRESS_A = 0
PHASEA_INGRESS_B = 7

PINNED_PHASEB_INGRESS = 7
PINNED_PHASEB_EGRESS  = 0

# NOTE:
# These mappings are effectively using egress IDs 1..4, while Phase A uses egress 0.
# Keeping this as-is to match your current workload behavior.
INCAST_LIST_LOAD = {

    "uniform": [1, 2, 3, 4, 4, 3, 2, 1],

    "zipf":    [1, 1, 2, 3, 3, 2, 1, 1],

    "skewed":  [1, 1, 1, 2, 2, 1, 1, 1],

}

if len(sys.argv) < 4:
    print("Usage: two_phase_workload.py <burst_percent> <incast_tag> <rounds_tag>")
    sys.exit(1)

if sys.argv[2] not in INCAST_LIST_LOAD:
    print(f"Unknown incast_tag={sys.argv[2]}")
    print(f"Valid options: {list(INCAST_LIST_LOAD.keys())}")
    sys.exit(1)

INCAST_LIST = INCAST_LIST_LOAD[sys.argv[2]]
assert len(INCAST_LIST) == N_PORTS, "INCAST_LIST length must equal N_PORTS"

# ─────────── Phase-B packet sampler ───────────
# Your comment said {1440, 200}, but your current code uses {1500, 1500}.
# I am leaving that unchanged.
PHASEB_SIZES = (1500, 1500)

def sample_phaseB_pkt() -> int:
    return PHASEB_SIZES[0] if random.random() < 0.5 else PHASEB_SIZES[1]

def _bytes_quota_aligned(percent: float) -> int:
    """floor(percent * PORT_BUFFER) to a multiple of PACKET_BYTES."""
    raw = int(PORT_BUFFER * percent / 100.0)
    return (raw // PACKET_BYTES) * PACKET_BYTES

def write_csv(dest_port, size, label: str):
    path = f"output_new_{label}.csv"

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
    burst_percent = int(sys.argv[1])
    incast_tag    = sys.argv[2]
    rounds_tag    = sys.argv[3]
    label = f"{burst_percent}_{incast_tag}_{rounds_tag}"

    dest_port = [[] for _ in range(N_PORTS)]
    size      = [[] for _ in range(N_PORTS)]

    # ─────────────────────────────────────────
    # Phase A:
    # ingress 0 and ingress 7 → egress 0
    # ─────────────────────────────────────────
    phaseA_quota = _bytes_quota_aligned(180.0)
    egress_bytes = [0] * N_PORTS

    while egress_bytes[0] + 2 * PACKET_BYTES <= phaseA_quota:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS

        row_dest[PHASEA_INGRESS_A] = 0
        row_size[PHASEA_INGRESS_A] = PACKET_BYTES

        row_dest[PHASEA_INGRESS_B] = 0
        row_size[PHASEA_INGRESS_B] = PACKET_BYTES

        egress_bytes[0] += 2 * PACKET_BYTES

        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

    # If only one more packet fits, emit one final partial Phase-A timestep.
    remaining = phaseA_quota - egress_bytes[0]
    if remaining >= PACKET_BYTES and remaining < 2 * PACKET_BYTES:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS

        row_dest[PHASEA_INGRESS_A] = 0
        row_size[PHASEA_INGRESS_A] = PACKET_BYTES

        egress_bytes[0] += PACKET_BYTES

        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

    # ─────────────────────────────────────────
    # Phase B:
    # ingress 7 is pinned to egress 0.
    # all other ingresses follow INCAST_LIST.
    # ─────────────────────────────────────────
    phaseB_egress_for_ingress = []

    for i in range(N_PORTS):
        if i == PINNED_PHASEB_INGRESS:
            phaseB_egress_for_ingress.append(PINNED_PHASEB_EGRESS)
        else:
            phaseB_egress_for_ingress.append(INCAST_LIST[i])

    burst_quota = {}
    burst_sent  = {}

    egress_set = sorted(set(phaseB_egress_for_ingress))

    for k in egress_set:
        burst_quota[k] = _bytes_quota_aligned(float(burst_percent))
        burst_sent[k]  = 0

    while True:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS
        active   = 0

        for i in range(N_PORTS):
            k = phaseB_egress_for_ingress[i]

            remaining = burst_quota[k] - burst_sent[k]

            if remaining < min(PHASEB_SIZES):
                continue

            pkt = sample_phaseB_pkt()

            if pkt > remaining:
                if remaining >= min(PHASEB_SIZES):
                    pkt = min(PHASEB_SIZES)
                else:
                    continue

            row_dest[i] = k
            row_size[i] = pkt
            burst_sent[k] += pkt
            active += 1

        if active == 0:
            break

        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

        if all(burst_sent[k] >= burst_quota[k] for k in egress_set):
            break

    write_csv(dest_port, size, label)

if __name__ == "__main__":
    generate_two_phase()