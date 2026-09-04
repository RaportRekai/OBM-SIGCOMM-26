import math
import csv
import copy

# io_helpers.py --------------------------------------------------------------
from pathlib import Path
import numpy as np
import pandas as pd

                   # keep in sync with the rest of your code

def _lists_to_matrix(lists, fill=np.nan):
    """ragged list-of-lists  →  (N, T_max) numpy array, padded with `fill`."""
    max_len = max(len(row) for row in lists)
    mat = np.full((N, max_len), fill)
    for i, row in enumerate(lists):
        mat[i, :len(row)] = row
    return mat

class MemoryPool:
    def __init__(self, num_cells: int, cell_size: int):
        """
        Initialize a memory pool of `num_cells` cells, each of `cell_size` bytes.
        """
        self.cell_size = cell_size
        self.num_cells = num_cells
        # simulate a base address (for illustration)
        self.base_address = 0x10000000
        # free_list holds indices of cells that are free
        self.free_list = list(range(num_cells))
        # track which indices are currently allocated
        self.allocated = set()

    def malloc(self) -> int | None:
        """
        Allocate one K-byte cell.
        Returns the starting "address" of that cell (an integer),
        or None if no free cell is available.
        """
        if not self.free_list:
            return None
        idx = self.free_list.pop(0)
        self.allocated.add(idx)
        return self.base_address + idx * self.cell_size

    def deallocate(self, addr: int) -> None:
        """
        Return the cell at `addr` back to the free pool.
        Raises ValueError if `addr` is invalid or not currently allocated.
        """
        # compute the cell index from the address
        offset = addr - self.base_address
        if offset < 0 or offset % self.cell_size != 0:
            raise ValueError(f"Invalid address: {hex(addr)}")
        idx = offset // self.cell_size
        if idx not in self.allocated:
            raise ValueError(f"Address not allocated or already freed: {hex(addr)}")
        # free it
        self.allocated.remove(idx)
        self.free_list.append(idx)

    def free_count(self) -> int:
        """
        Returns the number of cells still in the free pool.
        """
        return len(self.free_list)

import sys
TOTAL_MEMORY = int(sys.argv[-1]) + 304 #int(22 * 1024 * 1024/cell_size)
cell_size = 80
memory_manager = MemoryPool(TOTAL_MEMORY,cell_size)
N = 8
#block_ports = [[0,0] for i in range(N)]

gate = [[0 for c in range(N)] for _ in range(N)]
q = [[[] for _ in range(N)] for _ in range(N)]
voq_len = [[0 for c in range(N)] for d in range(N)]

# def port_block():
#     for i in range(N):
#         if block_ports[i][0] == 1 and block_ports[i][1] > 0:
#             block_ports[i][1] -= 1
#         elif block_ports[i][1] == 0:
#             block_ports[i][0] = 0

def find_numbering_anomalies(data, wrap_at=18, idx=1):
    """
    Detects discontinuities in a sequence of numbers that should form
    contiguous cycles starting with 0.

    Rules
    -----
    • Every cycle starts with 0.
    • After a 0, values must increase by +1 each step (0 → 1 → 2 → …).
    • Encountering another 0 (at any point) begins a new cycle immediately.
    • Values are limited to the range 0 … wrap_at (inclusive).  If a value
      reaches wrap_at, the ONLY valid next value is 0.

    Parameters
    ----------
    data     : list-like of sequences (e.g., list of tuples or lists)
               The element at position `idx` in each inner sequence is checked.
    wrap_at  : int  (default 18)
               Maximum value in a cycle before it must wrap to 0.
    idx      : int  (default 1)
               Index of the field inside each inner sequence that holds
               the counter you want to validate.

    Returns
    -------
    List[dict]  — each dict describes one anomaly:
      {
         'at_position': int,    # index of the bad element in `data`
         'found'      : int,    # value that was actually seen
         'expected'   : int,    # value that should have appeared
         'prev_value' : int     # previous value in the stream
      }
    """
    anomalies = []
    if not data:
        return anomalies

    expected =  data[0][1]       # the very first element must be 0
    prev_val = None

    for pos, item in enumerate(data):
        val = item[idx]

        # Correct value?
        if val == expected:
            prev_val = val
            expected = val+1
            continue

        # Early restart with 0 is allowed — just resynchronise
        elif val == 0:
            prev_val = val
            expected = 1
            continue

        # Anything else is an anomaly
        else:
            print(val)
            print(expected)
            print(prev_val)
            anomalies.append({
                'at_position': pos,
                'found'      : val,
                'expected'   : expected,
                'prev_value' : prev_val
            })

        # Resynchronise from this unexpected value
            prev_val = val
            expected = (val + 1)

    return anomalies


packet_served = 0
packet_dropped = 0
total_packets = 0
packet_saved = 0

def decide_and_bitmap(d_port,cell_len,s_port,cell_count):
    #This function will decide whether the packet that has reached now has to be dropped or not
    # total packets should record pckeats that are dropped at this point as well as the packet sthat enter the pipeline
    global gate
    global free_blocks
    global q
    global voq_len
    global packet_dropped
    global packet_served
    global total_packets
    global packet_saved
    

    #find the longest q for the run

    # the gate variable checks whether to admit packets after a rejection to longest queue
    # request for a longest q removal comes at this point
    # the removable variable keeps track of whether or not to remove the last set of packets... the packets need to be removed only when all packets of that clock cycle have been processed

    packet_saved = 0
    # count_q = sum(
    # 1
    # for outer in q
    # for middle in outer
    # for inner in middle
    # if inner[1] == 0)
    # if packet_dropped + packet_served + count_q != total_packets:
    #     print(packet_dropped)
    #     print(packet_served)
    #     print(count_q)
    #     print(total_packets)
    #     fdf
    # else:
    #     print("u fine bruh")
        
    for c in range(N):
        for j in range(N):
            anoms = find_numbering_anomalies(q[c][j], wrap_at=18, idx=1)

            if not anoms:
                continue
            else:
                print(q[c][j])
                print(f"🚨 Numbering anomalies detected: {c}:{j}")
                for a in anoms:
                    print(f" • At element #{a['at_position']}: "
                        f"saw {a['found']} (prev was {a['prev_value']}), "
                        f"expected {a['expected']}")
                asa

    total_cells_requested = 0
    #port_block()
    for i in range(N):
        
        
        block_c = 0
        for c in range(N):
            for h in range(N):
                block_c += len(q[c][h])
        if TOTAL_MEMORY!=block_c+free_blocks:
            print(TOTAL_MEMORY,block_c+free_blocks)
            fdf
        n = len(q)
# generate all (i,j) pairs, then pick the one whose q[i][j] has the greatest len()
        
        #print(f"Longest sublist is q[{longest[0]}][{longest[1]}] with length {len(q[longest[0]][longest[1]])}")

        #checking for packet to place
        if d_port[i]!=-1 :
            if cell_len[i] == 0:
                total_packets+=1
        
            #place the current packet only if packets early on have been placed or if a new packet has come
            if gate[d_port[i]][i] == 1 or cell_len[i] == 0:
            
                #if there are free blocks then place packets
                if free_blocks!=0:
                    cell_add = memory_manager.malloc()
                    if cell_add== None:
                        print(free_blocks)
                        dsd
                    q[d_port[i]][i].append([cell_add,cell_len[i],s_port[i],cell_count[i]])

                    #print(f"i have placed a cell {[cell_add,cell_len[i],s_port[i],cell_count[i]]}")
                    voq_len[d_port[i]][i] += 1
                    gate[d_port[i]][i] = 1
                    free_blocks-=1
                # if u do not have free blocks, then we have to remove some packets from the longest queue
                else:
                    longest = max(
                    ((i, j) for i in range(n) for j in range(n)),
                    key=lambda ij: len(q[ij[0]][ij[1]])
                    )
                    # if packets are to the longest queue just drop them
                    if longest[0] == d_port[i] and longest[1] == i:
                        gate[d_port[i]][i] = 0
                        if cell_len[i] != 0:
                            for c in range(0,cell_len[i]):
                                # print(q[longest[0]][longest[1]][-(c+1)][0])
                                # print(cell_len[i])
                                # print(q[longest[0]][longest[1]])
                                memory_manager.deallocate(q[longest[0]][longest[1]][-(c+1)][0])
                                
                            del q[longest[0]][longest[1]][-cell_len[i]:]
                            voq_len[d_port[i]][i] -=  cell_len[i]
                            free_blocks += cell_len[i]
                            packet_dropped +=1
                            #print("I have removed some packets to the longest queue")
                        else:
                            packet_dropped +=1
                            continue
                    # if they are not to the longest queue then just send them to their best place
                    else:
                        q[d_port[i]][i].append([q[longest[0]][longest[1]][-1][0],cell_len[i],s_port[i],cell_count[i]])
                        gate[longest[0]][longest[1]] = 0
                        
                        total_cells_requested +=1
                        voq_len[d_port[i]][i] += 1
                        # print("I am trying to make space for the new packet from the longest queue")
                        # print(q[longest[0]][longest[1]])
                        # print(q[longest[0]][longest[1]][-1][1]+1)
                        gate[d_port[i]][i] = 1
                        voq_len[longest[0]][longest[1]] -=  q[longest[0]][longest[1]][-1][1]+1
                        free_blocks += q[longest[0]][longest[1]][-1][1]
                        for c in range(1,q[longest[0]][longest[1]][-1][1]+1):
                            memory_manager.deallocate(q[longest[0]][longest[1]][-(c+1)][0])
                        del q[longest[0]][longest[1]][-(q[longest[0]][longest[1]][-1][1]+1):]
                        packet_dropped +=1
                        # print(free_blocks)
                        # print(free_blocks)
                        # print(q[longest[0]][longest[1]])
                        #print(f"i remove {q[longest[0]][longest[1]][-1][1]} and give one l")
    #print("This is the anomaly")
    # print(q[1][4])
    # print(gate[1][4])
    
reading = [-1]*N
count = [-1]*N
stall_s = [0.0]*N
track_s = [0]*N
p_y = [[0 for i in range(N)] for _ in range(N)]
rr = [0]*N
bytes_sent = [0]*N


def pad_to_cell(bytes_, cell_size):
    return ((bytes_ + cell_size - 1) // cell_size) * cell_size



pending_head = [[0 for _ in range(N)] for _ in range(N)]
def deallocate():
    global free_blocks
    global q
    global voq_len
    global rr
    global packet_served
    global packet_dropped
    global bytes_sent
    global pending_head
    global stall_s
    global track_s
    global p_y
    global count
    global reading

    # ------------------------------------------------------------
    # Deallocator behavior:
    #   - obey stall_s / track_s
    #   - one cell max per output per clock cycle
    #   - RR among active VOQs
    #   - remove cell no matter whether packet is corrupt
    #   - count served only for valid seq 0 -> seq 1
    #   - count dropped only when seq 0 is followed by another seq 0
    # ------------------------------------------------------------

    for d in range(N):

        # If output d is still busy, do not drain this cycle.
        if stall_s[d] > track_s[d]:
            track_s[d] += 1
            continue

        # Pick next active VOQ using RR.
        chosen_i = -1

        for off in range(N):
            cand = (rr[d] + off) % N
            if q[d][cand]:
                chosen_i = cand
                break

        # No active VOQ for this output.
        if chosen_i == -1:
            stall_s[d] = 0
            track_s[d] = 0
            count[d] = -1
            reading[d] = -1

            for i in range(N):
                voq_len[d][i] = len(q[d][i])
                p_y[d][i] = 0

            continue

        i = chosen_i

        # Remove exactly one cell.
        cell = q[d][i].pop(0)

        addr = cell[0]
        seq = cell[1]
        size_bytes = cell[2]

        memory_manager.deallocate(addr)
        free_blocks += 1

        bytes_sent[d] += size_bytes

        # Update queue bookkeeping.
        voq_len[d][i] = len(q[d][i])

        # --------------------------------------------------------
        # Packet accounting.
        #
        # Valid:
        #   0 then 1 from same q[d][i] => served
        #
        # Corrupt:
        #   0 then 0 from same q[d][i] => previous packet dropped
        #   1 with no pending 0 => orphan tail, not served
        # --------------------------------------------------------
        if seq == 0:
            if pending_head[d][i] == 1:
                # Previous head was never followed by seq 1.
                packet_dropped += 1

            pending_head[d][i] = 1

        elif seq == 1:
            if pending_head[d][i] == 1:
                packet_served += 1
                pending_head[d][i] = 0
            else:
                # Tail without head. Remove it but do not count served.
                pass

        else:
            # Unexpected sequence for your current 2-cell workload.
            if pending_head[d][i] == 1:
                packet_dropped += 1
                pending_head[d][i] = 0

        # Preserve stall/track timing.
        stall_s[d] = size_bytes * 8 / (link_speed * time_period)
        track_s[d] = 1

        # Old state variables kept sane.
        reading[d] = seq
        count[d] = 2

        # Advance RR.
        rr[d] = (i + 1) % N

    # Final bookkeeping repair.
    for d in range(N):
        for i in range(N):
            voq_len[d][i] = len(q[d][i])
            p_y[d][i] = 0

        if sum(len(q[d][i]) for i in range(N)) == 0:
            count[d] = -1
            reading[d] = -1
    #print(rr)
                
def LQD(d_port,cell_len,t,s_port,cell_count):
    

########################################### Initialization #############################
    cmpr = []
    out_addr = []
    pair_list = []
    memory_location = []
    for c in range(int(math.log(N,2))):
        cmpr.append([[0,0] for j in range(int(N/2**(c+1)))])
        out_addr.append([0]*int(N/(2**(c+1)))) 
    
########################################## Begin process ################################

    decide_and_bitmap(d_port,cell_len,s_port,cell_count)
    deallocate()


from pathlib import Path
import csv

def read_csv(burst,incast,round):
    """Read the CSV file and extract data into 2D arrays dest_port and size."""
    csv_file_path = f"output_new_{burst}_{incast}_{round}_{sys.argv[-1]}.csv"
    global n_dest_port
    global n_size
    n_dest_port = []
    n_size = []
    with open(csv_file_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            t, i, dp, sz = map(int, row)
            if len(n_dest_port) <= i:
                n_dest_port.append([])
                n_size.append([])
            n_dest_port[i].append(dp)
            n_size[i].append(sz)
    return n_size, n_dest_port

import os

def log_q_sums(q, t=None, path="./q_log/q_sums.csv", include_time=True, reset=False):
    """
    Append one CSV row to ./q_log/q_sums.csv with one column per i:
        row = [t?, sum_j len(q[i][j]) for i in 0..N-1]
    - q: NxN list where q[i][j] is an iterable (len() defined)
    - t: optional timestep to log as the first column
    - path/include_time: customize output
    - reset=True: recreate the file with a fresh header on this call
    """
    import os, csv
    N = len(q)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    # Create/refresh header if file missing or reset requested
    need_header = reset or not os.path.exists(path)
    if need_header:
        with open(path, "w", newline="") as f:
            header = (["t"] if include_time else []) + [f"i{i}" for i in range(N)]
            csv.writer(f).writerow(header)

    # Compute row: sum_j len(q[i][j]) for each i
    row = ([t] if (include_time and t is not None) else []) + [
        sum(len(q[i][j]) for j in range(N)) for i in range(N)
    ]

    # Append
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)


free_blocks = int(TOTAL_MEMORY)
link_speed = 4*10**11 #100 Gbps
time_period = 1*(10**-9) #10ns
data = [[] for _ in range(N)]

def main(burst,incast,round):
    global N
    global c
    global t
    global cell_size
    # Initialize dataset
    global packet_served
    global dest_port
    global size
    global free_blocks
    global link_speed
    global time_period
    flag = 0
    # Generating data that comes in through 5 port ingress_port[T][N]
    #print("reading csv")
    size,dest_port = read_csv(burst,incast,round)
    size_e = copy.deepcopy(size)
    dest_port
    stall = [-1]*N
    v = 0
    v_i = [0]*N
    phase_2 = 0
    track = [1 for _ in range(N)]
    d_port = [-1]*N
    s_port = [-1]*N
    cell_len = [-1]*N
    cell_count = [0]*N
    
    t = 0
    while True:
        t+=1
        log_q_sums(q,t,path = f"./q_log/q_sums_{burst}_{incast}_{round}_lqd.csv")
        #print(f"time = {t}")
        #print(bytes_sent)
        # print(f"\nTime Slot {t}")
        # print(v[0])
        # print(f"free_blocks = {free_blocks}")
        ray_of_death = 0
        for i in range(0,N):
            # for phase 1
            if dest_port[0][v] != 0 and not phase_2:
                v_i = [v]*N
                phase_2 = 1
            if not phase_2:
                if track[i] > stall[i] and v<len(size[i])-1:
                    track[i] = 1
                    d_port[i] = dest_port[i][v]
                    if dest_port[i][v] != -1:
                        ray_of_death = 1

                    if cell_len[i] == -1: # changing packet size to a multiple of cell size
                        size[i][v] = pad_to_cell(size[i][v], cell_size)
                        s_port[i] = min(size_e[i][v],cell_size)
                        if s_port[i]<-1:
                            s_port[i] = -1
                            d_port[i] = -1
                        cell_count[i] = math.ceil(size[i][v]/cell_size)
                        # print("#################33")
                        # dfd
                    else:
                        s_port[i] = min(size_e[i][v],cell_size)
                        if s_port[i]<-1:
                            s_port[i] = -1
                            d_port[i] = -1
                        cell_count[i] = 0
                    stall[i] = min(cell_size*8/(link_speed*time_period),size[i][v]*8/(link_speed*time_period))
                    size[i][v] = size[i][v]-cell_size
                    size_e[i][v] = size_e[i][v]-cell_size
                    cell_len[i] +=1
                elif dest_port[i][v]!=-1 and len(dest_port[i]) != v+1:
                    ray_of_death = 1
                    track[i]+=1
                    d_port[i]=-1
                    s_port[i]=0
        
        # for phase 2
            else:
                if track[i] > stall[i] and v_i[i]<len(size[i])-1:
                    track[i] = 1
                    d_port[i] = dest_port[i][v_i[i]]
                    if dest_port[i][v_i[i]] != -1:
                        ray_of_death = 1

                    if cell_len[i] == -1: # changing packet size to a multiple of cell size
                        size[i][v_i[i]] = pad_to_cell(size[i][v_i[i]], cell_size)
                        s_port[i] = min(size_e[i][v_i[i]],cell_size)
                        if s_port[i]<-1:
                            s_port[i] = -1
                            d_port[i] = -1
                        cell_count[i] = math.ceil(size[i][v_i[i]]/cell_size)
                        # print("#################33")
                        # dfd
                    else:
                        s_port[i] = min(size_e[i][v_i[i]],cell_size)
                        if s_port[i]<-1:
                            s_port[i] = -1
                            d_port[i] = -1
                        cell_count[i] = 0
                    stall[i] = min(cell_size*8/(link_speed*time_period),size[i][v_i[i]]*8/(link_speed*time_period))
                    size[i][v_i[i]] = size[i][v_i[i]]-cell_size
                    size_e[i][v_i[i]] = size_e[i][v_i[i]]-cell_size
                    cell_len[i] +=1
                elif dest_port[i][v_i[i]]!=-1 and len(dest_port[i]) != v_i[i]+1:
                    ray_of_death = 1
                    track[i]+=1
                    d_port[i]=-1
                    s_port[i]=0
            
        if any(s_port[i] < -1 for i in range(N)) == 1:
            breakpoint()
        r = LQD(d_port,cell_len,t,s_port,cell_count)
        if not phase_2:
            for i in range(0,N):
                if size[i][v] <= 0:
                    cell_len[i] = -1
            if all(size[i][v] <= 0 for i in range(N)):
                if len(dest_port[i])-1 > v:    
                    v += 1

        # for phase two
        else:
            for i in range(0,N):
                if size[i][v_i[i]] <= 0:
                    cell_len[i] = -1
                    if len(dest_port[i])-1 > v_i[i]:    
                        v_i[i] += 1

        d_port = [-1]*N
        s_port = [-1]*N
        sum = 0
        for e in q:
            for o in e:
                sum += len(o)
        
        if ray_of_death == 0:
            break

    while True:
        gg = 0
        t += 1

        # log during final drain too
        log_q_sums(q, t, path=f"./q_log/q_sums_{burst}_{incast}_{round}_lqd.csv")

        for c in range(N):
            for h in range(N):
                if len(q[c][h]) > 0:
                    deallocate()
                    gg = 1
                    break
            if gg == 1:
                break

        if gg == 0:
            # log one final row at simulation end
            log_q_sums(q, t, path=f"./q_log/q_sums_{burst}_{incast}_{round}_lqd.csv")
            break
    
    # for c in range(4):
    #     for j in range(4):
    #         print("**************************************")
    #         print("**************************************")
    #         print(f"q for {c},{4*c+j} - {q[c][4*c+j]}")
    return t

import sys
 # Save the original stdout (standard output) \
def run(i):
    original_stdout = sys.stdout         
    with open(fr'/home/dan/LQD/LQD/master/optimal_logs/output_optimal_{i}.txt', 'w') as file: # Redirect stdout to the file 
        sys.stdout = file
        t = main(i)
        print(f"dropped packets = {packet_dropped}")
        print("n**2_q algo")
        print(f"packets served = {packet_served}")
        print(f"{sum(bytes_sent)*8*(10**-9)/(t*time_period)} gbps per port")
        sys.stdout = original_stdout
    print("Entered text in file")
# index = int(input("what index do u want to run at ?"))
# main(index)
# save_obm_outputs(data, Path("/home/dan/LQD/OBM"))
#main(1)
#print(packet_served)
#print(packet_dropped)
import sys
time = main(int(sys.argv[1]),sys.argv[2],int(sys.argv[3]))
print(f"dropped packets = {packet_dropped}")
print(f"time = {time}")
print("LQD")
print(f"packets served = {packet_served}")
print(f"{sum(bytes_sent)*8*(10**-9)/(time*time_period)} gbps per port")
print(f"{sum(bytes_sent)*8*(10**-9)/(time_period)} divide this value by max time")