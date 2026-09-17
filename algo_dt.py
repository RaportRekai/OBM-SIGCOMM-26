# T = runtime 
import csv
import random
import copy
import pandas as pd
import sys


ALG_TAG = "dt"          #  "abm", "dt", "lqd", …

# Constants
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import get_cmap

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

#index = int(input("what workload are u running the experiment for ?"))


BASE_DIR   = Path(".")
CSV_DIR    = BASE_DIR / ALG_TAG / f"csv_{2}"
PNG_DIR    = BASE_DIR / ALG_TAG / f"png_{2}"
LOG_DIR    = BASE_DIR / ALG_TAG / f"logs_{2}"

for d in (CSV_DIR, PNG_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

N = 16  # Example: number of input/output ports
MAX_PACKET_SIZE = 1500
T = 2000  # Total time slots
# Arrival and departure details for packets
dept_time = [[0] * 2000 for _ in range(N)]
size = [[0] * 2000 for _ in range(N)]
dest_port = [[0] * 2000 for _ in range(N)]
data     = [[] for _ in range(N)]         # one list per queue
t_series = [[] for _ in range(N)]         # one list per queue
# Virtual output queues
# vq[o][i] is a VOQ for output port `o` and input mapped to `i`
q = [[[] for _ in range(N)] for _ in range(N)]
cell_size = 80
# Tracker for last packet with each tag (<input_port, output_port>)
# Tracks (mapped_input, index_in_vq)
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import get_cmap

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def plot_queues_to_png(solid, dotted, out_dir: Path,
                       clip_edges: bool = True, dpi: int = 300) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    solid  = np.asarray(solid)
    dotted = np.asarray(dotted)

    # Optionally trim the first/last 100 samples to hide warm-up/transients
    if clip_edges:
        solid  = solid[:, 100:-100]
        dotted = dotted[:, 100:-100]
        t_axis = np.arange(solid.shape[1]) + 100
    else:
        t_axis = np.arange(solid.shape[1])

    # ---------- 1. Per-queue figures (unchanged) ----------
    for q in range(16):
        plt.figure(figsize=(12, 4))
        plt.plot(t_axis, solid[q],  lw=1.5, label="Queue")
        plt.plot(t_axis, dotted[q], lw=1.5, ls=":", label="Reference")
        plt.title(f"Queue {q} Occupancy vs Time")
        plt.xlabel("Timestep")
        plt.ylabel("Occupancy")
        plt.legend()
        plt.grid(alpha=.3)
        plt.tight_layout()
        plt.savefig(out_dir / f"queue_{q:02d}.png", dpi=dpi)
        plt.close()

    # ---------- 2. All-queues-in-one figure ----------
    plt.figure(figsize=(14, 6))

    # Pick 16 visually distinct colors from a qualitative colormap
    cmap   = plt.get_cmap("tab20")        # 20 discrete hues
    colors = [cmap(i) for i in range(0, 32, 2)]  # grab 0,2,4,…,30 → 16 colors

    for q in range(16):
        plt.plot(t_axis, solid[q],
                 lw=1.4,
                 color=colors[q],
                 label=f"Q{q:02d}")

    plt.title("All 16 Queues – Occupancy vs Time")
    plt.xlabel("Timestep")
    plt.ylabel("Occupancy")
    plt.legend(ncol=4, fontsize=8, framealpha=.8)   # compact legend
    plt.grid(alpha=.3)
    plt.tight_layout()
    plt.savefig(out_dir / "all_queues.png", dpi=dpi)
    plt.close()

"""
export_csv.py  ──  save_sim_outputs()
-------------------------------------------------------
Write solid_matrix (data) and dotted_matrix (reference) to CSVs that
are human-readable: one column per queue with a header row.

Call once, *after* your simulation finishes – e.g.:

    save_sim_outputs(data, t_series)
"""
from pathlib import Path
import numpy as np
import pandas as pd


def _save_matrix(path: Path, mat: np.ndarray) -> None:
    mat = np.asarray(mat)
    assert mat.shape[0] == 16
    df = pd.DataFrame(mat.T, columns=[f"queue_{i}" for i in range(16)])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"✔︎ wrote {path}  [{df.shape[0]} rows × {df.shape[1]} cols]")

def save_sim_outputs(solid, dotted, out_dir: Path) -> None:
    _save_matrix(out_dir / "solid_matrix.csv",  solid)
    _save_matrix(out_dir / "dotted_matrix.csv", dotted)

import csv
from pathlib import Path
from typing import Sequence, Union

Number = Union[int, float]

def save_queue_csv(
        values: Sequence[Number],
        csv_name: str,
        out_dir: Union[str, Path] = "/home/dan/outputs"
) -> Path:
    """
    Save a 1-D sequence of numbers to /home/dan/outputs/<csv_name>.

    CSV format:
        queue
        0.0
        0.0
        …

    Parameters
    ----------
    values   : list/tuple/np.ndarray of numbers
    csv_name : file name to use for the CSV (must include .csv)
    out_dir  : target directory (default: /home/dan/outputs)

    Returns
    -------
    pathlib.Path pointing to the written file.
    """
    # Ensure directory exists
    out_dir = Path(out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / csv_name

    # Write header + one value per line
    with out_path.open(mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["queue"])          # header
        for v in values:
            writer.writerow([float(v)])    # one item per row, cast to float

    return out_path




def calculate_1500_byte_packets(free_blocks):
    """
    Calculate the number of 1500-byte packets that can be allocated from the free_blocks list.
    :param free_blocks: List of free memory blocks [(start_address, block_size)].
    :return: Number of 1500-byte packets that can be allocated.
    """
    packet_size = 1500
    total_packets = 0

    for _, block_size in free_blocks:
        # Calculate the number of 1500-byte packets that can fit in this block
        total_packets += block_size // packet_size

    return total_packets

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
    
"""             USE CASE
# Define the memory manager with a total memory size of 20 MB
TOTAL_MEMORY = 20 * 1024 * 1024
memory_manager = MemoryManager(TOTAL_MEMORY)

# Example usage:
chunk_size = 1500
address = memory_manager.malloc(chunk_size)
if address is not None:
    print(f"Memory allocated at address {address} with size {chunk_size} bytes.")

    # Write data to the allocated memory
    data = [1] * chunk_size  # Example data
    if memory_manager.write_to_memory(address, data):
        print("Data written successfully.")

    # Read and free the allocated memory
    read_data = memory_manager.read_and_free(address)
    if read_data:
        print(f"Data read {data} successfully and memory freed.")

"""

TOTAL_MEMORY = 26214 + 304
memory_manager = MemoryPool(TOTAL_MEMORY,cell_size)
# Constants



def read_csv(oo):
    """Read the CSV file and extract data into 2D arrays dest_port and size."""
    csv_file_path = f"output_new_{oo}.csv"
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


# def read_from_csv(oo):
#     """Reads a CSV file into two 2D lists dep_t and dest_port."""
#     depr_t, destr_port = [], []
#     filename=f"output_new_{oo}.csv"
#     with open(filename, mode='r') as file:
#         reader = csv.reader(file)
#         current_array = depr_t  # Start with dep_t

#         for row in reader:
#             if not row:  # Blank row indicates switch to dest_port
#                 current_array = destr_port
#             else:
#                 current_array.append([int(value) for value in row])

#     return depr_t, destr_port



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





def reverse_tree(memory_location,split):
    new_split = []
    #print(f"split = {split}")
    #print(f"memory_loaction = {memory_location}")
    for ind,i in enumerate(split):
        if memory_location:
            if len(memory_location[ind])>=i[0]:
                new_split.append(memory_location[ind][0:i[0]])
                if len(memory_location[ind])>=i[0]+i[1]:
                    new_split.append(memory_location[ind][i[0]:i[0]+i[1]])
                else:
                    new_split.append(memory_location[ind][i[0]:len(memory_location[ind])])
                    #print(i[0],len(memory_location))
            else:
                new_split.append(memory_location[ind])
                new_split.append([])
            
    return(new_split)
    

lag = 2
trk = lag

def plot_and_save_active_queues( i,
                                *,
                                title="Active Queues Over Time",
                                xlabel="Time step",
                                ylabel="Number of active queues"):
    """
    Plot queue-count time-series, save PNG + CSV.

    Parameters
    ----------
    series : Sequence[int | float]
        Active-queue counts per time step.
    i : int | str
        Run / workload identifier to drop into file names.
    """
    global active_ports
    BASE_DIR = Path("master/dt_logs") 
    # ----- build file paths --------------------------------------------------
    csv_path = BASE_DIR / f"output_dynamic_n_2_{i}.csv"
    png_path = BASE_DIR / f"output_dynamic_n_2_{i}.png"

    # ----- ensure parent directory exists ------------------------------------
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # ----- write CSV ----------------------------------------------------------
    pd.Series(active_ports, name="active_queues").to_csv(csv_path, index_label="time_step")

    # ----- make plot ----------------------------------------------------------
    y = list(active_ports)
    x = range(len(y))

    plt.figure(figsize=(8, 4))
    plt.plot(x, y, linewidth=1.8)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(png_path, bbox_inches="tight")
    plt.close()                       # free resources

    print(f"Saved {csv_path} and {png_path}")
 

def shift_list_in_place(l):
    # If the list is empty or has only one element, no need to shift
    if len(l) <= 1:
        return
    # Perform the in-place shift
    last_element = l.pop()  # Remove the last element
    l.insert(0, last_element)  # Insert it at the beginning


final_add = [[-1 for i in range(N)] for _ in range(lag)]
last = [[[-1,-1,-1] for _ in range(N)] for j in range(N)]
cnt = [[-1 for _ in range(N)] for i in range(N)]
nppq = [[0 for i in range(N)] for _ in range(N)]
#free_blocks

total_packets = 0
packet_dropped = 0
packet_served = 0



#################################################################cleared################################################
def bit_mapper(d_port,cell_len,s_port,cell_count):
    global final_add
    global trk
    global free_blocks
    global dropped_packet
    global nppq
    global total_packets

    lqd_bit = [0]*N
    shift_list_in_place(final_add)






    for i in range(N):
        if d_port[i] != -1:
            buffer[0][i] = [d_port[i],cell_len[i],s_port[i],cell_count[i]]
            if cell_len[i] == 0:
                total_packets+=1
            
            # if cell_count[i]!=0:
            #     total_packets +=1 
        else:
            buffer[0][i] = [-1,-1,-1,-1]

    # check for served dropped and total packets received
    count_q = sum(
    1
    for outer in q
    for middle in outer
    for inner in middle
    if inner[1] == 0)

    
    count_g = 0
    for layer in buffer:
        for cell in layer:
            if cell[1] == 0:
                count_g += 1

    if count_g+count_q+packet_dropped+packet_served != total_packets:
        dfd

    #print(tresh[0][0])
    #print(tresh)
    # for i in range(N):
    #     for j in range(N):
    #         print(f"{i}{j} - {len(q[i][j])}")
    #print(voq_len)
    
    for i in range(N):
        if sum([len(q[d_port[i]][h]) for h in range(N)]) < tresh[d_port[i]] and d_port[i]!=-1 and free_blocks>0:
            lqd_bit[i] = 1
            #print(f"was able to find a new space for packet from port {i} to port {d_port[i]}")
            final_add[0][i] = memory_manager.malloc()
            free_blocks-=1
        elif d_port!=-1:
            lqd_bit[i] = 1
            #print(f"was not able to find a suitable space for packet from port {i}")
            final_add[0][i] = -1

         
    #print(f"trk = {trk}")
    lqd_bit_map = lqd_bit
    return lqd_bit_map
    #print(lqd_bit)
cunt = 0
voq_len = [[0 for c in range(N)] for d in range(N)]
p_d = [0]*N
def allct(r,t):
    global q
    global trk
    global cnt
    global last_q
    global p_remove
    global lqd
    global len_lst
    global voq_len
    global free_blocks
    global pre_lq
    global pre_lvoq
    global q_change
    global packet_dropped
    global p_d
    #print(f"r = {r}")
    

    #numbering anomaly inside q check
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
    
    #free block check:
    block_c = 0
    for c in range(lag):
        for h in range(N):
            if final_add[c][h]!=-1:
                block_c+=1
    block_c += free_blocks
    for c in range(N):
        for h in range(N):
            block_c += len(q[c][h])

    if block_c != TOTAL_MEMORY:
        print(block_c)
        heyyyy
    
    for i,k in enumerate(final_add[-1]):
        #print(f"buffer = {buffer[-1][i]} ")  
        #print(f"final add = {final_add[-1][i]}")  
        if final_add[-1][i]!=-1:
            
            #placing a normal packet
            if (0 == buffer[-1][i][1] and  last_q[i][1] == 0) or (last_q[i][1] == 1) :
                q[buffer[-1][i][0]][i].append([final_add[-1][i],buffer[-1][i][1],buffer[-1][i][2],buffer[-1][i][3]])
                voq_len[buffer[-1][i][0]][i] += 1
                #print(f"packet = {buffer[-1][i]} allocated from {i} to {buffer[-1][i][0]}")
                last_q[i] = [buffer[-1][i][1],1]
            
            # removing a packet when there is no actual packet
            else:
                memory_manager.deallocate(final_add[-1][i])
                #print(f"preventing packet allocation = {i} - {buffer[-1][i]}")
                free_blocks+=1
                if buffer[-1][i][1] == 0:
                    p_d[buffer[-1][i][0]] += 1 
                    packet_dropped+=1
        
        # recording packet drops when there is no location available
        elif 0 == buffer[-1][i][1] and  last_q[i][1] == 0:
            p_d[buffer[-1][i][0]] += 1 
            packet_dropped+=1


        # what to do when we have no cells left for a packet
        if buffer[-1][i][0]!=-1 and last_q[i][1] == 1 and final_add[-1][i]==-1:
            last_q[i][1] = 0
            #print(buffer[-1][i][1])
            #print(f"q before:{q[buffer[-1][i][0]][i]}")
            if buffer[-1][i][1] == 0:
                p_d[buffer[-1][i][0]] += 1 
                packet_dropped += 1


            #print(f"removing packet because space was not available")
            else:
                free = copy.deepcopy(q[buffer[-1][i][0]][i][-buffer[-1][i][1]:])
                del q[buffer[-1][i][0]][i][-buffer[-1][i][1]:]
                #print(f"q after:{q[buffer[-1][i][0]][i]}")
                for c in free:
                    #print(f"deallocating - {c}")
                    memory_manager.deallocate(c[0])
                    voq_len[buffer[-1][i][0]][i] -= 1 #changing voq_len
                    #print(f"reducing {buffer[-1][i][0]} {i} when we dont have a location")
                    if c[1] == 0:
                        p_d[buffer[-1][i][0]] += 1 
                        packet_dropped += 1

                    free_blocks+=1
        
    shift_list_in_place(buffer)

            #dedw
fl = 0
dropped_packet = 0
prev_drop_packet = 0
st = 0
counter = 0
def active_calc(alpha):
    # what i need?
    # number of queues with 90% thresh
    # number of active queues in i
    aqm = [0]*N
    global free_blocks
    global tresh
    global t_series
    global data
    global t
    
    npc = 0
    #print([sum([len(q[g][f]) for f in range(N)]) for g in range(N)])
    for g in range(N):
        if sum([len(q[g][f]) for f in range(N)]) > 0*tresh[g]:
            npc += 1

    for n1,i in enumerate(q):
        tresh[n1] = alpha*B/(1+npc*alpha)
    #print(tresh)
        # data[n1].append(occ)
        # t_series[n1].append(p_d[n1])
    #print(f"percent {p_d}")
    
    # print(tresh[0][0])
    # print(len(q[0][0]))
    # print(npc)
    
            

    
    # print(tresh)
    # print(free_blocks)
    # print(memory_manager.free_count())


B = int(TOTAL_MEMORY)
alpha = 8
tresh = [B/N for i in range(N)]





def LQD(d_port,cell_len,t,s_port,cell_count,alpha):
    global buffer
    global prev_lqd_bit_map
    global tresh
    #print(buffer[0])
    lqd_bit_map = bit_mapper(d_port,cell_len,s_port,cell_count)
    active_calc(alpha)           
    #print(np)
    allct(prev_lqd_bit_map,t)
    #print(f"tresh = {tresh}")
    # print(f"time = {t}")
    # print(f"free blocks = {free_blocks}")
    # print(tresh[0][0])
    # print(voq_len[0][0])
    prev_lqd_bit_map = lqd_bit_map

    #print(len(q[0][0]),len(q[1][0]),len(q[2][0]),len(q[3][0]),len(q[4][0]),len(q[5][0]))
    
    

buffer = [[[-1,-1]]*N for _ in range(lag)]   
lag = 2
lqd_bit_map = [0 for i in range(N)]
prev_lqd_bit_map = [0 for i in range(N)]
#print(lqd_bit_map)
last_q = [[0,0] for _ in range(N)]
p_y = [[0 for i in range(N)] for _ in range(N)]
cell_trk = [0]*N
count = [0]*N
rr = [0]*N
stall_s = [0]*N
track_s = [0]*N

import random


pointer = [0]*N
sum_c = 0




stop = [-2]*N
tra = [-1]*N
reading = [-1]*N
count = [-1]*N
stall_s = [0.0]*N
track_s = [0]*N
p_y = [[0 for i in range(N)] for _ in range(N)]
rr = [0]*N
bytes_sent = [0]*N
def pad_to_cell(bytes_, cell_size):
    return ((bytes_ + cell_size - 1) // cell_size) * cell_size

active_ports = []

def deallocate():
    global free_blocks
    global rr
    global stall_s
    global track_s
    global voq_len
    global q
    global p_y
    global packet_served
    global reading
    global count
    global bytes_sent
    global min_pack_sent
    #set stage
    # if the egress port is not serving any packet we should set some variable to be -1
    
    active_port = [0]*N

    for d in range(0,N):
        for l in range(N):
            if len(q[d][l])>0:
                active_port[d] = 1
            if q[d][l]:

                #after a break of flow of packets, this peice of code will find the queues which have packets to sent    
                if (voq_len[d][l] >= q[d][l][0][3] and p_y[d][l] == 0 and q[d][l][0][1] == 0 and (reading[d] != 0 or q[d][l][0][3] != 1)):
                    if voq_len[d][l] >= q[d][l][0][3]:
                        voq_len[d][l] -= q[d][l][0][3] #changing voq_len
                        #print(f"reducing {d} {l} when we restart flow")
                        p_y[d][l] = 1
                        if count[d] == -1:
                            count[d] = 0
                            rr[d] = l
                    else:
                        p_y[d][l] = 0
                
        if (stall_s[d]<=track_s[d] and count[d]!=-1) or count[d] == 0:
            if reading[d]!=-1:
                #print(f"popping {d} , {rr[d]}")
                #print(voq_len)
                send = q[d][rr[d]].pop(0)
                memory_manager.deallocate(send[0])
                #print(f"i am sending the packet {send}")
                bytes_sent[d] += send[2]
                if send[1] == 0:
                    packet_served+=1
                    #print(send)
                    
                free_blocks+=1
                # if count[d] == 1:
                #     if voq_len[d][rr[d]] >= q[d][rr[d]][0][3]: 
                #         voq_len[d][rr[d]] -= q[d][rr[d]][0][3] #changing voq_len
                #         #print(f"reducing {d} {rr[d]}")

                #         p_y[d][rr[d]] = 1
                #     else:
                #         p_y[d][rr[d]] = 0

            if reading[d] == count[d]-1 and count[d]!=0:
                for l in range(0,N):
                    if p_y[d][(rr[d]+1+l)%N]!=0:
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
##########################################changing contents of reading #############################    
            elif count[d] == 0: #this condition caters for the case when there is a break in packet flow and the rr had to find the queue that needs to be served next
                count[d] = q[d][rr[d]][0][3]
                track_s[d] = 1
                stall_s[d] = q[d][rr[d]][0][2]*8/(link_speed*time_period)
                reading[d] = 0
            else:
                reading[d] = q[d][rr[d]][0][1]
                track_s[d] = 1
                stall_s[d] = q[d][rr[d]][0][2]*8/(link_speed*time_period)
                
            
            
######################################### analysing changed content ################################
            if reading[d] == count[d]-1:
                if voq_len[d][rr[d]] > 1:    
                         
                    if voq_len[d][rr[d]] >= q[d][rr[d]][1][3]: 
                        voq_len[d][rr[d]] -= q[d][rr[d]][1][3] #changing voq_len
                        #print(f"reducing {d} {rr[d]}")

                        p_y[d][rr[d]] = 1
                    else:
                        p_y[d][rr[d]] = 0
                else:
                    p_y[d][rr[d]] = 0

        elif stall_s[d]>track_s[d]:
            track_s[d]+=1

#This check pertains to the event where the p_y is set to 1 even for voqs which dont have any packet
    
        for g in range(N):
            if not q[d][g] and p_y[d][g] == 1:
                print(f"the rouge is {d,g}")
                fd

        #     dfd
    for n1 in range(N):
        for n2 in range(N):
            if voq_len[n1][n2] < 0:
                ff

    active_ports.append(sum(active_port))



import math

trk = lag
free_blocks = int(TOTAL_MEMORY)
link_speed = 4*10**11 #100 Gbps
time_period = 1*(10**-9) #10ns
values = []
t = 0
def main(oo,alpha):
    global N
    global T
    global M
    global K
    global t
    # Initialize dataset
    global dropped_packets
    global total_packets
    global stored_packets
    global dest_port
    global dep_t
    global size
    global trk
    global free_blocks
    global link_speed
    global time_period
    flag = 0
    # Generating data that comes in through 5 port ingress_port[T][N]
    size,dest_port = read_csv(oo)
    size_e = copy.deepcopy(size)
    stall = [-1 for _ in range(N)]
    v = [0 for _ in range(N)]
    track = [0 for _ in range(N)]
    d_port = [-1]*N
    s_port = [-1]*N
    cell_len = [-1]*N
    cell_count = [0]*N
    global values
    step = 0
    #print(f"dep_t = {[dep_t[i][0] for i in range(N)] }")   
    # for i in range(len(dep_t)):
    #     for j in range(len(dep_t[i])):
    #         if dep_t[i][j] != -1:
    #             size[i][j] = 1500#random.randint(64,MAX_PACKET_SIZE)

    t = 0
    while True:
        t+=1
        #print(bytes_sent)
        # print(f"\nTime Slot {t}")
        
        # print(f"free blocks = {free_blocks}")
        # for c in range(N):
        #     for f in range(N):
        #         print(len(q[c][f]), end=' ')
        #     print("")
        values.append(packet_dropped)
        ray_of_death = 0
        for i in range(0,N):
            #print(v[i])
            if track[i] > stall[i] and step<len(size[i])-1 and size_e[i][step]>-1:
                track[i] = 1
                d_port[i] = dest_port[i][step]
                if dest_port[i][step] != -1:
                    ray_of_death = 1
                if cell_len[i] == -1 and size[i][step]>0:
                    size[i][step] = pad_to_cell(size[i][step], cell_size)
                    s_port[i] = min(size_e[i][step],cell_size)
                    cell_count[i] = math.ceil(size[i][step]/cell_size)
                    # print("#################33")
                    # dfd
                else:
                    s_port[i] = min(size_e[i][step],cell_size)
                    cell_count[i] = 0
                stall[i] = min(cell_size*8/(link_speed*time_period),size[i][step]*8/(link_speed*time_period))
                size[i][step] = size[i][step]-cell_size
                size_e[i][step] = size_e[i][step]-cell_size
                cell_len[i] +=1
            elif dest_port[i][step]!=-1 and len(dest_port[i]) != step+1:
                #print(ray_of_death)
                #print(dest_port[i][v[i]])
                #print(i,v[i])
                ray_of_death = 1
                track[i]+=1
                d_port[i]=-1
                s_port[i]=0
            
        #print(d_port[0],cell_len[0],s_port[0],cell_count[0])
        #print(d_port[1],cell_len[1],s_port[1],cell_count[1])
        for i in s_port:
            if i<-1:
                #print(cell_len)
                #print(s_port)
                #print(cell_count)
                breakpoint()
        #print(s_port)
        r = LQD(d_port,cell_len,t,s_port,cell_count,alpha)
        deallocate()
        #print(s_port)
        notice = 0
        for i in range(0,N):
            if size[i][step] <= 0:
                cell_len[i] = -1
            else:
                notice = 1
        if notice == 0:
            step+=1
        d_port = [-1]*N
        s_port = [-1]*N
        if ray_of_death == 0:
            print(dest_port[0][step:step+50])
            break

    # while True:
    #     gg = 0
    #     for c in range(N):
    #         for h in range(N):
    #             if len(q[c][h])>=19:
    #                 deallocate()

    #                 # print(q[c][h])
    #                 # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    #                 gg = 1
    #                 # print(packet_served)
    #                 # print(packet_dropped)
    #                 # print(total_packets)
    #                 break
    #     if gg ==0:
    #         break
    
        #deallocate(t)
    #print(q)
    #print(free_blocks)
    return t
            
        


import sys
 # Save the original stdout (standard output) \
def run(i):
    original_stdout = sys.stdout 
    # Open a file named 'output.txt' in write mode 
    with open(fr'master/dt_logs/output_dynamic_n_2_{i}', 'w') as file: # Redirect stdout to the file 
        sys.stdout = file
        t = main(i)
        print(f"dropped_packet = {packet_dropped}")
        print(f"Over in t = {t}")
        print(f"packets served = {packet_served}")
        print("ABM algo") # Print statements (these will go to the file instead of the terminal) print("Hello, world!") print("This output will be written to the text file.") # Restore original stdout 
        print(f"{sum(bytes_sent)*8*(10**-9)/(t*time_period)} gbps per port")
        sys.stdout = original_stdout 
    plot_and_save_active_queues(i)
    print(packet_dropped)
    print(packet_served)
    print(total_packets)
    # print("Output written to output.txt successfully!")
    # print(cunt)



# for c in range(4):
#         for j in range(4):
#             print("**************************************")
#             print("**************************************")
#             print(f"q for {c},{4*c+j} - {q[c][4*c+j]}")
burst = sys.argv[1]
time = main(int(burst),float(sys.argv[2]))
print(f"dropped_packet = {packet_dropped}")
print(f"Over in t = {time}")
print(f"packets served = {packet_served}")
print(f"DT = {alpha} algo") # Print statements (these will go to the file instead of the terminal) print("Hello, world!") print("This output will be written to the text file.") # Restore original stdout 
print(f"{((sum(bytes_sent) * 8 * 1e-9 / (time * time_period)) - (30 if float(sys.argv[2]) == 6 else 40 / (2 * (int(float(sys.argv[2]) / 4) + 1)) if float(sys.argv[2]) <= 6 else 0))} gbps per port")
# save_sim_outputs(data, t_series,CSV_DIR) 
# plot_queues_to_png(data, t_series, PNG_DIR, clip_edges=False)
# csv_path = save_queue_csv(values, "dt_drops.csv")

#main(2)
# print(packet_dropped)
# print(packet_served)
# print(total_packets)

