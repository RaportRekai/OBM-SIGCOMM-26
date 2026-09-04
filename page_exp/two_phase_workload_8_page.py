#!/usr/bin/env python3
"""
three_phase_workload.py
───────────────────────
Session 1 / Phase A:
  • Only ingress 0 and 1 send 160-B packets to egress 0 each timestep.
  • Stop when bytes_to_egress[0] reaches floor(1.8 × PORT_BUFFER) aligned to 160 B.

Session 2 / Phase B:
  • All N_PORTS ingresses active.
  • Each ingress i sends packets to egress = SESSION2_INCAST_LIST[i] (0-indexed).
  • Packet size is sampled from PHASEB_SIZES.
  • For each egress k in SESSION2_INCAST_LIST, cap aggregate bytes at
    floor(burst% × PORT_BUFFER) aligned to 160 B.

Session 3 / Phase C:
  • Same control parameters as Session 2.
  • Uses a different incast list: SESSION3_INCAST_LIST.
  • Same per-egress quota, same packet sampler, same idle-row rule.

Invariant:
  • Never write a timestep where all ingresses are idle.

CSV:
  • Columns: t, i, dest_port, size
  • size = -1 for idle
  • file: output_new_{label}.csv
"""

from __future__ import annotations
import sys
import csv
import os
import random
import sys

# ─────────── Constants ───────────
N_PORTS       = 8
PORT_BUFFER   = int(sys.argv[-1])*80 #2 * 1024 * 1024      # bytes per egress
PACKET_BYTES  = 160                 # Phase A packet size and quota alignment


# ─────────── Session 2 incast mapping ───────────
# 0-indexed mapping: ingress i → egress SESSION2_INCAST_LIST[i]
INCAST_LIST_LOAD_SESSION2 = {
    # Balanced-ish
    "uniform": [3, 3, 3, 3, 4, 4, 4, 4],

    # More traffic concentrated on egress 1
    "zipf":    [1, 1, 1, 1, 2, 2, 3, 3],

    # Highly imbalanced
    "skewed":  [1, 1, 1, 1, 1, 2, 2, 2],
}


# ─────────── Session 3 incast mapping ───────────
# Edit this list to whatever second burst session you want.
# It has the same controls as Session 2, but can target different egresses.
INCAST_LIST_LOAD_SESSION3 = {
    # Example: shift uniform burst to different egresses
    "uniform": [5, 5, 5, 5, 6, 6, 6, 6],

    # Example: shift zipf burst away from Session 2 egresses
    "zipf":    [4, 4, 4, 4, 5, 5, 6, 6],

    # Example: another skewed burst to a different hot egress
    "skewed":  [4, 4, 4, 4, 4, 5, 5, 5],
}


# ─────────── Phase-B / Phase-C packet sampler ───────────
# Your comment said {1440, 200}, but your code had (160, 160).
# I kept your current behavior as-is.
PHASEB_SIZES = (160, 160)

def sample_phaseB_pkt() -> int:
    return PHASEB_SIZES[0] if random.random() < 0.5 else PHASEB_SIZES[1]


def _bytes_quota_aligned(percent: float) -> int:
    """
    floor(percent * PORT_BUFFER) to a multiple of PACKET_BYTES.
    """
    raw = int(PORT_BUFFER * percent / 100.0)
    return (raw // PACKET_BYTES) * PACKET_BYTES


def append_row(dest_port, size, row_dest, row_size):
    """
    Append one timestep row to the per-ingress storage.
    """
    for i in range(N_PORTS):
        dest_port[i].append(row_dest[i])
        size[i].append(row_size[i])


def write_csv(dest_port, size, label: str):
    path = f"output_new_{label}_{sys.argv[-1]}.csv"

    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    T = len(dest_port[0])
    L = len(dest_port)

    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "i", "dest_port", "size"])

        for t in range(T):
            for i in range(L):
                eg = dest_port[i][t]
                w.writerow([
                    t,
                    i,
                    eg,
                    size[i][t] if eg >= 0 else -1
                ])

    print(f"✓  {path}")


def generate_burst_session(
    dest_port,
    size,
    incast_list,
    burst_percent: int,
    session_name: str,
):
    """
    Generic burst session used by both Session 2 and Session 3.

    Same control parameters:
      • same burst_percent
      • same per-egress quota
      • same packet-size sampler
      • same fallback behavior
      • same no-all-idle invariant
    """

    assert len(incast_list) == N_PORTS, (
        f"{session_name}: incast list length must equal N_PORTS"
    )

    burst_quota = {}
    burst_sent  = {}

    egress_set = sorted(k for k in set(incast_list) if k >= 0)

    for k in egress_set:
        burst_quota[k] = _bytes_quota_aligned(float(burst_percent))
        burst_sent[k]  = 0

    while True:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS
        active   = 0

        for i in range(N_PORTS):
            k = incast_list[i]

            if k < 0:
                continue

            remaining = burst_quota[k] - burst_sent[k]

            if remaining < 200:
                continue

            pkt = sample_phaseB_pkt()

            if pkt > remaining:
                if remaining >= 200:
                    pkt = 200
                else:
                    continue

            row_dest[i] = k
            row_size[i] = pkt
            burst_sent[k] += pkt
            active += 1

        # Prevent writing all-idle rows
        if active == 0:
            break

        append_row(dest_port, size, row_dest, row_size)

        # If all egresses have reached quota, stop immediately
        if all(burst_sent[k] >= burst_quota[k] for k in egress_set):
            break

    print(f"{session_name}: sent bytes per egress = {burst_sent}")


def generate_three_phase():
    # ── CLI: <burst_percent> <incast_tag> <rounds_tag>
    if len(sys.argv) < 4:
        print("Usage: three_phase_workload.py <burst_percent> <incast_tag> <rounds_tag>")
        print("Example: three_phase_workload.py 40 uniform 1")
        sys.exit(1)

    burst_percent = int(sys.argv[1])
    incast_tag    = sys.argv[2]
    rounds_tag    = sys.argv[3]

    if incast_tag not in INCAST_LIST_LOAD_SESSION2:
        print(f"Unknown incast tag for Session 2: {incast_tag}")
        print(f"Available tags: {list(INCAST_LIST_LOAD_SESSION2.keys())}")
        sys.exit(1)

    if incast_tag not in INCAST_LIST_LOAD_SESSION3:
        print(f"Unknown incast tag for Session 3: {incast_tag}")
        print(f"Available tags: {list(INCAST_LIST_LOAD_SESSION3.keys())}")
        sys.exit(1)

    session2_incast_list = INCAST_LIST_LOAD_SESSION2[incast_tag]
    session3_incast_list = INCAST_LIST_LOAD_SESSION3[incast_tag]

    assert len(session2_incast_list) == N_PORTS, (
        "SESSION2_INCAST_LIST length must equal N_PORTS"
    )
    assert len(session3_incast_list) == N_PORTS, (
        "SESSION3_INCAST_LIST length must equal N_PORTS"
    )

    label = f"{burst_percent}_{incast_tag}_{rounds_tag}"

    # ── Storage
    dest_port = [[] for _ in range(N_PORTS)]
    size      = [[] for _ in range(N_PORTS)]

    # ─────────────────────────────────────────────
    # Session 1 / Phase A:
    # ingress 0 and 1 → egress 0
    # ─────────────────────────────────────────────
    phaseA_quota = _bytes_quota_aligned(180.0)
    egress_bytes = [0] * N_PORTS

    while egress_bytes[0] + 2 * PACKET_BYTES <= phaseA_quota:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS

        row_dest[0] = 0
        row_size[0] = PACKET_BYTES

        row_dest[1] = 0
        row_size[1] = PACKET_BYTES

        egress_bytes[0] += 2 * PACKET_BYTES

        append_row(dest_port, size, row_dest, row_size)

    # If exactly one more 160-B packet fits, emit one more step.
    remaining = phaseA_quota - egress_bytes[0]

    if remaining >= PACKET_BYTES and remaining < 2 * PACKET_BYTES:
        row_dest = [-1] * N_PORTS
        row_size = [-1] * N_PORTS

        row_dest[0] = 0
        row_size[0] = PACKET_BYTES

        egress_bytes[0] += PACKET_BYTES

        append_row(dest_port, size, row_dest, row_size)

    print(f"Session 1: sent bytes to egress 0 = {egress_bytes[0]}")

    # ─────────────────────────────────────────────
    # Session 2 / Phase B:
    # Burst according to first incast list
    # ─────────────────────────────────────────────
    generate_burst_session(
        dest_port=dest_port,
        size=size,
        incast_list=session2_incast_list,
        burst_percent=burst_percent,
        session_name="Session 2",
    )

    # ─────────────────────────────────────────────
    # Session 3 / Phase C:
    # Burst according to second incast list
    # Same control parameters as Session 2
    # ─────────────────────────────────────────────
    # generate_burst_session(
    #     dest_port=dest_port,
    #     size=size,
    #     incast_list=session3_incast_list,
    #     burst_percent=burst_percent,
    #     session_name="Session 3",
    # )

    # ── Write CSV
    write_csv(dest_port, size, label)


if __name__ == "__main__":
    generate_three_phase()