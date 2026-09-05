# T = runtime 
import csv
import random
import copy
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import math
import sys
import os
import re
import joblib

ALG_TAG = "credence" 

# ==========================================
# 1. FAST FOREST CLASS
# ==========================================
class FastForest:
    def __init__(self, sklearn_model):
        self.trees = []
        for estimator in sklearn_model.estimators_:
            tree_structure = estimator.tree_
            tree_data = {
                'feature': tree_structure.feature.tolist(),
                'threshold': tree_structure.threshold.tolist(),
                'children_left': tree_structure.children_left.tolist(),
                'children_right': tree_structure.children_right.tolist(),
                'value': tree_structure.value.tolist()
            }
            self.trees.append(tree_data)

    def predict(self, f0, f1, f2, f3):
        votes_for_drop = 0
        total_trees = len(self.trees)
        
        for tree in self.trees:
            node = 0 
            while tree['children_left'][node] != -1:
                feature_idx = tree['feature'][node]
                if feature_idx == 0: val = f0
                elif feature_idx == 1: val = f1
                elif feature_idx == 2: val = f2
                else: val = f3
                
                if val <= tree['threshold'][node]:
                    node = tree['children_left'][node]
                else:
                    node = tree['children_right'][node]
            
            counts = tree['value'][node][0]
            if counts[1] > counts[0]:
                votes_for_drop += 1
        
        return 1 if votes_for_drop > (total_trees / 2) else 0

# ==========================================
# 2. GLOBAL CONFIG & STATE
# ==========================================

N = 8  
MAX_PACKET_SIZE = 1500
T = 2000 
cell_size = 80
TOTAL_MEMORY = 26214 

# CREDENCE STATE VARIABLES
virtual_T = [0] * N          
virtual_gamma = 0            
avg_q_len = [0.0] * N        
avg_shared_occ = 0.0         
ewma_alpha = 2 / (30 + 1)    
credence_model = None  
ml_dropped_per_port = [0] * N      

# Standard Simulator State
dept_time = [[0] * 2000 for _ in range(N)]
size = [[0] * 2000 for _ in range(N)]
dest_port = [[0] * 2000 for _ in range(N)]
data = [[] for _ in range(N)]        
t_series = []        
q = [[[] for _ in range(N)] for _ in range(N)] 
voq_len = [[0 for c in range(N)] for d in range(N)] 

class MemoryPool:
    def __init__(self, num_cells: int, cell_size: int):
        self.cell_size = cell_size
        self.num_cells = num_cells
        self.base_address = 0x10000000
        self.free_list = list(range(num_cells))
        self.allocated = set()

    def malloc(self) -> int | None:
        if not self.free_list:
            return None
        idx = self.free_list.pop(0)
        self.allocated.add(idx)
        return self.base_address + idx * self.cell_size

    def deallocate(self, addr: int) -> None:
        offset = addr - self.base_address
        if offset < 0 or offset % self.cell_size != 0:
            raise ValueError(f"Invalid address: {hex(addr)}")
        idx = offset // self.cell_size
        if idx not in self.allocated:
            raise ValueError(f"Address not allocated: {hex(addr)}")
        self.allocated.remove(idx)
        self.free_list.append(idx)

    def free_count(self) -> int:
        return len(self.free_list)

memory_manager = MemoryPool(TOTAL_MEMORY, cell_size)
free_blocks = TOTAL_MEMORY 

# Stats tracking
total_packets = 0
packet_dropped = 0
packet_served = 0
packet_admission_status = [False] * N
active_ports = []
bytes_sent = [0]*N
min_pack_sent = 0

# ==========================================
# 3. CREDENCE HELPER FUNCTIONS
# ==========================================

def _update_virtual_lqd(port_idx, event_type, size=1):
    """
    Updates the Virtual (Shadow) LQD system state.
    
    Args:
        port_idx (int): The port index (0 to N-1).
        event_type (str): 'arrival' or 'departure'.
        size (int): The number of cells (e.g., 19 for a 1500B packet).
    """
    global virtual_T, virtual_gamma, TOTAL_MEMORY
    
    if event_type == 'arrival':
        # 1. Tentatively add the new packet cells
        virtual_T[port_idx] += size
        virtual_gamma += size
        
        # 2. Enforce Limit (Iterative Push-out)
        # While the virtual buffer is overflowing, remove cells from the longest queue.
        # We loop because the 'longest' queue might shift as we remove cells, 
        # or the longest queue might run out of cells before we free enough space.
        while virtual_gamma > TOTAL_MEMORY:
            # Find the index of the queue holding the most virtual cells
            j = virtual_T.index(max(virtual_T))
            
            if virtual_T[j] > 0:
                # Optimization: We can remove 1 at a time, or chunks. 
                # Removing 1 is safer to ensure we respect the "longest queue" invariant strictly.
                # Given standard sizes (~19), this loop is very fast.
                virtual_T[j] -= 1
                virtual_gamma -= 1
            else:
                # Safety break: If gamma > Total but max queue is 0 (impossible state), stop.
                # This resets gamma to match reality to prevent infinite loops.
                virtual_gamma = sum(virtual_T) 
                if virtual_gamma > TOTAL_MEMORY:
                     # Hard reset if state is corrupted
                     virtual_gamma = TOTAL_MEMORY
                break
            
    elif event_type == 'departure':
        # Remove the full size of the departing packet
        if virtual_T[port_idx] >= size:
            virtual_T[port_idx] -= size
            virtual_gamma -= size
        else:
            # Prevent negative drift if virtual state was out of sync
            virtual_gamma -= virtual_T[port_idx]
            virtual_T[port_idx] = 0

def _update_ewma(port_idx):
    global avg_q_len, avg_shared_occ, q, free_blocks, TOTAL_MEMORY, ewma_alpha
    
    phys_q_len = sum([len(q[port_idx][h]) for h in range(N)])
    phys_occ = TOTAL_MEMORY - free_blocks
    
    avg_q_len[port_idx] = (ewma_alpha * phys_q_len) + ((1 - ewma_alpha) * avg_q_len[port_idx])
    avg_shared_occ = (ewma_alpha * phys_occ) + ((1 - ewma_alpha) * avg_shared_occ)

# ==========================================
# 4. CORE LOGIC
# ==========================================

def bit_mapper(d_port, cell_len, s_port, cell_count):
    global final_add, trk, free_blocks, dropped_packet, nppq, total_packets, packet_admission_status
    global virtual_T, credence_model, q, TOTAL_MEMORY, ml_dropped_per_port
    
    lqd_bit = [0]*N
    shift_list_in_place(final_add)

    for i in range(N):
        if d_port[i] != -1:
            buffer[0][i] = [d_port[i], cell_len[i], s_port[i], cell_count[i]]
            if cell_len[i] == 0:
                total_packets += 1
        else:
            buffer[0][i] = [-1, -1, -1, -1]

    for i in range(N):
        dest = d_port[i]
        size = cell_count[i]
        if dest == -1:
            lqd_bit[i] = 1 
            final_add[0][i] = -1
            continue

        if cell_len[i] == 0:
            _update_virtual_lqd(dest, 'arrival',size)
            _update_ewma(dest)
            
            decision = "DROP"
            current_q_len = sum([len(q[dest][h]) for h in range(N)])
            current_shared_occ = TOTAL_MEMORY - free_blocks
            
            max_q = 0
            for p in range(N):
                p_len = sum([len(q[p][h]) for h in range(N)])
                if p_len > max_q: max_q = p_len
            
            safeguard_thresh = TOTAL_MEMORY / N
            
            if max_q < safeguard_thresh:
                decision = "ACCEPT"
            else:
                if current_q_len < virtual_T[dest]:
                    if credence_model is not None:
                        pred = credence_model.predict(
                            current_q_len, 
                            current_shared_occ, 
                            avg_q_len[dest], 
                            avg_shared_occ
                        )
                        if pred == 0: 
                            decision = "ACCEPT"
                            
                            #print("accepting coz credence said")
                            #breakpoint()
                        else: 
                            decision = "DROP"
                            ml_dropped_per_port[dest] += 1
                            #print("dropping coz credence said")
                            #breakpoint()
                    else:
                        print("Model not found")
                        #breakpoint()
                        decision = "ACCEPT"
                else:
                    print("Thresold drop")
                    #breakpoint()
                    decision = "DROP"

            needed_space = 19*N
            if free_blocks < needed_space:
                decision = "DROP"
                #print("No space available")
                #breakpoint()
            if decision == "ACCEPT":
                packet_admission_status[i] = True
                lqd_bit[i] = 1
                final_add[0][i] = memory_manager.malloc()
                free_blocks -= 1
            else:
                packet_admission_status[i] = False
                lqd_bit[i] = 1 
                final_add[0][i] = -1 

        else:
            if packet_admission_status[i] and free_blocks > 0:
                lqd_bit[i] = 1
                final_add[0][i] = memory_manager.malloc()
                free_blocks -= 1
            else:
                lqd_bit[i] = 1
                final_add[0][i] = -1

    return lqd_bit

def allct(r,t):
    global q, trk, cnt, last_q, voq_len, free_blocks, packet_dropped, buffer
    
    for i,k in enumerate(final_add[-1]):
        if final_add[-1][i] != -1:
            dest = buffer[-1][i][0]
            
            if (0 == buffer[-1][i][1] and last_q[i][1] == 0) or (last_q[i][1] == 1):
                q[dest][i].append([final_add[-1][i], buffer[-1][i][1], buffer[-1][i][2], buffer[-1][i][3]])
                voq_len[dest][i] += 1
                last_q[i] = [buffer[-1][i][1], 1]
            else:
                memory_manager.deallocate(final_add[-1][i])
                free_blocks += 1
                if buffer[-1][i][1] == 0: packet_dropped += 1
        
        elif 0 == buffer[-1][i][1] and last_q[i][1] == 0:
            packet_dropped += 1

        if buffer[-1][i][0] != -1 and last_q[i][1] == 1 and final_add[-1][i] == -1:
            last_q[i][1] = 0
            if buffer[-1][i][1] == 0:
                packet_dropped += 1
            else:
                dest = buffer[-1][i][0]
                packets_to_remove = buffer[-1][i][1]
                if packets_to_remove > len(q[dest][i]): packets_to_remove = len(q[dest][i])
                breakpoint()

    shift_list_in_place(buffer)

def deallocate():
    global free_blocks, rr, stall_s, track_s, voq_len, q, p_y, packet_served, reading, count, bytes_sent
    global active_ports
    
    current_active = [0]*N

    for d in range(0,N): 
        for l in range(N):
            if len(q[d][l]) > 0: current_active[d] = 1
            
            if q[d][l]:
                if (voq_len[d][l] >= q[d][l][0][3] and p_y[d][l] == 0 and q[d][l][0][1] == 0 and (reading[d] != 0 or q[d][l][0][3] != 1)):
                    if voq_len[d][l] >= q[d][l][0][3]:
                        voq_len[d][l] -= q[d][l][0][3]
                        p_y[d][l] = 1
                        if count[d] == -1:
                            count[d] = 0
                            rr[d] = l
                    else:
                        p_y[d][l] = 0
        
        if (stall_s[d] <= track_s[d] and count[d] != -1) or count[d] == 0:
            if reading[d] != -1:
                send = q[d][rr[d]].pop(0)
                memory_manager.deallocate(send[0])
                bytes_sent[d] += send[2]
                
                if send[1] == 0:
                    packet_served += 1
                    _update_virtual_lqd(d, 'departure',send[3])
                    
                free_blocks += 1

            if reading[d] == count[d]-1 and count[d] != 0:
                for l in range(0,N):
                    if p_y[d][(rr[d]+1+l)%N] != 0:
                        if not q[d][rr[d]] and p_y[d][rr[d]] == 1:
                            p_y[d][rr[d]] = 0
                        rr[d] = (rr[d]+1+l)%N
                        count[d] = q[d][rr[d]][0][3]
                        track_s[d] = 1
                        stall_s[d] = q[d][rr[d]][0][2]*8/(link_speed*time_period)
                        reading[d] = 0
                        break
                    count[d] = -1
                    reading[d] = -1
            elif count[d] == 0: 
                count[d] = q[d][rr[d]][0][3]
                track_s[d] = 1
                stall_s[d] = q[d][rr[d]][0][2]*8/(link_speed*time_period)
                reading[d] = 0
            else:
                reading[d] = q[d][rr[d]][0][1]
                track_s[d] = 1
                stall_s[d] = q[d][rr[d]][0][2]*8/(link_speed*time_period)
            
            if reading[d] == count[d]-1:
                if voq_len[d][rr[d]] > 1:    
                    if voq_len[d][rr[d]] >= q[d][rr[d]][1][3]: 
                        voq_len[d][rr[d]] -= q[d][rr[d]][1][3]
                        p_y[d][rr[d]] = 1
                    else:
                        p_y[d][rr[d]] = 0
                else:
                    p_y[d][rr[d]] = 0
        elif stall_s[d] > track_s[d]:
            track_s[d] += 1

    active_ports.append(sum(current_active))


# ==========================================
# 5. MAIN AND UTILS
# ==========================================

def read_csv(burst,incast,round):
    csv_file_path = f"output_new_{burst}_{incast}_{round}.csv"
    global n_dest_port, n_size
    n_dest_port = []
    n_size = []
    with open(csv_file_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader) 
        for row in reader:
            t, i, dp, sz = map(int, row)
            if len(n_dest_port) <= i:
                n_dest_port.append([])
                n_size.append([])
            n_dest_port[i].append(dp)
            n_size[i].append(sz)
    return n_size, n_dest_port

def shift_list_in_place(l):
    if len(l) <= 1: return
    last_element = l.pop()
    l.insert(0, last_element)

def pad_to_cell(bytes_, cell_size):
    return ((bytes_ + cell_size - 1) // cell_size) * cell_size

def log_q_sums(q, t=None, path="./q_log/q_sums.csv", include_time=True, reset=False):
    import os, csv
    N = len(q)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    need_header = reset or not os.path.exists(path)
    if need_header:
        with open(path, "w", newline="") as f:
            header = (["t"] if include_time else []) + [f"i{i}" for i in range(N)]
            csv.writer(f).writerow(header)
    row = ([t] if (include_time and t is not None) else []) + [sum(len(q[i][j]) for j in range(N)) for i in range(N)]
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)

def plot_and_save_active_queues(i, title="Active Queues", xlabel="Time", ylabel="Count"):
    global active_ports
    BASE_DIR = Path("master/credence_logs") 
    BASE_DIR.mkdir(parents=True, exist_ok=True) 
    
    csv_path = BASE_DIR / f"output_credence_n_2_{i}.csv"
    png_path = BASE_DIR / f"output_credence_n_2_{i}.png"
    
    pd.Series(active_ports, name="active_queues").to_csv(csv_path, index_label="time_step")
    y = list(active_ports)
    plt.figure(figsize=(8, 4))
    plt.plot(range(len(y)), y, linewidth=1.8)
    plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.4); plt.tight_layout()
    plt.savefig(png_path, bbox_inches="tight"); plt.close()

# Execution variables
final_add = [[-1 for i in range(N)] for _ in range(2)] 
buffer = [[[-1,-1]]*N for _ in range(2)]   
last_q = [[0,0] for _ in range(N)]
lag = 2
prev_lqd_bit_map = [0 for i in range(N)] 

stop = [-2]*N
tra = [-1]*N
reading = [-1]*N
count = [-1]*N
stall_s = [0.0]*N
track_s = [0]*N
p_y = [[0 for i in range(N)] for _ in range(N)]
rr = [0]*N

link_speed = 4*10**11 
time_period = 1*(10**-9) 

def main(burst, incast, round, alpha):
    global t, credence_model
    
# === LOAD ML MODEL ===

    try:
        model_dir = "."
        model_filename = f"model_ports{N}_trees1_depth4.joblib"
        model_path = os.path.join(model_dir, model_filename)
        print(f"Loading raw model: {model_path}...")
        raw_model = joblib.load(model_path)
        credence_model = FastForest(raw_model)
        del raw_model
        print("CREDENCE: Optimized model ready.")
        if not found:
            print(f"WARNING: No model found for ports {N}. Running without predictions.")
    except Exception as e:
        print(f"Error loading model: {e}")

    # Standard Sim Init
    size, dest_port = read_csv(burst, incast, round)
    size_e = copy.deepcopy(size)
    stall = [-1 for _ in range(N)]
    v = 0
    v_i = [0]*N
    track = [0 for _ in range(N)]
    d_port = [-1]*N
    s_port = [-1]*N
    cell_len = [-1]*N
    cell_count = [0]*N
    phase_2 = 0
    t = 0
    prev_lqd_bit_map = [0] * N 
    global ml_dropped_per_port
    ml_dropped_per_port = [0] * N
    
    Q_LOG_DIR = Path("master/q_log")
    # Main Time Loop
    while True:
        t += 1
        log_q_sums(q, t, path=f"./q_log/q_sums_{burst}_{incast}_{round}_{alpha}_credence.csv")
        
        ray_of_death = 0
        for i in range(0,N):
            if dest_port[0][v] != 0 and not phase_2:
                v_i = [v]*N; phase_2 = 1
            if not phase_2:
                if track[i] > stall[i] and v < len(size[i])-1:
                    track[i] = 1
                    d_port[i] = dest_port[i][v]
                    if dest_port[i][v] != -1: ray_of_death = 1
                    if cell_len[i] == -1: 
                        size[i][v] = pad_to_cell(size[i][v], cell_size)
                        s_port[i] = min(size_e[i][v], cell_size)
                        cell_count[i] = math.ceil(size[i][v]/cell_size)
                    else:
                        s_port[i] = min(size_e[i][v], cell_size)
                        cell_count[i] = 0
                    stall[i] = min(cell_size*8/(link_speed*time_period), size[i][v]*8/(link_speed*time_period))
                    size[i][v] -= cell_size
                    size_e[i][v] -= cell_size
                    cell_len[i] += 1
                elif dest_port[i][v] != -1 and len(dest_port[i]) != v+1:
                    ray_of_death = 1
                    track[i]+=1; d_port[i]=-1; s_port[i]=0
            else:
                 if track[i] > stall[i] and v_i[i]<len(size[i])-1:
                    track[i] = 1
                    d_port[i] = dest_port[i][v_i[i]]
                    if dest_port[i][v_i[i]] != -1: ray_of_death = 1
                    if cell_len[i] == -1: 
                        size[i][v_i[i]] = pad_to_cell(size[i][v_i[i]], cell_size)
                        s_port[i] = min(size_e[i][v_i[i]], cell_size)
                        cell_count[i] = math.ceil(size[i][v_i[i]]/cell_size)
                    else:
                        s_port[i] = min(size_e[i][v_i[i]], cell_size)
                        cell_count[i] = 0
                    stall[i] = min(cell_size*8/(link_speed*time_period), size[i][v_i[i]]*8/(link_speed*time_period))
                    size[i][v_i[i]] -= cell_size
                    size_e[i][v_i[i]] -= cell_size
                    cell_len[i] += 1
                 elif dest_port[i][v_i[i]]!=-1 and len(dest_port[i]) != v_i[i]+1:
                    ray_of_death = 1
                    track[i]+=1; d_port[i]=-1; s_port[i]=0

        lqd_bit_map = bit_mapper(d_port, cell_len, s_port, cell_count)
        allct(prev_lqd_bit_map, t)
        deallocate()
        prev_lqd_bit_map = lqd_bit_map
        
        if not phase_2:
            for i in range(0,N):
                if size[i][v] <= 0: cell_len[i] = -1
            if all(size[i][v] <= 0 for i in range(N)):
                if len(dest_port[i])-1 > v: v += 1
        else:
            for i in range(0,N):
                if size[i][v_i[i]] <= 0:
                    cell_len[i] = -1
                    if len(dest_port[i])-1 > v_i[i]: v_i[i] += 1

        d_port = [-1]*N
        s_port = [-1]*N
        if ray_of_death == 0: break

    while True:
        gg = 0
        t += 1
        log_q_sums(q, t, path=f"./q_log/q_sums_{burst}_{incast}_{round}_{alpha}_credence.csv")
        for c in range(N):
            for h in range(N):
                if len(q[c][h]) >= 19: 
                    deallocate()
                    gg = 1
                    break
        if gg == 0: break
    
    return t

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 5:
        print("Usage: python credence_sim.py <burst> <incast> <round> <alpha>")
        sys.exit(1)

    i = int(sys.argv[1])
    incast = sys.argv[2]
    rnd = int(sys.argv[3])
    alpha_val = float(sys.argv[4])
    
    LOG_DIR = Path("master/credence_logs")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = LOG_DIR / f'output_credence_{i}_{incast}_{rnd}.txt'
    
    # 1. Run Main Simulation
    print(f"--- Starting Simulation for Burst={i} ---")
    time = main(i, incast, rnd, alpha_val)
    
    # 2. Calculate Stats
    total_bits = sum(bytes_sent) * 8
    duration_seconds = time * time_period
    
    if duration_seconds > 0:
        agg_throughput_gbps = (total_bits * 1e-9) / duration_seconds
        avg_throughput_per_port = agg_throughput_gbps / N
    else:
        agg_throughput_gbps = 0
        avg_throughput_per_port = 0

    # 3. Create Report String
    report = [
        f"dropped_packet = {packet_dropped}",
        f"Over in t = {time}",
        f"packets served = {packet_served}",
        f"200Byte packet sent = {min_pack_sent}",
        f"1500Byte packet sent = {packet_served - min_pack_sent}",
        "CREDENCE algo",
        f"{agg_throughput_gbps:.4f} Gbps (Aggregate)",
        f"{avg_throughput_per_port:.4f} Gbps (Per Port Average)",
        f"ML Drops per Port: {ml_dropped_per_port}",
        f"Total ML Drops: {sum(ml_dropped_per_port)}"
    ]
    report_text = "\n".join(report)

    # 4. Print to Terminal (So you see it now)
    print("\n" + "="*30)
    print("      SIMULATION RESULTS      ")
    print("="*30)
    print(report_text)
    print("="*30)

    # 5. Write to File (So it saves to the log)
    # This was the missing step!
    with open(output_file, 'w') as f:
        f.write(report_text + "\n")

    plot_and_save_active_queues(i)
    print(f"\nLog file saved to: {output_file}")