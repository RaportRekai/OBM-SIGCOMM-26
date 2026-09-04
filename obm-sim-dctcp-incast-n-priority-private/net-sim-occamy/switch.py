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

    def __init__(self, addr,load, num_tor_ports, num_agg_ports, hosts_per_rack):
        """Initialize parameters"""
        self.addr = addr  # address of switch
        self.links = {}   # links indexed by port
        self.queues = {}  # list of virtual output queues per port
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 4  # in terms of number of size in Bytes
        self.K = 25                   # threshold for ECN marking

        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        
        # Buffer sizes in packets
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports 
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports 
        
        self.packet_dropped = 0
        self.port_qsize = {}  # number of packets queued per port

        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize*num_tor_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.N)] for _ in range(self.N)]
            self.per_port_buffer = [0 for i in range(self.ports)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.N)] for _ in range (self.N)]
            self.per_port_buffer = [0 for i in range(self.ports)]
            print(num_agg_ports)

        #########################################################################################################
        # OCCAMY INIT
        #########################################################################################################
        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.T = self.total_buffer_size/(self.N) # Single global threshold
        self.sent = 0
        #self.alpha = 8
        #self.alpha = 1
        #self.alpha = 0.8
        #self.alpha = 8 works for 0.3 and 0.6
        self.alpha = 4 if load == "0.4" else 4
        self.alpha = 10 if load == "0.2" else self.alpha
        self.alpha = 8 if load == "0.8" else self.alpha
        #self.alpha = 10 if load == "0.3" else self.alpha
        self.t = 0
        self.track = 0

        # Occamy specific tracking
        self.drop_timer = 0
        
        # 1. Global Round Robin to pick the PORT
        self.expulsion_port_rr_idx = 0  
        
        # 2. Per-Port Round Robin to pick the VOQ inside that port
        # Stores { port_id: last_checked_voq_index }
        self.expulsion_voq_rr = {} 

    def runSwitch(self, currTimeslot):
        """Main loop of switch"""
        self.t += 1
        
        # ---------------------------------------------------------------------
        # 1. OCCAMY EXPULSION LOGIC (Nested Round Robin)
        # ---------------------------------------------------------------------
        self.drop_timer += 1
        
        if self.drop_timer % 1 == 0:
            
            # Sorted ports for consistent ordering
            sorted_ports = sorted(list(self.links.keys()))
            num_ports = len(sorted_ports)
            packet_expelled = False
            
            # --- OUTER LOOP: Iterate Ports (Global RR) ---
            for i in range(num_ports):
                # Pick port based on Global Port RR Index
                p_idx = (self.expulsion_port_rr_idx + i) % num_ports
                port_key = sorted_ports[p_idx]
                
                # Ensure we have a saved VOQ index for this port
                if port_key not in self.expulsion_voq_rr:
                    self.expulsion_voq_rr[port_key] = 0
                
                # --- INNER LOOP: Iterate VOQs for THIS Port (Per-Port RR) ---
                # self.N is the number of input-VOQs per output port
                for j in range(self.N):
                    # Pick VOQ based on this Port's specific RR Index
                    v_idx = (self.expulsion_voq_rr[port_key] + j) % self.N
                    
                    # Check threshold
                    if self.voq_port_qsize[port_key-1][v_idx] > self.T:
                        
                        pq = self.queues[port_key][v_idx]
                        if hasattr(pq, 'queue') and len(pq.queue) > 0:
                            head_packet = pq.queue[0]
                            
                            if head_packet.invalid == 0 and head_packet.prvt == 0:
                                # 1. Drop Packet
                                head_packet.invalid = 1 
                                
                                # 2. Update Counters
                                self.total_usage -= 1
                                self.port_qsize[port_key] -= 1
                                self.voq_port_qsize[port_key-1][v_idx] -= 1
                                self.packet_dropped += 1
                                
                                # 3. Update INDICES
                                # Update this port's specific VOQ pointer
                                self.expulsion_voq_rr[port_key] = (v_idx + 1) % self.N
                                
                                # Update global port pointer (start next search from next port)
                                self.expulsion_port_rr_idx = (p_idx + 1) % num_ports
                                
                                packet_expelled = True
                                break 
                
                if packet_expelled:
                    break

        # ---------------------------------------------------------------------
        # 2. SENDING LOGIC (Round Robin with Invalid Check)
        # ---------------------------------------------------------------------
        for port in self.links.keys():
            start = self.voq_rr.get(port, 0)
            flag_1 = 0
            
            num_queues = len(self.queues[port])
            
            for i in range(0, num_queues):
                curr_q_idx = (start + i) % num_queues
                
                if self.queues[port][curr_q_idx].empty():
                    continue
                else:
                    # Drain Invalid Packets from Head
                    while not self.queues[port][curr_q_idx].empty():
                        packet = self.queues[port][curr_q_idx].get_nowait()
                        
                        if packet.invalid == 1:
                            # Expelled packet, skip
                            continue
                        else:
                            #packet.hops +=1
                            if packet.prvt == 1:
                                if self.per_port_buffer[port-1]==1:
                                    self.per_port_buffer[port-1] = 0
                                else:
                                    breakpoint()
                            else:
                                if self.port_qsize[port] <=0:
                                    breakpoint()
                                self.port_qsize[port] -= 1
                                self.total_usage-=1 
                                self.voq_port_qsize[port-1][curr_q_idx]-=1
                            # Valid packet found
                            packet.prvt = 0
                            self.links[port].send(packet, self.addr, currTimeslot)
                            
                            self.voq_rr[port] = (curr_q_idx + 1) % num_queues
                            
                            self.sent += 1
                            #self.total_usage -= 1 
                            
                            flag_1 = 1
                            assert(self.port_qsize[port] >= 0)
                            break
                    
                    if flag_1 == 1:
                        break

        # ---------------------------------------------------------------------
        # 3. RECEIVING LOGIC
        # ---------------------------------------------------------------------
        for port in self.links.keys(): 
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                packet.invalid = 0
                self.handleRecvdPacket(port, packet, currTimeslot)
            else:
                self.final_add[port-1] = 0
        
        return self.packet_dropped

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

    ########################################################################
    # OCCAMY THRESHOLD CALCULATION
    ########################################################################

    def threshold_calculate(self):
        # Single threshold applied to ALL queues
        self.T = self.alpha * (self.total_buffer_size - self.total_usage)

    def handleRecvdPacket(self, inPort, packet, arrivalTime):
        """Handle the packet received on the specified input port"""
        outPort = self.getOutPort(self.addr, packet)
        
        # ---------------------------------------------------------
        # OCCAMY ADMISSION CONTROL
        # ---------------------------------------------------------
        if self.per_port_buffer[outPort-1] == 0:
            self.per_port_buffer[outPort-1] = 1
            # we have to introduce a new field for packet.py
            packet.prvt = 1
            self.queues[outPort][inPort-1].put(packet)
            #breakpoint()
        
        elif self.total_buffer_size > self.total_usage:
            #breakpoint()
            # Check Port Queue Size (or VOQ size based on your specific logic)
            # Standard Occamy checks Port Queue Size against T
            if self.port_qsize[outPort] < self.T:
                self.final_add[inPort-1] = 1
                self.total_usage += 1
                
                # Add to queue (indexed by InPort-1)
                self.queues[outPort][inPort-1].put(packet)
                
                self.port_qsize[outPort] += 1
                self.voq_port_qsize[outPort-1][inPort-1] += 1
                
                self.setECNFlag(packet, outPort)
            else:
                self.final_add[inPort-1] = 0
                self.packet_dropped += 1
        else:
            self.final_add[inPort-1] = 0
            self.packet_dropped += 1
        
        self.threshold_calculate()