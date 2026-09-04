# T = runtime 
import csv
import random
import copy
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import math

# Constants

N = 8#16  # Example: number of input/output ports
MAX_PACKET_SIZE = 1500
T = 2000  # Total time slots
# Arrival and departure details for packets
dept_time = [[0] * 2000 for _ in range(N)]
size = [[0] * 2000 for _ in range(N)]
dest_port = [[0] * 2000 for _ in range(N)]
cnt = [[-1 for _ in range(N)] for i in range(N)]
# Virtual output queues
# vq[o][i] is a VOQ for output port `o` and input mapped to `i`
q = [[[] for _ in range(N)] for _ in range(N)]
cell_size = 80
# Tracker for last packet with each tag (<input_port, output_port>)
# Tracks (mapped_input, index_in_vq)

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
import sys
TOTAL_MEMORY = int(sys.argv[-1])  #int(22 * 1024 * 1024/cell_size)
memory_manager = MemoryPool(TOTAL_MEMORY,cell_size)
# Constants

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









def reverse_tree(memory_location,split):
    new_split = []
    for ind,i in enumerate(split):
        if memory_location:
            if len(memory_location[ind])>=i[0]:
                new_split.append(memory_location[ind][0:i[0]])
                if len(memory_location[ind])>=i[0]+i[1]:
                    new_split.append(memory_location[ind][i[0]:i[0]+i[1]])
                else:
                    new_split.append(memory_location[ind][i[0]:len(memory_location[ind])])
            else:
                new_split.append(memory_location[ind])
                new_split.append([])
            
    return(new_split)
    
def compare_non_overlapping_adjacent(lst):
    """
    Compare adjacent elements in a list in non-overlapping pairs
    and return the greatest among the two for each pair.
    Each element in the list is in the format [value, id].

    :param lst: List of elements in the format [value, id].
    :return: List of the greater elements in the format [value, id].
    """
    if len(lst) < 2:
        # If the list has fewer than 2 elements, return it as is
        return lst

    result = []
    for i in range(0, len(lst) - 1, 2):  # Iterate in steps of 2
        # Compare the current element with the next one
        if lst[i][0] >= lst[i + 1][0]:
            result.append(lst[i])
        else:
            result.append(lst[i + 1])

    return result

# Rewriting the fetch function and test example due to state reset

# Updated fetch function with maintenance of empty lists

def adder(input_list):
    """
    Adds consecutive elements of a list and returns:
    1. A list of sums of consecutive pairs.
    2. A list of tuples showing the pairs that were summed.
    
    If the input list has n elements, the output lists will have n/2 elements.
    """
    # Check if the list length is even
    if len(input_list) % 2 != 0:
        raise ValueError("The input list must have an even number of elements.")
    
    # Generate pairs and sums
    pairs = [(input_list[i], input_list[i + 1]) for i in range(0, len(input_list), 2)]
    sums = [a + b for a, b in pairs]
    
    return sums, pairs
lag = 10
trk = lag

pre_out_adder = [[0],[0],[0]]
lqd_counter = 0

# Rewriting the fetch function and test example due to state reset

# Updated fetch function with maintenance of empty lists
def fetch(k,longest_ind,index_of_longest_sublist):
    global remove
    global lqd
    global len_lst
    global voq_len
    global packet_dropped
    global p_remove
    global remove
    global lqd_counter
    # Finding the longest queue based on the sum of innermost elements
    if lqd_counter == 50:
        lqd = 0
    else:
        lqd_counter+=1
    # if free_blocks>120:
    #     lqd = 0
    # print(f"all voq = {voq_len}")
    #print(f"longest queue = {index_of_longest_sublist,longest_ind[1]}")

    longest_queue = q[longest_ind[1]]
    if remove[1]!=-1:
        p_remove = remove

    if voq_len[longest_ind[1]][index_of_longest_sublist]!=0:
        longest_sublist = longest_queue[index_of_longest_sublist]
        
        #case when there is no enough tail cells to drop when the lqd request is up
        if voq_len[longest_ind[1]][index_of_longest_sublist] < k and voq_len[longest_ind[1]][index_of_longest_sublist]!=0:
            
            sen = copy.deepcopy(longest_queue[index_of_longest_sublist][-voq_len[longest_ind[1]][index_of_longest_sublist]:])
            last_q[index_of_longest_sublist][longest_ind[1]][1] = 0
            print(f"because of insufficient removal [{index_of_longest_sublist}]")
            del longest_queue[index_of_longest_sublist][-voq_len[longest_ind[1]][index_of_longest_sublist]:]            
            remove = [0,longest_ind[1],index_of_longest_sublist]
            
            len_lst[longest_ind[1]][0] -= voq_len[longest_ind[1]][index_of_longest_sublist]
            voq_len[longest_ind[1]][index_of_longest_sublist]  = 0
            
            # this checks for the number of packets removed from the tail
            for j in sen:
                if j[1] == 0:
                    packet_dropped += 1  
            
            return sen
        
        #incase there are no packets that can be removed from the longest queue
        elif voq_len[longest_ind[1]][index_of_longest_sublist]==0:
            remove = [0,-1,-1]
            return []


        # If k is not 0, fetch the last k elements and remove them from the sublist
        if k != 0:

            lqd = 1
            lqd_counter = 0
            if k <= voq_len[longest_ind[1]][index_of_longest_sublist]:
                result = copy.deepcopy(longest_sublist[-k:])
                last_q[index_of_longest_sublist][longest_ind[1]][1] = 0
                #print(f"because of sufficient removal [{index_of_longest_sublist}]")
                del longest_sublist[-k:]  
                
                
                for j in result:
                    if j[1] == 0:
                        packet_dropped += 1 

                len_lst[longest_ind[1]][0] -= k
                voq_len[longest_ind[1]][index_of_longest_sublist] -= k 
                
            # If the sublist becomes empty, maintain an empty list
            
                if not longest_sublist:
                    longest_queue[longest_queue.index(longest_sublist)] = []
                    remove = [0,longest_ind[1],index_of_longest_sublist]
                else:
                    remove = [result[0][1],longest_ind[1],index_of_longest_sublist]        
                return result
        else:
            remove = [0,-1,-1]
            return []
            
    else:
        remove = [0,-1,-1]
        return []

def shift_list_in_place(l):
    # If the list is empty or has only one element, no need to shift
    if len(l) <= 1:
        return
    # Perform the in-place shift
    last_element = l.pop()  # Remove the last element
    l.insert(0, last_element)  # Insert it at the beginning

# Example usage
buffer_lag = 38
lag = 10


pair_list_list = []
for c in range(int(math.log(N,2))):
    pair_list_list.append([[(0,0) for _ in range(int(N/(2**(c+1))))] for i in range(lag-2*(c+1))])

ru = 0
prev_cmpr = []
prev_out_adder = []
for c in range(int(math.log(N,2))):
    prev_cmpr.append([[0,0] for j in range(int(N/2**(c+1)))])
    prev_out_adder.append([0]*int((N/(2**(c+1)))))

pre_cmpr = [[[0,0]],[[0,0]],[[0,0]]]

prev_memory_locations = []
prev_memory_location = []
for c in range(int(math.log(N,2))):
    prev_memory_location.append([])
last_q = [[[0,0] for c in range(N)] for _ in range(N)]

final_add = [[-1 for i in range(N)] for _ in range(lag)]

remove = [0,-1,-1]
p_remove = [0,-1,-1]

lqd = 0

len_lst = [[0,j]for j in range(N)]
voq_len = [[0 for c in range(N)] for d in range(N)]
gate = [[0,0] for _ in range(N)]

pre_lq = -1
pre_lvoq = -1 

packet_dropped = 0
packet_served = 0
total_packets = 0
index_tracker = [-1]*N

def decide_and_bitmap(d_port,cell_len,s_port,cell_count):
    #This function will decide whether the packet that has reached now has to be dropped or not
    # total packets should record pckeats that are dropped at this point as well as the packet sthat enter the pipeline
    global gate
    global stop
    global free_blocks
    global final_add
    global total_packets
    global buffer
    global packet_dropped
    global index_tracker
    global packet_broken
    
    lqd_bit = [0]*N
    shift_list_in_place(final_add)
    for c in range(N):
        final_add[0][c] = -1
    
    
    for i,k in enumerate(d_port):

        #print(f"the packet {k,cell_len[i]} has reached")

        #this part here checks for addresses when the packets reach the designated spot on the pipeline
        if buffer[i][buffer_lag - lag -1][0] != -1 or stop[i] == 1:
            if free_blocks>i:
                lqd_bit[i] = 0
                final_add[0][i] = memory_manager.malloc()
                free_blocks-=1
            else:
                lqd_bit[i] = 1
                final_add[0][i] = -1
                #breakpoint()
            
        # this will let in packets into the buffer if all conditions are satisfied
        if stop[i] == 0 and  k !=-1 and (gate[i][1] == 1 or (gate[i][1] == 0 and cell_len[i]==0)) :
            shift_list_in_place(buffer[i])
            if index_tracker[i] !=-1:
                index_tracker[i] += 1
            if cell_len[i] == 0:
                index_tracker[i] = 0
            buffer[i][0] = [d_port[i],cell_len[i],s_port[i],cell_count[i]] 
            if cell_len[i] == 0:
                #print("counting the packet")
                total_packets+=1
            gate[i] = [cell_len[i],1]

        # this is when the buffer doesnt allow packets to get in because one of the cells of the packets were dropped
        elif stop[i] == 0 and (gate[i][1] == 0 and cell_len[i]!=0):
            shift_list_in_place(buffer[i])
            if index_tracker[i] !=-1:
                index_tracker[i] += 1
            buffer[i][0] = [-1,-1,-1,-1]

        # this is when there is no packets attempting to get inside the buffer
        elif stop[i] == 0 and  k ==-1:
            shift_list_in_place(buffer[i])
            if index_tracker[i] != -1:
                index_tracker[i] += 1
            buffer[i][0] = [-1,-1,-1,-1]
        
        # this when the pipeline is stalled because the free blocks/lqd were not sufficient to satisfy the requirement at the end of the pipeline
        elif stop[i] == 1 and k != -1:

            # this checks for final add or lqd cell add for the packet that is stuck at the head
            if free_blocks>i and final_add[0][i]==-1:
                lqd_bit[i] = 0
                final_add[0][i] = memory_manager.malloc()
                free_blocks-=1
            elif final_add[0][i]==-1:
                lqd_bit[i] = 1
                final_add[0][i] = -1
            #print("U r getting in here")
            # this will remove any unnecessary packets stored in the buffer
            if (gate[i][0]+1 == cell_len[i] or cell_len[i]==0) and gate[i][1] == 1:
                if index_tracker[i] != -1 and cell_len[i]!=0:
                    for c in range(index_tracker[i]+1):
                        print(index_tracker[i])
                        print(f"removing the packet from buffer = {buffer[i][c]}")
                        packet_broken += 1
                        buffer[i][c] = [-1,-1,-1,-1] #we might have to change this piece of code depending on the cell length and time taken to transmit a cell
                if cell_len[i] == 0:
                    print("counting the packet")
                    total_packets+=1
                index_tracker[i] = -1
                packet_dropped+=1
                gate[i][1] = 0
            
            elif cell_len[i]==0 and gate[i][1] == 0:
                total_packets+=1
                packet_dropped+=1
                gate[i][1] = 0
            

        
        # we forcefully set lqd bit depending upon the requirements just like before
        elif stop[i] == 1 and k == -1:
            if free_blocks>i and final_add[0][i]==-1:
                lqd_bit[i] = 0
                final_add[0][i] = memory_manager.malloc()
                free_blocks-=1
            elif final_add[0][i]==-1:
                lqd_bit[i] = 1
                final_add[0][i] = -1
            
    lqd_bit_map = lqd_bit    


# # check mechanism for packets served and dropped
#     count_q = sum(
#     1
#     for outer in q
#     for middle in outer
#     for inner in middle
#     if inner[1] == 0)

    
#     count_g = 0
#     for layer in buffer:
#         for cell in layer:
#             if cell[1] == 0:
#                 count_g += 1
#     if count_g+count_q+packet_dropped+packet_served != total_packets:
#         print(count_g)
#         print(count_q)
#         print(packet_dropped)
#         print(packet_served)
#         print(total_packets)
#         dfd
    

    return lqd_bit_map


    


def allct(r,t,lq,lvoq):
    global q
    global trk
    global cnt
    global last_q
    global p_remove
    global stop
    global lqd
    global len_lst
    global voq_len
    global free_blocks
    global pre_lq
    global pre_lvoq
    global q_change
    global packet_dropped
    global final_add

    #last_q will be the gate for the entrance to the q on a per input basis
    #gate will be the entrance for the buffer on a per input basis
    
    #this part of the function will check for correct memory address deallocation 
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
    
    #print(q[8][0])
    rej_lqd = 0
    rej_free = 0
    #print(r)
    #print(last_q[0][8])
    for i in range(N):
        # if len(buffer[i][-1]) == 4:
        #     print(f"Placing {[buffer[i][-1][0],buffer[i][-1][1],buffer[i][-1][2],buffer[i][-1][3]]} for {i}")
            
        if r!=[]:

            #in case there was an lqd event in the previous clock cycle and the longest queue changed after it, we remove the excess cells yet to be placed onto the tail of the previous longest queue
            if (q_change == 1 and p_remove[0]!=0 and p_remove[2] == i):
                
                
                last_q[i][p_remove[1]][1] = 0
                #print("setting restrictions for {i}")

                #we are deallocating any packet that was directed to the previous longest queue
                
                #last queue will prevent any excess cells of the packets that were removed from the longest queue from getting in
                
                
                free = copy.deepcopy(q[p_remove[1]][i][-p_remove[0]:])
                del q[p_remove[1]][i][-p_remove[0]:]
                len_lst[p_remove[1]][0] -= p_remove[0]
                voq_len[p_remove[1]][i] -= p_remove[0]
                for c in free:
                    if c[1] == 0:
                        packet_dropped+=1
                    memory_manager.deallocate(c[0])
                    free_blocks+=1
                if buffer[i][-1][0] == p_remove[1]:
                    if r[i]!=[]:
                        memory_manager.deallocate(r[i][0][0])
                        free_blocks+=1
                        rej_lqd+=1
                    if final_add[-1][i]!=-1:
                        memory_manager.deallocate(final_add[-1][i])
                        free_blocks+=1
                        rej_free+=1
                    
                    stop[i] = 1
                else:
                    p_remove = [0,-1,-1]
                    q_change = 0
                

           


            if buffer[i][-1][0] == p_remove[1] and p_remove[2] == i and q_change == 1 and p_remove[0]!=0:
                p_remove = [0,-1,-1]
                q_change = 0
                continue
                
            
            #if the packets are directed to the longest queue, then we should not admit them

            elif buffer[i][-1][0] == lq and lvoq == i and lqd == 1 and last_q[i][buffer[i][-1][0]][1] == 0:
                #print("Not placing because of longest")
                if r[i]!=[]:
                    memory_manager.deallocate(r[i][0][0])
                    free_blocks+=1
                    rej_lqd+=1
                if final_add[-1][i]!=-1:
                    memory_manager.deallocate(final_add[-1][i])
                    free_blocks+=1
                    rej_free+=1
                         
                stop[i] = 1 # we have to change this we have
                
            
            #in general, if the last_q variable is set to 0, unless the cell has a packet index of 0, it wont be admitted
            elif last_q[i][buffer[i][-1][0]][1] == 0 and buffer[i][-1][1] != 0 :
                #print("Not placing because of longest because it was gated")
                # we should place if the removal was not from
                if r[i]!=[]:
                    memory_manager.deallocate(r[i][0][0])
                    free_blocks+=1
                    rej_lqd+=1
                if final_add[-1][i]!=-1:
                    memory_manager.deallocate(final_add[-1][i])
                    free_blocks+=1
                    rej_free+=1
                stop[i] = 0

            #if we get an address from both lqd and free blocks, we will use the address from the free blocks and return the address from the lqd to the free blocks
            elif r[i] != [] and (last_q[i][buffer[i][-1][0]][1] == 1 or buffer[i][-1][1] == 0 ) and final_add[-1][i] != -1 and buffer[i][-1][0]!=-1: # 111 allocate lqd and deallocate final add
                q[buffer[i][-1][0]][i].append([r[i][0][0],buffer[i][-1][1],buffer[i][-1][2],buffer[i][-1][3]])
                memory_manager.deallocate(final_add[-1][i])
                rej_free+=1
                len_lst[buffer[i][-1][0]][0] +=1 
                voq_len[buffer[i][-1][0]][i] +=1 
                free_blocks+=1
                last_q[i][buffer[i][-1][0]] = [buffer[i][-1][1],1]
                stop[i] = 0
            
            #this case is when there is no packet to be allocated, but u got an adress from both free blocks and lqd... this is a hypothetical scenario
            elif r[i] != [] and final_add[-1][i] != -1 and buffer[i][-1][0]==-1 : #110 misc
                asldfkj
            
            # when cell address is made available from lqd only
            elif r[i] != [] and final_add[-1][i] == -1 and buffer[i][-1][0]!=-1 and (last_q[i][buffer[i][-1][0]][1] == 1 or buffer[i][-1][1] == 0): #101 allocate lqd
                q[buffer[i][-1][0]][i].append([r[i][0][0],buffer[i][-1][1],buffer[i][-1][2],buffer[i][-1][3]])
                len_lst[buffer[i][-1][0]][0] +=1 
                voq_len[buffer[i][-1][0]][i] +=1
                last_q[i][buffer[i][-1][0]]  = [buffer[i][-1][1],1]
                stop[i] = 0

            #when there is a cell address from lqd, but there are no packets to be placed
            #happens when there are no packets to be placed but the last chunk of a packet which did not get its cell address from the pipeline - in this scenario, the pipeline is stalled to find an address for the next packet
            #in this case the lqd bits are turned on for the pipeline. it might result in allocating address to 
            elif r[i] != [] and final_add[-1][i] == -1 and buffer[i][-1][0]==-1: #100 misc
                memory_manager.deallocate(r[i][0][0])
                free_blocks+=1
                rej_lqd+=1
            
            #when there is a cell address available from free block
            elif r[i] == [] and final_add[-1][i] != -1 and buffer[i][-1][0]!=-1 and (last_q[i][buffer[i][-1][0]][1] == 1 or buffer[i][-1][1] == 0): #011 allocate final add
                q[buffer[i][-1][0]][i].append([final_add[-1][i],buffer[i][-1][1],buffer[i][-1][2],buffer[i][-1][3]])
                len_lst[buffer[i][-1][0]][0] +=1 
                voq_len[buffer[i][-1][0]][i] +=1
                last_q[i][buffer[i][-1][0]]  = [buffer[i][-1][1],1]
                stop[i] = 0

            #when there is a cell address from free blocks, but there are no packets to be placed
            elif r[i] == [] and final_add[-1][i] != -1 and buffer[i][-1][0]==-1: #010 misc
                memory_manager.deallocate(final_add[-1][i])
                free_blocks+=1
                rej_free+=1

            #stopping the flow when there is no cell address available for a packet cell
            elif r[i] == [] and final_add[-1][i] == -1 and buffer[i][-1][0]!=-1 and (last_q[i][buffer[i][-1][0]][1] == 1 or buffer[i][-1][1] == 0): #001 stall
                
                stop[i] = 1
                #print("Not placing because of unavailability")
            
            #neither cell address not packet present in pipeline
            elif r[i] == [] and final_add[-1][i] == -1 and buffer[i][-1][0]==-1: #000 continue
                continue
            
            else:
                fdf

def priority_encoder(longest_ind,k):
    for c in range(N):
        if voq_len[longest_ind[1]][c] > k:
            index_of_longest_sublist = c
            return index_of_longest_sublist
    for c in range(N):
        if voq_len[longest_ind[1]][c] > 0:
            index_of_longest_sublist = c
            return index_of_longest_sublist
    return(0) 
    


prev_index_of_longest_sublist = 0
prev_dropped_packet = 0
dropped_packet = 0
q_change = 0



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
        if val == expected or val == 0:
            prev_val = val
            expected = (val+1)%19
            continue

        # Early restart with 0 is allowed — just resynchronise
        # elif val == 0:
        #     prev_val = val
        #     expected = 1
        #     continue

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


            

    

import copy
def LQD(d_port,cell_len,t,s_port,cell_count):
    global buffer
    global p_remove
    global remove
    global prev_memory_locations
    global prev_lqd_bit_map
    global dropped_packet
    global prev_dropped_packet
    global prev_index_of_longest_sublist
    global len_lst
    global q_change
    global pre_lq
    global pre_lvoq

########################################### Initialization #############################
    cmpr = []
    out_addr = []
    pair_list = []
    memory_location = []
    for c in range(int(math.log(N,2))):
        cmpr.append([[0,0] for j in range(int(N/2**(c+1)))])
        out_addr.append([0]*int(N/(2**(c+1)))) 
    
########################################## Begin process ################################

    lqd_bit_map = decide_and_bitmap(d_port,cell_len,s_port,cell_count)
    
    
    


    cmpr[0] = compare_non_overlapping_adjacent(len_lst)
    
    out_addr[0],pair = adder(prev_lqd_bit_map)
    
    pair_list.append(pair)
    shift_list_in_place(pair_list_list[0])
    pair_list_list[0][0] = pair_list[0]

    for c in range(int(math.log(N,2))-1):
        cmpr[c+1] = compare_non_overlapping_adjacent(prev_cmpr[c]) 
        #print(f"stage - {2+c+1} cmpr = {cmpr[c+1]}")
        out_addr[c+1],pair = adder(prev_out_adder[c])
        #print(f"stage - {2+c+1} out_addr = {out_addr[c+1]}")
        pair_list.append(pair)
        shift_list_in_place(pair_list_list[c+1])
        pair_list_list[c+1][0] = pair_list[c+1]
    

    #print(f"{prev_cmpr[int(math.log(N,2))-1][0],prev_out_adder[int(math.log(N,2))-1][0]}")
    index_of_longest_sublist = priority_encoder(prev_cmpr[int(math.log(N,2))-1][0],prev_out_adder[int(math.log(N,2))-1][0])
    memory_locations = fetch(pre_out_adder[2][0],pre_cmpr[2][0],prev_index_of_longest_sublist)

    
    #memory_locations = [500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515]
    #dropped_packet += pre_out_adder_4[2][0]
    
    memory_location.append(reverse_tree([prev_memory_locations],pair_list_list[int(math.log(N, 2))-1][-1]))
    #print(memory_location[0])    
    for c in range(int(math.log(N,2))-1):
        memory_location.append(reverse_tree(prev_memory_location[c],pair_list_list[int(math.log(N, 2))-c-2][-1]))
    #print("these are the memory locations")
    #print(memory_location)
    #print(pre_cmpr)
    #print(cmpr[int(math.log(N, 2))-1])
    if ((pre_lq != pre_cmpr[2][0][1] or pre_lvoq != prev_index_of_longest_sublist) and pre_lq!=-1):
        #print(pre_lq)
        q_change = 1
        #print("The q has changed")
    else:
        q_change = 0
        #print("The q has not changed")
    allct(prev_memory_location[int(math.log(N,2))-1],t,pre_cmpr[2][0][1],prev_index_of_longest_sublist)
    deallocate()

    #check for proper cell deallocation

    block_c = 0
    fin_count = 0
    for c in range(lag-1):
        for h in range(N):
            if final_add[c][h]!=-1:
                block_c+=1
                fin_count+=1
    block_c += free_blocks
    q_len = 0
    for c in range(N):
        for h in range(N):
            q_len += len(q[c][h])
            block_c += len(q[c][h])
    
    for c in range(N):
        for h in range(N):
            if voq_len[c][h] <0:
                print(q[c][h])
                print(voq_len[c][h])
                sfd
    total_addresses = sum(
    1
    for row in prev_memory_location[:-1]
    for group in row
    for addr in group)

    block_c+=len(memory_locations)
    block_c+=len(prev_memory_locations)
    block_c+=total_addresses
    if block_c < TOTAL_MEMORY:
        heyyyy
    


################################################# Updating global variables ###########################################
    
    pre_lq = copy.deepcopy(pre_cmpr[2][0][1])
    pre_lvoq = copy.deepcopy(prev_index_of_longest_sublist)
    
    for c in range(int(math.log(N,2))):
        prev_out_adder[c] = out_addr[c]
        prev_cmpr[c] = cmpr[c]
        prev_memory_location[c] = memory_location[c]
        

    prev_memory_locations = memory_locations

    prev_lqd_bit_map = lqd_bit_map
    
        
    pre_cmpr[0] = cmpr[int(math.log(N, 2))-1]
    pre_out_adder[0] = out_addr[int(math.log(N, 2))-1]
    shift_list_in_place(pre_cmpr)
    shift_list_in_place(pre_out_adder)
    prev_index_of_longest_sublist = index_of_longest_sublist
   


    #return memory_location[int(math.log(N, 2))-1]







buffer = [[[-1,-1,-1]]*buffer_lag for _ in range(N)]   
lag = 10
lqd_bit_map = [0 for i in range(N)]
prev_lqd_bit_map = [0 for i in range(N)]



import random

def modify_list(lst, k):
    # Get the indices of all 0s in the list
    zero_indices = [i for i, value in enumerate(lst) if value == 0]
    
    # Ensure there are enough 0s to turn into 1s
    if k > len(zero_indices):
        raise ValueError("Not enough 0s in the list to make k of them 1.")
    
    # Randomly select k indices from the zero indices
    selected_indices = random.sample(zero_indices, k)
    
    # Change the selected indices in the list to 1
    for index in selected_indices:
        lst[index] = 1
    return lst

pointer = [0]*N
sum_c = 0

def pad_to_cell(bytes_, cell_size):
    return ((bytes_ + cell_size - 1) // cell_size) * cell_size



stop = [0]*N
tra = [-1]*N
c = 0
rr = [0]*N
stage = [[] for _ in range(N)]
stall_s = [0.0]*N
track_s = [0]*N
packets_sent = 0
packets_received = 0
valid = [0]*N
p_y = [[0 for i in range(N)] for _ in range(N)]
count = [-1]*N
reading = [-1]*N
bytes_sent = [0]*N
pending_head = [[0 for _ in range(N)] for _ in range(N)]
packet_broken = 0
def deallocate():
    global free_blocks
    global q
    global voq_len
    global len_lst
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
    global packet_broken
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

        # --------------------------------------------------------
        # Service timing: if output d is still busy, wait.
        # --------------------------------------------------------
        if stall_s[d] > track_s[d]:
            track_s[d] += 1
            continue

        # --------------------------------------------------------
        # Pick next active VOQ using RR.
        # --------------------------------------------------------
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

        # --------------------------------------------------------
        # Remove exactly one cell.
        # --------------------------------------------------------
        cell = q[d][i].pop(0)

        addr = cell[0]
        seq = cell[1]
        size_bytes = cell[2]

        memory_manager.deallocate(addr)
        free_blocks += 1

        bytes_sent[d] += size_bytes

        # Update queue bookkeeping.
        voq_len[d][i] = len(q[d][i])
        len_lst[d][0] -= 1

        if len_lst[d][0] < 0:
            print(f"ERROR: len_lst[{d}][0] went negative")
            print(f"cell removed = {cell}")
            print(f"q[{d}][{i}] len = {len(q[d][i])}")
            breakpoint()

        # --------------------------------------------------------
        # Packet accounting.
        #
        # Valid:
        #   0 then 1 from the same q[d][i] => served
        #
        # Corrupt:
        #   0 then 0 from the same q[d][i] => previous packet dropped
        #   1 with no pending 0 => orphan tail, not served
        # --------------------------------------------------------
        if seq == 0:
            if pending_head[d][i] == 1:
                # Previous head was never followed by seq 1.
                # Since we are seeing another head, previous packet is corrupt.
                packet_dropped += 1
                packet_broken += 1 

            # This cell becomes the new pending head.
            pending_head[d][i] = 1

        elif seq == 1:
            if pending_head[d][i] == 1:
                # Valid packet completed.
                packet_served += 1
                pending_head[d][i] = 0
            else:
                # Tail without head. Corrupt tail.
                # Remove it, but do not count served.
                packet_broken += 1 

        else:
            # Unexpected sequence for 2-cell packets.
            # Remove it, but do not count served.
            if pending_head[d][i] == 1:
                packet_dropped += 1
                packet_broken += 1
                pending_head[d][i] = 0
            else:
                packet_broken += 1

        # --------------------------------------------------------
        # Preserve stall/track timing.
        # This output now becomes busy for this cell's service time.
        # --------------------------------------------------------
        stall_s[d] = size_bytes * 8 / (link_speed * time_period)
        track_s[d] = 1

        # These are no longer used for scheduling, but keep them sane.
        reading[d] = seq
        count[d] = 2

        # --------------------------------------------------------
        # Advance RR to the next VOQ after the one served.
        # --------------------------------------------------------
        rr[d] = (i + 1) % N

    # ------------------------------------------------------------
    # Final bookkeeping repair.
    # ------------------------------------------------------------
    for d in range(N):
        actual_output_len = 0

        for i in range(N):
            voq_len[d][i] = len(q[d][i])
            actual_output_len += len(q[d][i])
            p_y[d][i] = 0

        len_lst[d][0] = actual_output_len

        if actual_output_len == 0:
            count[d] = -1
            reading[d] = -1

trk = lag
free_blocks = int(TOTAL_MEMORY)
link_speed = 4*10**11 #100 Gbps
time_period = 1*(10**-9) #10ns
freeb = [699]*12

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


def main(burst,incast,round):
    global N
    global T
    global M
    global K
    global c
    global t
    global cell_size
    # Initialize dataset
    global packet_dropped
    global total_packets
    global packet_served
    global dest_port
    global size
    global trk
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
    track = [1 for _ in range(N)]
    d_port = [-1]*N
    s_port = [-1]*N
    cell_len = [-1]*N
    cell_count = [0]*N
    phase_2 = 0
    
    
    t = 0
    while True:
        t+=1
        log_q_sums(q,t,path = f"./q_log/q_sums_{burst}_{incast}_{round}_obm.csv")
        # print(f"time = {t}")
        # if t>47000:
        #     print(buffer[9])
        #     print(q[7][9][-36:])
        #print(bytes_sent)
        #print(v[14])
        # if v[14] == 300:
        #     dsd
        # print(v)
        # print(total_packets/16)
        #print(f"time = {t}")
        # if total_packets%16!=0:
        #     dd
        # print(packet_dropped)
        # print(packet_served)
        # print(free_blocks)
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
        sum = 0
        for e in q:
            for o in e:
                sum += len(o)
        if ray_of_death == 0:
            break
        
        
    
    # print(packet_served,packet_dropped,total_packets)
    # for c in range(4):
    #     for j in range(4):
    #         print("**************************************")
    #         print("**************************************")
    #         print(f"q for {c},{4*c+j} - {q[c][4*c+j]}")
    

    
    
    while True:
        q_not_empty = False

        for c in range(N):
            for h in range(N):
                if len(q[c][h]) > 0:
                    q_not_empty = True
                    break
            if q_not_empty:
                break

        if not q_not_empty:
            break

        t += 1
        log_q_sums(q, t, path=f"./q_log/q_sums_{burst}_{incast}_{round}_obm.csv")

        # Drain only. Do not call LQD here.
        deallocate()

    n = len(q)
# generate all (i,j) pairs, then pick the one whose q[i][j] has the greatest len()
    longest = max(
        ((i, j) for i in range(n) for j in range(n)),
        key=lambda ij: len(q[ij[0]][ij[1]])
    )
    print(packet_served)
    print(packet_dropped)
    print(total_packets)
    return t
            
import sys
 # Save the original stdout (standard output) \
def run(i):
    original_stdout = sys.stdout         
    with open(fr'/home/dan/LQD/LQD/master/n_2_logs/output_n_2_{i}.txt', 'w') as file: # Redirect stdout to the file 
        sys.stdout = file
        t = main(i)
        print(f"dropped packets = {packet_dropped}")
        print("n**2_q algo")
        print(f"packets served = {packet_served}")
        print(f"{packet_served*160*8*(10**-9)/(t*time_period)} gbps per port")
        sys.stdout = original_stdout
    print("Entered text in file")

import sys, pdb
def _excepthook(exc_type, exc, tb):
    pdb.post_mortem(tb)  # opens pdb at the crash site
sys.excepthook = _excepthook
import sys
time = main(int(sys.argv[1]),sys.argv[2],int(sys.argv[3]))
print(f"dropped packets = {packet_dropped}")
print(f"time = {time}")
print("OBM")
print(f"packets served = {packet_served}")
print(f"{sum(bytes_sent)*8*(10**-9)/(time*time_period)} gbps per port")
print(f"{sum(bytes_sent)*8*(10**-9)/(time_period)} divide this value by max time")
print(f"broken packets = {packet_broken}")