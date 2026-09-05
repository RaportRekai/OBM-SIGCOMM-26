#!/usr/bin/env python3
"""
two_phase_workload.py
─────────────────────
Phase A:
  • Only ingress 0 and 1 send 1500-B packets to egress 0 each timestep.
  • Stop when bytes_to_egress[0] reaches floor(1.8 × PORT_BUFFER) aligned to 1500 B.

Phase B:
  • All N_PORTS ingresses active.
  • Each ingress i sends packets to egress = INCAST_LIST[i] (0-indexed).
  • Packet size is sampled from {1440, 200} (50/50). If 1440 doesn't fit the remaining
    per-egress quota, fall back to 200; if 200 doesn't fit, that ingress idles this step.
  • For each egress k in INCAST_LIST, cap aggregate bytes at floor(burst% × PORT_BUFFER)
    aligned to 1500 B (unchanged).
Invariant:
  • Never write a timestep where all ingresses are idle (skip trailing all-idle).
CSV:
  • Columns: t, i, dest_port, size  (−1 for idle), file: output_new_{label}.csv
"""

from __future__ import annotations
import sys
import csv
import os
import random

# ─────────── Constants (kept consistent) ───────────
N_PORTS       = 8
PORT_BUFFER   = 2 * 1024 * 1024      # bytes per egress
PACKET_BYTES  = 1500                 # Phase A packet size (fixed)

# 0-indexed mapping: ingress i → egress INCAST_LIST[i]
INCAST_LIST_LOAD = {
    # 2 ingresses per egress (Balanced)
    "uniform": [1, 1, 2, 2, 3, 3, 4, 4],
    
    # ~50% traffic to egress 0, rest distributed
    "zipf":    [1, 1, 1, 1, 2, 2, 3, 3],
    
    # ~60-70% traffic to egress 0 (Highly imbalanced)
    "skewed":  [1, 1, 1, 1, 1, 2, 2, 2]
}
INCAST_LIST = INCAST_LIST_LOAD[sys.argv[2]] 
#[1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8] 
#[1,1,1,1,1,1,1,1,1,2,2,3,3,3,4,4] 
#[1,1,1,1,1,1,1,3,3,3,3,5,5,5,6,6]
assert len(INCAST_LIST) == N_PORTS, "INCAST_LIST length must equal N_PORTS"

# ─────────── Phase-B packet sampler: {1440, 200} 50/50 ───────────
PHASEB_SIZES = (1500, 1500)

def sample_phaseB_pkt() -> int:
    return PHASEB_SIZES[0] if random.random() < 0.5 else PHASEB_SIZES[1]

def _bytes_quota_aligned(percent: float) -> int:
    """floor(percent * PORT_BUFFER) to a multiple of PACKET_BYTES (1500)."""
    raw = int(PORT_BUFFER * percent / 100.0)
    return (raw // PACKET_BYTES) * PACKET_BYTES

def write_csv(dest_port, size, label: str):
    path = f"output_new_{label}.csv"

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
    # ── CLI: keep your label shape: <burst_percent> <incast_tag> <rounds_tag>
    if len(sys.argv) < 4:
        print("Usage: two_phase_workload.py <burst_percent> <incast_tag> <rounds_tag>")
        sys.exit(1)
    burst_percent = int(sys.argv[1])     # per-egress (Phase B) quota %
    incast_tag    = sys.argv[2]          # only used for file label
    rounds_tag    = sys.argv[3]          # only used for file label
    label = f"{burst_percent}_{incast_tag}_{rounds_tag}"

    # ── Storage
    dest_port = [[] for _ in range(N_PORTS)]
    size      = [[] for _ in range(N_PORTS)]

    # ── Phase A: ingress 0 & 1 → egress 0 until 1.8× buffer (aligned)
    phaseA_quota = _bytes_quota_aligned(180.0)  # 180% of buffer
    egress_bytes = [0] * N_PORTS

    while egress_bytes[0] + 2 * PACKET_BYTES <= phaseA_quota:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS
        # Only ingresses 0 and 1 are active (1500-B packets)
        row_dest[0] = 0; row_size[0] = PACKET_BYTES
        row_dest[1] = 0; row_size[1] = PACKET_BYTES
        egress_bytes[0] += 2 * PACKET_BYTES

        # append timestep
        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

    # If exactly one more 1500-B packet (not both) would fit, emit one more step.
    remaining = phaseA_quota - egress_bytes[0]
    if remaining >= PACKET_BYTES and remaining < 2 * PACKET_BYTES:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS
        row_dest[0] = 0; row_size[0] = PACKET_BYTES
        egress_bytes[0] += PACKET_BYTES
        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

    # ── Phase B: all ingresses active, mapped by INCAST_LIST; per-egress burst quota
    burst_quota = {}
    burst_sent  = {}
    egress_set  = sorted(set(INCAST_LIST))
    for k in egress_set:
        burst_quota[k] = _bytes_quota_aligned(float(burst_percent))  # still aligned to 1500
        burst_sent[k]  = 0

    while True:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS
        active   = 0

        for i in range(N_PORTS):
            k = INCAST_LIST[i]
            remaining = burst_quota[k] - burst_sent[k]
            if remaining < 200:
                # cannot fit even the smallest Phase-B packet
                continue

            pkt = sample_phaseB_pkt()
            if pkt > remaining:
                # fallback to 200 if 1440 didn't fit
                if remaining >= 200:
                    pkt = 200
                else:
                    continue

            # send
            row_dest[i] = k
            row_size[i] = pkt
            burst_sent[k] += pkt
            active += 1

        # Stop if no one sent this timestep (prevents writing all-idle rows)
        if active == 0:
            break

        # Append the timestep
        for i in range(N_PORTS):
            dest_port[i].append(row_dest[i])
            size[i].append(row_size[i])

        # If every egress in the incast set has reached its quota, next loop would be idle → exit now.
        if all(burst_sent[k] >= burst_quota[k] for k in egress_set):
            break

    # ── Write CSV with your original naming convention
    write_csv(dest_port, size, label)

if __name__ == "__main__":
    generate_two_phase()
