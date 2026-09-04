# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import queue
import hashlib
from link import Link
import math
import copy
import joblib
import numpy as np
import re
import os
# Import the FastForest class
from FastForest import FastForest

class Switch():
    """
    Switch class implementing CREDENCE logic with Drop Tail.
    """

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack):
        """Initialize parameters"""
        self.addr = addr
        self.links = {}   # links indexed by port
        self.queues = {}  # list of virtual output queues
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 5  
        self.K = 4                   
        self.num_tor_ports = num_tor_ports
        self.num_agg_ports = num_agg_ports
        self.hosts_per_rack = hosts_per_rack
        self.tor_buff_size = self.per_port_max_qsize * self.num_tor_ports
        self.agg_buff_size = self.per_port_max_qsize * self.num_agg_ports
        self.packet_dropped = 0
        self.port_qsize = {}  
        self.priority_classes = 3
        
        # --- CREDENCE / ML VARIABLES ---
        self.model = None
        self.ewma_alpha = 2 / (30 + 1)
        self.avg_q_len = {}          
        self.avg_shared_occ = 0.0    
        self.virtual_T = {} 
        self.virtual_gamma = 0       
        # -------------------------------

        if self.addr[0] == 't':
            self.ports = num_tor_ports
            self.total_buffer_size = self.per_port_max_qsize * num_tor_ports
            self.N = 1 if num_tor_ports < 1 else 2 ** ((num_tor_ports - 1).bit_length())
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize * num_agg_ports
            self.N = 1 if num_agg_ports < 1 else 2 ** ((num_agg_ports - 1).bit_length())
            self.voq_port_qsize = [[0 for i in range(self.priority_classes)] for _ in range(self.N)]
            print(num_agg_ports)

        # Initialize tracking dicts for CREDENCE
        for i in range(1, self.N + 1):
            self.virtual_T[i] = 0
            self.avg_q_len[i] = 0.0

        self.total_usage = 0 
        self.sent = 0
        self.t = 0
        
        # --- LOAD ML MODEL (CREDENCE) ---
        try:
            jobfile = re.compile(f"model_ports{self.ports}_")
            found = False
            for filename in os.listdir('.'):
                if jobfile.match(filename):
                    print(f"Loading raw model for {self.addr}: {filename}...")
                    raw_model = joblib.load(filename)
                    # Convert to FastForest
                    self.model = FastForest(raw_model)
                    del raw_model 
                    print(f"CREDENCE: Optimized model ready for {self.addr}.")
                    found = True
                    break
            if not found:
                print(f"WARNING: No matching model found for {self.addr} (ports={self.ports})")
        except Exception as e:
            print(f"Error loading model: {e}")

    # --- CREDENCE HELPER FUNCTIONS ---
    def _update_virtual_lqd(self, port_idx, event_type):
        """Updates the virtual thresholds T according to LQD logic for ML features."""
        if event_type == 'arrival':
            if self.virtual_gamma == self.total_buffer_size:
                # Push-out simulation
                if self.virtual_T:
                    j = max(self.virtual_T, key=self.virtual_T.get)
                    self.virtual_T[j] -= 1
                    self.virtual_T[port_idx] += 1
            else:
                self.virtual_T[port_idx] += 1
                self.virtual_gamma += 1
                
        elif event_type == 'departure':
            if self.virtual_T[port_idx] > 0:
                self.virtual_T[port_idx] -= 1
                self.virtual_gamma -= 1

    def _update_ewma(self, port_idx):
        """Updates exponentially weighted moving averages"""
        curr_q = self.port_qsize.get(port_idx, 0)
        curr_occ = self.total_usage
        
        self.avg_q_len[port_idx] = (self.ewma_alpha * curr_q) + \
                                   ((1 - self.ewma_alpha) * self.avg_q_len[port_idx])
        
        self.avg_shared_occ = (self.ewma_alpha * curr_occ) + \
                              ((1 - self.ewma_alpha) * self.avg_shared_occ)
    # ---------------------------------

    def runSwitch(self, currTimeslot):
        """Main loop of switch: Round Robin Service"""
        self.t += 1
        
        for port in self.links.keys(): 
            start = self.voq_rr[port]
            flag_1 = 0
            for i in range(0, len(self.queues[port]) + 1):
                if self.queues[port][(start + i) % len(self.queues[port])].empty():
                    continue
                else:
                    for j in range(0, self.queues[port][(start + i) % len(self.queues[port])].qsize()):
                        packet = self.queues[port][(start + i) % len(self.queues[port])].get_nowait()
                        if packet.invalid == 0:
                            # --- HOP COUNTING ---
                            packet.hops += 1
                            # --------------------

                            self.voq_rr[port] = (start + i + 1) % len(self.queues[port])
                            self.links[port].send(packet, self.addr, currTimeslot)
                            self.port_qsize[port] -= 1
                            self.sent += 1
                            self.total_usage -= 1 
                            self.voq_port_qsize[port - 1][(start + i) % len(self.queues[port])] -= 1
                            
                            # [CREDENCE] Update Virtual LQD on departure
                            self._update_virtual_lqd(port, 'departure')
                            
                            flag_1 = 1
                            assert(self.port_qsize[port] >= 0)
                            break
                        
                    if flag_1:
                        break

        # Receive Packets
        for port in self.links.keys():
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                # handleRecvdPacket uses pure Drop Tail logic (no LQD push-out)
                self.handleRecvdPacket(packet, currTimeslot)

        
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

    def handleRecvdPacket(self, packet, arrivalTime):
        """
        Handle the packet received using CREDENCE logic.
        """
        outPort = self.getOutPort(self.addr, packet)
        
        # 1. Update Virtual Thresholds
        self._update_virtual_lqd(outPort, 'arrival')
        
        # 2. Update Stats
        self._update_ewma(outPort)
        
        decision = "DROP"
        
        # --- CREDENCE LOGIC START ---
        
        # Safeguard Condition
        longest_queue_len = 0
        if len(self.port_qsize) > 0:
            longest_queue_len = max(self.port_qsize.values())

        safeguard_threshold = self.total_buffer_size / self.N
        
        if longest_queue_len < safeguard_threshold:
            decision = "ACCEPT"
        else:
            # Threshold Check
            current_q_len = self.port_qsize.get(outPort, 0)
            virtual_threshold = self.virtual_T[outPort]
            
            if current_q_len < virtual_threshold:
                if self.total_usage < self.total_buffer_size:
                    # ML Prediction
                    #print("ML prediction invoked")
                    if self.model:
                        prediction = self.model.predict(
                            current_q_len, 
                            self.total_usage, 
                            self.avg_q_len[outPort], 
                            self.avg_shared_occ
                        )
                        if prediction == 0:
                            decision = "ACCEPT"
                        else:
                            print("CREdence says drop")
                            decision = "DROP"
                            #breakpoint()
                    else:
                        # Fallback if model failed to load
                        decision = "ACCEPT"
                else:
                    decision = "DROP" # Physically full
            else:
                decision = "DROP" # Exceeds virtual threshold
                
        # --- EXECUTE DECISION ---
        if decision == "ACCEPT":
            if self.total_usage < self.total_buffer_size:
                inPort_priority = packet.priority
                self.total_usage += 1
                self.queues[outPort][inPort_priority-1].put(packet)
                self.port_qsize[outPort] += 1
                self.voq_port_qsize[outPort-1][inPort_priority-1] += 1
                self.setECNFlag(packet, outPort)
            else:
                self.packet_dropped += 1
        else:
            self.packet_dropped += 1