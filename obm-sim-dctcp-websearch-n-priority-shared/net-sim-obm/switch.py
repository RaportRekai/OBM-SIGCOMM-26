# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import queue
import hashlib
from link import Link
import math
import copy

class Switch():
    """Switch class"""

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack):
        """Initialize parameters"""
        self.addr = addr  # address of switch
        self.links = {}   # links indexed by port, i.e., {port:link, ......, port:link}
        self.queues = {}  # list of virtual output queues (of type queue.Queue) per port
                          # indexed by port, i.e., {port:[queue], ......, port:[queue]}
                          # each virtual output queue is a FIFO queue of infinite size
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 5  # in terms of number of 1500B packets
        self.K = 25                   # threshold for ECN marking (in terms of number of packets)
        self.flag = 0
        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports # in terms of number of packets
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports # in terms of number of packets
        self.packet_dropped = 0
        self.port_qsize = {}  # number of packets queued per port
        
        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize*num_tor_ports
            self.N = 1 if num_tor_ports < 1 else 2 ** ((num_tor_ports - 1).bit_length())
            self.voq_port_qsize = [[0 for i in range(self.N)] for _ in range(self.N)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
            self.N = 1 if num_agg_ports < 1 else 2 ** ((num_agg_ports - 1).bit_length())
            self.voq_port_qsize = [[0 for i in range(self.N)] for _ in range(self.N)]
            print(num_agg_ports)
            

        #########################################################################################################
        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.T = self.total_buffer_size
        self.sent = 0
        self.t = 0
        self.k = 0
        self.t_track = 0
        self.buffer = [[-1,-1] for i in range(self.N)]

        # --- DATA ACQUISITION / TRAINING VARIABLES ---
        self.avg_q_len = 0.0
        self.avg_occ = 0.0
        # Alpha for EWMA. Fixed RTT = 30 timestamps.
        self.alpha = 2 / (30 + 1)

        # Switch-assigned unique ID for packet arrivals (per switch)
        self.arrival_uid = 0

        # The Master Log for Training Data
        # Format: { "switch_uid": [queueLength, sharedOccupancy, avgQ, avgOcc, drop_status] }
        self.packet_history = {}
        # ---------------------------------------------


    def runSwitch(self, currTimeslot):
        """Main loop of switch"""
        self.t+=1
        
        for port in self.links.keys():  # in each timeslot, send a packet
                                        # at the head of a VOQ at each port.
                                        # VOQs at each port are scheduled in
                                        # round robin manner
            start = self.voq_rr[port]
            flag_1 = 0
            for i in range(0,len(self.queues[port])+1):
                if self.queues[port][(start+i)%len(self.queues[port])].empty():
                    continue
                else:
                    #print(packet)
                    #print(len(self.queues[port]))
                    for j in range(0,self.queues[port][(start+i)%len(self.queues[port])].qsize()):
                        packet = self.queues[port][(start+i)%len(self.queues[port])].get_nowait()
                        if packet.invalid == 0:
                            #print("packetsent")
                            # if packet.priority == 1 and self.voq_port_qsize[port-1][1] != 0 and self.voq_port_qsize[port-1][2] != 0 and  self.voq_port_qsize[port-1][0]!=1 and self.addr == 't1':
                            #     #print(self.voq_port_qsize[port-1])

                            #     with open("/home/dan/LQD/obm-sim/obm-sim/max_q_length.txt", "a") as f:
                            #         f.write(f"{self.voq_port_qsize[port-1],self.addr,port-1}\n")
                            
                            #packet.hops += 1 # Integrated hop tracking
                            self.voq_rr[port] = (start+i+1)%len(self.queues[port])
                            self.links[port].send(packet, self.addr, currTimeslot)
                            self.port_qsize[port] -= 1
                            self.sent+=1
                            #print(f"I - {self.addr} have {self.total_usage}/{self.total_buffer_size} packets in buffer")
                            #print(f"Packet sent = {self.addr} at {port-1} {(start+i)%len(self.queues[port])} at time {self.t}")
                            self.total_usage-=1 
                            self.voq_port_qsize[port-1][(start+i)%len(self.queues[port])]-=1
                            flag_1 = 1
                            assert(self.port_qsize[port] >= 0)
                            break
                        # else:
                        #     #print("Invalid packet!!")
                        
                    if flag_1:
                        break

        self.k = 0
        self.buffer = [[-1,-1] for i in range(self.N)]
        self.largest_index = max(self.port_qsize, key=self.port_qsize.get)
        #print(f"The largest q is {self.largest_index}")
        #print(f"port qsize = {self.port_qsize}")
        for port in self.links.keys():  # in each timeslot, receive a
                                        # pa cket (if any) on each input
                                        # port and handle it
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                self.handleRecvdPacket(port, packet, currTimeslot)
        if self.k>0:
            self.lvoq = self.priority_encoder(self.largest_index,self.k)
            mem = self.fetch()
            self.allct(mem)
        
        #if self.t > self.t_track:
        #    self.t_track+=200
        #    if self.addr == 't9':
        #        print(f"switch {self.addr}, usage = {self.total_usage}, total = {self.total_buffer_size}")

        
    def setECNFlag(self, packet, outPort):
        if self.port_qsize[outPort] > self.K:
            packet.ecnFlag = 1


    def ecmp(self, packet):
        flowid = packet.srcAddr + packet.dstAddr + str(packet.srcPort) + str(packet.dstPort)
        outPort = int(hashlib.sha256(flowid.encode('utf-8')).hexdigest(), 16) % (self.num_tor_ports - self.hosts_per_rack) + (self.hosts_per_rack + 1)
        return outPort


    def getOutPort(self, switchId, packet):
        if switchId[0] == 't':
            if int(packet.dstAddr[1:]) >= int(switchId[1])*16-15 and int(packet.dstAddr[1:]) <= int(switchId[1])*16:
                return int(packet.dstAddr[1:])-((int(switchId[1])-1)*16)
            else:
                return self.ecmp(packet)
        elif switchId[0] == 'a':
            return int((int(packet.dstAddr[1:])-1)/16)+1
######################################################################## Additional ######################################################################################

    def find_index_of_largest(self):
        elements = []
        queue_instance = self.port_qsize
        
        # Dequeue all elements and keep them in a list
        while not queue_instance.empty():
            elements.append(queue_instance.get())
        
        # Find the index of the largest element
        index_of_largest = elements.index(max(elements))
        
        # Restore the elements back to the queue
        for item in elements:
            queue_instance.put(item)
        
        return index_of_largest

    def priority_encoder(self,longest_ind,k):
        for inPort in range(self.ports):
            
            if self.voq_port_qsize[longest_ind-1][inPort]>=k:
                #print(f"got {k} locations")
                return inPort
        ##print(f"Not able to get {k} locations")
        #gjhg
        #print(f"voq {longest_ind-1}  = {self.voq_port_qsize[longest_ind-1]}")

        return 0
    
    def fetch(self):
        mem_loc = []
        target_queue = self.queues[self.largest_index][self.lvoq]
        
        # if self.flag == 1:  
        #     print(f"target queue = {target_queue.qsize()}") # actual q size
        #     print(f"maxsize queue = {target_queue.maxsize}")
        #print(k)
        for h in range(self.k):
            if not target_queue.empty():  # Ensure the queue is not empty
                #print(f"Have removed an element from voq [{self.largest_index-1},{self.lvoq}]")
                #print(f"Number of packets available: {self.voq_port_qsize[self.largest_index-1][self.lvoq]}")
                
                # Access the last element directly
                #print(f"In contrast we have only {target_queue.qsize()} packets")
                #last_element = target_queue.queue.pop()  # Access the last element
                #last_element.invalid = 1  # Mark it as invalid (or any custom modification)
                c = 0
                while target_queue.queue[target_queue.qsize()-c-1].invalid ==1 and c!=target_queue.qsize():
                    c+=1
                if c==target_queue.qsize(): 
                    self.flag = 1
                    break
                target_queue.queue[target_queue.qsize()-c-1].invalid = 1
                
                # --- DATA ACQUISITION: UPDATE LOG (PACKET EVICTED) ---
                # This packet was just invalidated (virtually dropped) by LQD
                pkt = target_queue.queue[target_queue.qsize()-c-1]
                victim_id = getattr(pkt, "switch_uid", None)
                if victim_id is not None and victim_id in self.packet_history:
                    self.packet_history[victim_id][4] = 1 # Update drop status to 1
                # -----------------------------------------------------

                mem_loc.append(1)  # Log the memory location (example)
                self.packet_dropped+=1
                msg = f"switch {self.addr} - space constrain drop - {self.packet_dropped} \n"
                with open("drop_stats_obm.txt", "a") as f:
                    f.write(msg)
                # Optionally remove the last element
                #target_queue.queue.pop()  # Remove the last element if needed
                self.port_qsize[self.largest_index] -= 1
                self.voq_port_qsize[self.largest_index-1][self.lvoq] -= 1
                self.total_usage -= 1 
                
            else:
                #print(f"Queue [{self.largest_index}][{ind}] is empty.")
                break  # Stop if the queue becomes empty
        
        return mem_loc
    
    def allct(self,mem):
        space = sum(mem)
        trk = 0
        req = 0
        for ind,i in enumerate(self.buffer):
            if i[1] != -1:
                req+=1
        if req > space:
            self.packet_dropped+= (req - space)
            msg = f"switch {self.addr} - space constrain drop - {self.packet_dropped} \n"
            with open("drop_stats_obm.txt", "a") as f:
                f.write(msg)
        for ind,i in enumerate(self.buffer):
            if i[1] != -1:
                self.queues[i[1]][ind].put(i[0])
                trk +=1
                self.total_usage +=1
                self.port_qsize[i[1]] += 1
                self.setECNFlag(i[0], i[1])
                self.voq_port_qsize[i[1]-1][ind]+=1
            if trk == space:
                break
        
        

###############################################################################################################################################################

    def handleRecvdPacket(self, inPort, packet, arrivalTime):
        """Handle the packet received on the specified input port 'inPort'.
           arrivalTime is the timeslot in which the packet was received"""
        outPort = self.getOutPort(self.addr, packet)  # output port the packet needs to be sent out on
        
        # --- DATA ACQUISITION LOGIC START ---
        # 1. Update Moving Averages (based on target outPort state)
        current_q = self.port_qsize.get(outPort, 0)
        current_occ = self.total_usage

        self.avg_q_len = (1 - self.alpha) * self.avg_q_len + (self.alpha * current_q)
        self.avg_occ = (1 - self.alpha) * self.avg_occ + (self.alpha * current_occ)

        # 2. Generate Switch-Assigned Unique ID (per arrival event)
        self.arrival_uid += 1
        unique_id = f"{self.addr}_{self.arrival_uid}"
        # Persist on the packet so fetch() can update the correct row later
        packet.switch_uid = unique_id

        # 3. Log Initial State (Default drop = 0)
        # Record the state *before* we make the drop/enqueue decision
        self.packet_history[unique_id] = [
            current_q,
            current_occ,
            round(self.avg_q_len, 4),
            round(self.avg_occ, 4),
            0
        ]
        # --- DATA ACQUISITION LOGIC END ---

################################################################################ BIT MAPPER ########################################################################################
        if self.total_buffer_size > self.total_usage:

            self.total_usage +=1
            self.queues[outPort][inPort-1].put(packet)
            self.port_qsize[outPort] += 1
            self.voq_port_qsize[outPort-1][inPort-1]+=1
            self.setECNFlag(packet, outPort)
            #print(f"Packet placed = {self.addr} at {outPort-1} {inPort-1} at time {self.t}")
            #print(f"port qsize = {self.port_qsize}")
        #print("Packets scheduled via final add")
        else:
            if outPort != (self.largest_index):
                self.buffer[inPort-1] = [packet,outPort]
                self.k +=1   
                #print("Initiated LQD")       
            else:
                # Fallthrough: Tail Drop 
                # Packet is implicitly dropped here because LQD is not triggered
                # and buffer is full. Mark as dropped in history.
                self.packet_history[unique_id][4] = 1

    def export_training_data(self, filename="training_data.csv"):
        """Call this at the end of the simulation to dump the CSV (space-separated)."""
        print(f"Exporting {len(self.packet_history)} records to {filename}...")
        try:
            with open(filename, "w") as f:
                # Header (space-separated)
                f.write("queueLength sharedOccupancy averageQueueLength averageOccupancy drop\n")

                # Rows
                for _, data in self.packet_history.items():
                    f.write(" ".join(map(str, data)) + "\n")

            print("Export complete.")
        except Exception as e:
            print(f"Failed to export data: {e}")