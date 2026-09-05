# T = runtime 
import csv
import random
import copy
import pandas as pd
import sys

# Constants

N = 8  # Example: number of input/output ports
MAX_PACKET_SIZE = 1500
T = 2000  # Total time slots
# Arrival and departure details for packets
dept_time = [[0] * 3000 for _ in range(N)]
size = [[0] * 3000 for _ in range(N)]
dest_port = [[0] * 3000 for _ in range(N)]

# Virtual output queues
# vq[o][i] is a VOQ for output port `o` and input mapped to `i`
q = [[[] for _ in range(N)] for _ in range(N)]
cell_size = 80
# Tracker for last packet with each tag (<input_port, output_port>)
# Tracks (mapped_input, index_in_vq)


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

TOTAL_MEMORY = 26214 #+ 304
memory_manager = MemoryPool(TOTAL_MEMORY,cell_size)
# Constants

def read_csv(burst,incast,round):
    """Read the CSV file and extract data into 2D arrays dest_port and size."""
    csv_file_path = f"output_new_{burst}_{incast}_{round}.csv"
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

from pathlib import Path
import numpy as np
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

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
    BASE_DIR = Path("master/abm_logs") 
    # ----- build file paths --------------------------------------------------
    csv_path = BASE_DIR / f"output_abm_{i}.csv"
    png_path = BASE_DIR / f"output_abm_{i}.png"

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


packet_admission_status = [False] * N  # Persists decision for duration of packet
#################################################################cleared################################################
def bit_mapper(d_port,cell_len,s_port,cell_count):
    global final_add
    global trk
    global free_blocks
    global dropped_packet
    global nppq
    global total_packets
    global packet_admission_status
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
        
        # Skip inactive ports
        if d_port[i] == -1:
            lqd_bit[i] = 1 
            final_add[0][i] = -1
            continue

        # === CASE A: HEAD OF PACKET (Sequence 0) ===
        # We must make a "Whole Packet" decision here.
        if cell_len[i] == 0:
            
            # 1. Check Threshold (ABM Logic)
            queue_len = sum([len(q[d_port[i]][j]) for j in range(N)])
            thresh_ok = queue_len < tresh[d_port[i]]
            
            # 2. Check Whole Packet Space
            # cell_count[i] holds the total cells needed for this packet
            needed_space = 38*N
            space_ok = free_blocks >= needed_space

            if thresh_ok and space_ok:
                # ACCEPT
                packet_admission_status[i] = True
                
                lqd_bit[i] = 1
                final_add[0][i] = memory_manager.malloc()
                
                # Update counters
                free_blocks -= 1              # Actual deduction for HEAD
                
            else:
                # REJECT
                packet_admission_status[i] = False
                lqd_bit[i] = 1 
                final_add[0][i] = -1

        # === CASE B: BODY OF PACKET (Sequence > 0) ===
        # We simply follow the decision made at the Head.
        else:
            if packet_admission_status[i] and free_blocks > 0:
                lqd_bit[i] = 1
                final_add[0][i] = memory_manager.malloc()
                free_blocks -= 1
                # No need to touch virtual_free_blocks here; space was reserved by Head.
            else:
                lqd_bit[i] = 1
                final_add[0][i] = -1

    lqd_bit_map = lqd_bit
    return lqd_bit_map
    #print(lqd_bit)
cunt = 0
voq_len = [[0 for c in range(N)] for d in range(N)]
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
    #print(f"r = {r}")
    
    #print(voq_len)
    #numbering anomaly inside q check
    
        
    for c in range(N):
        for j in range(N):
            anoms = find_numbering_anomalies(q[c][j], wrap_at=18, idx=1)

            if not anoms:
                continue
            else:
                #print(q[c][j])
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
                #print(f"packet = {buffer[-1][i]} allocated")
                last_q[i] = [buffer[-1][i][1],1]
            
            # removing a packet when there is no actual packet
            else:
                memory_manager.deallocate(final_add[-1][i])
                #print(f"preventing packet allocation = {i} - {buffer[-1][i]}")
                free_blocks+=1
                print("This is not allowed")
                breakpoint()
                if buffer[-1][i][1] == 0:
                    packet_dropped+=1
        
        # recording packet drops when there is no location available
        elif 0 == buffer[-1][i][1] and  last_q[i][1] == 0:
            packet_dropped+=1


        # what to do when we have no cells left for a packet
        if buffer[-1][i][0]!=-1 and last_q[i][1] == 1 and final_add[-1][i]==-1:
            last_q[i][1] = 0
            #print(buffer[-1][i][1])
            #print(f"q before:{q[buffer[-1][i][0]][i]}")
            if buffer[-1][i][1] == 0:
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
                        packet_dropped += 1
                    print("This is not allowed")
                    breakpoint()
                    free_blocks+=1
        
    shift_list_in_place(buffer)

            #dedw
fl = 0
dropped_packet = 0
prev_drop_packet = 0


def active_calc(alpha):
    # what i need?
    # number of queues with 90% thresh
    # number of active queues in i
        # what i need?
    # number of queues with 90% thresh
    # number of active queues in i
    np = 0
    global free_blocks
    global tresh

    #print(f"tresh - {[tresh[n1][0] for n1 in range(N)]}")
    
    for n1,i in enumerate(q):
        if sum([len(q[n1][n2]) for n2 in range(N)]) > 0.9*tresh[n1]:
            np+=1    
    if np == 0:
        np = 1
    for n1,i in enumerate(q):
        tresh[n1] = alpha*(free_blocks)*(1/np)
    
    #print(tresh[0][0])
    # print(al)


B = int(TOTAL_MEMORY)
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
                        # if d == 5:
                        #     print(f"reducing {d} {l} when we restart flow")
                        #     breakpoint()
                        voq_len[d][l] -= q[d][l][0][3] #changing voq_len
                        
                        p_y[d][l] = 1
                        if count[d] == -1:
                            count[d] = 0
                            rr[d] = l
                    else:
                        p_y[d][l] = 0

        #count[d] keeps track of the number of cells for each packet in q
        # if count[d]==-1 then that means there are no packets to be sent in that queue       
        if (stall_s[d]<=track_s[d] and count[d]!=-1) or count[d] == 0:
            # print(f"reading = {reading[d]}")
            if reading[d]!=-1:
                # print(f"popping {d} , {rr[d]}")
                #print(voq_len)
                send = q[d][rr[d]].pop(0)
                bytes_sent[d] += send[2]
                memory_manager.deallocate(send[0])
                #print(f"i am sending the packet {send}")
                if send[1] == 0:
                    packet_served+=1
                free_blocks+=1
                # if count[d] == 1:
                #     if q[d][rr[d]]:
                #         if voq_len[d][rr[d]] >= q[d][rr[d]][0][3]: 
                #             voq_len[d][rr[d]] -= q[d][rr[d]][0][3] #changing voq_len
                #             #print(f"reducing {d} {rr[d]}")

                #             p_y[d][rr[d]] = 1
                #         else:
                #             p_y[d][rr[d]] = 0
                #     else:
                #             p_y[d][rr[d]] = 0


            if reading[d] == count[d]-1 and count[d]!=0:
                # print(f"we are round robining for {d}")
                # print(f"reading = {reading[d]} and count[d] = {count[d]}]")
                for l in range(0,N):
                    if p_y[d][(rr[d]+1+l)%N]!=0:
                        if not q[d][rr[d]] and p_y[d][rr[d]] == 1:
                            p_y[d][rr[d]] = 0
                        rr[d] = (rr[d]+1+l)%N
                        count[d] = q[d][rr[d]][0][3]
                        #print(f"this is the new {rr[d]}")
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
                    # print(voq_len[d][rr[d]])
                    # print(q[d][rr[d]])
                    # print(d,rr[d])
                    if voq_len[d][rr[d]] >= q[d][rr[d]][1][3]: 
                        # if d == 5:
                        #     print(f"reducing {d} {rr[d]}")
                        #     breakpoint()
                        voq_len[d][rr[d]] -= q[d][rr[d]][1][3] #changing voq_len
                        

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
            if voq_len[n1][n2] > len(q[n1][n2]):
                print(n1,n2)
                fdf
    
    active_ports.append(sum(active_port))


def pad_to_cell(bytes_, cell_size):
    return ((bytes_ + cell_size - 1) // cell_size) * cell_size


import math

trk = lag
free_blocks = int(TOTAL_MEMORY)
link_speed = 4*10**11 #100 Gbps
time_period = 1*(10**-9) #10ns

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

def main(burst,incast,round,alpha):
    global N
    global T
    global M
    global K
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
    print(alpha)
    size,dest_port = read_csv(burst,incast,round)
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
    #print(f"dep_t = {[dep_t[i][0] for i in range(N)] }")   
    # for i in range(len(dep_t)):
    #     for j in range(len(dep_t[i])):
    #         if dep_t[i][j] != -1:
    #             size[i][j] = 1500#random.randint(64,MAX_PACKET_SIZE)

    t = 0
    while True:
        t+=1
        log_q_sums(q,t,path = f"./q_log/q_sums_{burst}_{incast}_{round}_{alpha}_abm.csv")
        #print(bytes_sent)
        # print(f"\nTime Slot {t}")
        
        # print(f"free blocks = {free_blocks}")
        # for c in range(N):
        #     for f in range(N):
        #         print(len(q[c][f]), end=' ')
        #     print("")
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
        r = LQD(d_port,cell_len,t,s_port,cell_count,alpha)
        deallocate()
        #print(s_port)
        # for phase one
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
        if ray_of_death == 0:
            break

    while True:
        gg = 0
        t+=1
        log_q_sums(q,t,path = f"./q_log/q_sums_{burst}_{incast}_{round}_{alpha}_abm.csv")
        for c in range(N):
            for h in range(N):
                if len(q[c][h])>=19:
                    deallocate()

                    # print(q[c][h])
                    # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                    gg = 1
                    # print(packet_served)
                    # print(packet_dropped)
                    # print(total_packets)
                    break
        if gg ==0:
            break
    
        #deallocate(t)
    #print(q)
    #print(free_blocks)
    return t
            
        


import sys
 # Save the original stdout (standard output) \
def run(i):
    original_stdout = sys.stdout 
    # Open a file named 'output.txt' in write mode 
    with open(fr'/home/dan/LQD/LQD/master/abm_logs/output_abm_{i}.txt', 'w') as file: # Redirect stdout to the file 
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

#run(0)
# main(0)
# for c in range(4):
#         for j in range(4):
#             print("**************************************")
#             print("**************************************")
#             print(f"q for {c},{4*c+j} - {q[c][4*c+j]}")


time = main(int(sys.argv[1]),sys.argv[2],int(sys.argv[3]),float(sys.argv[4]))
print(f"dropped_packet = {packet_dropped}")
print(f"Over in time = {time}")
print(f"packets served = {packet_served}")
print("ABM algo") # Print statements (these will go to the file instead of the terminal) print("Hello, world!") print("This output will be written to the text file.") # Restore original stdout 
print(f"{sum(bytes_sent)*8*(10**-9)/(time*time_period)} gbps per port")
print(f"{sum(bytes_sent)*8*(10**-9)/(time_period)} divide this value by max time")