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
from typing import List
import sys
import numpy as np
import bisect
from typing import List, Tuple, Sequence
# ─────────── Scenario constants ───────────
N_PORTS          = 16
PORT_BUFFER      = 2 * 1024 * 1024               # bytes (per port)
BURST_PERCENT_SET    = [20, 30, 40, 50, 60]          # 5 scenarios
ROUNDS           = 5                             # merged
PACKET_BYTES     = 1500
IDLE_THRESHOLD   = 16                            # >10 idle lanes ends round
INCAST_VECTOR_SET = {'zipf':[1,2,13,1,1,1,13,0,5,3,2,1,1,1,1,0],'skewed':[1,2,13,1,1,1,13,0,8,2,1,1,1,1,0,0],
                     'uniform':[1, 2, 13, 1, 1, 1, 13, 0, 0, 2, 2, 2, 2, 2, 2, 2]}
pct = int(sys.argv[2])
INCAST_VECTOR = INCAST_VECTOR_SET[sys.argv[1]] 
#[1, 2, 13, 1, 1, 1, 13, 0, 0, 2, 2, 2, 2, 2, 2, 2]
#[1, 2, 13, 1, 1, 1, 13, 0, 8, 2, 1, 1, 1, 1, 0, 0]
#[1, 2, 13, 1, 1, 1, 13, 0, 5, 3, 2, 1, 1, 1, 1, 0]

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
        stream.extend([int(eg+len(INCAST_VECTOR)/2 - 1)] * cnt)
    print(stream)
    return stream


# ─────────── Core generator - idle (lane-reuse, multi-round) ───────────
def generate_idle_traffic(idle_incast,quota):
    # idle incast - [0,0,1,2,2,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
    data_sent = [0]*N_PORTS
    finish = 0
    while True:
        for i in range(N_PORTS):
            dest_port[i].append(idle_incast[i])
            pkt = sample_packet()
            size[i].append(pkt)
            if idle_incast[i] != -1:
                data_sent[idle_incast[i]]+=pkt
            if(data_sent[i]>quota):
                finish = 1

        if finish == 1:
            break 

# ─────────── Core generator (lane-reuse, multi-round) ───────────
dest_port = [[] for _ in range(len(INCAST_VECTOR))]
size: List[List[int]] = [[] for _ in range(N_PORTS)]

def generate_traffic(idle_incast,
    continue_idle_incast,
    incast: List[int],
    limit_bytes: int,
    N: int,
    
) -> List[List[int]]:
    """Return dest_port matrix [lane][t] (size always 1500 or -1)."""
    conveyor      = _flatten_incast(incast)
    PORTS         = len(INCAST_VECTOR)
    
    global dest_port
    global size

    
    bytes_sent   = [0] * PORTS
    active_ports = {int(i+len(INCAST_VECTOR)/2-1) for i, c in enumerate(incast) if c}
    print(active_ports)
    conveyor_idx = 0
    lane_map     = [-1] * N                        # current egress/lane
    finish = 0
    def next_port() -> int:
        nonlocal conveyor_idx
        while conveyor_idx < len(conveyor):
            eg = conveyor[conveyor_idx]
            conveyor_idx += 1
            print(eg)
            if bytes_sent[eg] < limit_bytes:
                return eg
        return -1                                  # conveyor exhausted

    # initial assignment
    for lane in range(N):
        lane_map[lane] = next_port()

    # timestep loop
    data_sent = [0]*N_PORTS
    while active_ports:
        
        idle_count = 0
        for lane in range(N):
            # this loop iterates through the ingress ports and the idle count literally keeps track of the number of ports 
            # that remains idle for a single circulation and has to be set to zero after one circulation
            # the only function of lane_map is to feed eg which is the egress port that is being fed for that iteration
            # lane map stores the egress ports to which the packet must go to in that circulation
            # This lane_map changes each time the next_port() is called 
            #print(active_ports)
            #print(data_sent)
            #print(f"bytes sent - {bytes_sent}")
            if finish == 0 and continue_idle_incast==1:
                #print(f"Hey - {idle_incast[lane]}")
                if idle_incast[lane] != -1:
                    dest_port[lane].append(idle_incast[lane])
                    pkt = sample_packet()
                    size[lane].append(pkt)
                    #print("appending")
                    data_sent[idle_incast[lane]]+=pkt
                    if(data_sent[lane]>limit_bytes):
                        #print(f"discarding {idle_incast[lane]}")
                        active_ports.discard(idle_incast[lane])
                        finish = 1
                    continue
                
                    
            eg = lane_map[lane-sum([1 for i in idle_incast if i !=-1])]

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
                lane_map[lane-sum([1 for i in idle_incast if i !=-1])] = eg = next_port()
                if eg == -1:
                    dest_port[lane].append(-1)
                    size[lane].append(-1)
                    idle_count += 1
                    continue
                remaining = limit_bytes - bytes_sent[eg]

            dest_port[lane].append(eg)
            pkt = min(sample_packet(), max(remaining, 64))
            size[lane].append(pkt)
            bytes_sent[eg] += pkt

        # ── Early-termination check ──────────────────────────
        if idle_count > IDLE_THRESHOLD:
            break

    return dest_port,size

# ─────────── CSV writer ───────────
def write_csv(dest_port: List[List[int]], size: List[List[int]],label: str):
    path = f"output_new_{label}.csv"
    T, N = len(dest_port[0]), len(dest_port)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "i", "dest_port", "size"])
        print(len(size),len(size[1]))
        print(len(dest_port),len(dest_port[0]))
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
                served_ts [k] += 1
                lane_total[k] += h

    print("Average incast (lanes while port active)")
    for k in range(ports):
        if served_ts[k]:
            avg = lane_total[k] / served_ts[k]
            print(f"  Port {k:2d}: {avg:.2f} lanes  "
                  f"(active {served_ts[k]} timesteps)")
        else:
            print(f"  Port {k:2d}: never served")

# ─────────── Scenario driver ───────────
if __name__ == "__main__":
    pct_2 = 180
    continue_idle_incast = 1
    
    idle_incast = [0,0,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
    dest_port = [[] for _ in range(len(INCAST_VECTOR))]
    quota = (PORT_BUFFER * pct // 100 // PACKET_BYTES) * PACKET_BYTES
    for i in range(ROUNDS):
        if i>0:
            if sum([dest_port[f][-1] for f in range(N_PORTS)]) == -N_PORTS:
                print("removing the last set of packets")
                for dp in dest_port:
                    dp.pop()
                for sz in size:
                    sz.pop()
        quota = (PORT_BUFFER * pct_2 // 100 // PACKET_BYTES) * PACKET_BYTES
        generate_idle_traffic(idle_incast,quota)
        quota = (PORT_BUFFER * pct // 100 // PACKET_BYTES) * PACKET_BYTES
        generate_traffic(idle_incast,continue_idle_incast,
            INCAST_VECTOR[7:],
            quota,
            N_PORTS,
        )
    write_csv(dest_port, size, str(pct))
    print(f"\n✓  output_new_{pct}.csv  (quota {quota} B, {ROUNDS} rounds)")
    report_average_incast(dest_port, len(INCAST_VECTOR))

    print("\nAll scenarios complete.")
