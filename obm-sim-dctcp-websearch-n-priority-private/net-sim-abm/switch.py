# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
import queue
import hashlib
from link import Link
import math
import copy

PACKET_SIZE = 1500

class Switch():
    """Switch class"""

    def __init__(self, addr, num_tor_ports, num_agg_ports, hosts_per_rack,load,alpha_t):
        """Initialize parameters"""
        self.addr = addr  # address of switch
        self.links = {}   # links indexed by port, i.e., {port:link, ......, port:link}
        self.queues = {}  # list of virtual output queues (of type queue.Queue) per port
                          # indexed by port, i.e., {port:[queue], ......, port:[queue]}
                          # each virtual output queue is a FIFO queue of infinite size
        self.voq_rr = {}  # stores the VOQ per port to be serviced next
        self.per_port_max_qsize = 4  # in terms of number of 1500B packets
        self.K = 25                   # threshold for ECN marking (in terms of number of packets)

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
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.N)] for _ in range(self.N)]
            self.per_port_buffer = [0 for _ in range(self.ports)]
            print(num_tor_ports)
        elif self.addr[0] == 'a':
            self.ports = num_agg_ports
            self.total_buffer_size = self.per_port_max_qsize*num_agg_ports
            self.N = self.ports
            self.voq_port_qsize = [[0 for i in range(self.N)] for _ in range (self.N)]
            self.per_port_buffer = [0 for _ in range(self.ports)]
            print(num_agg_ports)
            

        #########################################################################################################
        self.total_usage = 0 
        self.final_add = [0 for i in range(self.N)]
        self.T = [self.total_buffer_size/self.N for _ in range(self.ports)]
        self.T_h = [self.total_buffer_size/self.N for _ in range(self.ports)]
        self.sent = 0
        self.alpha_set = [[float(alpha_t),float(alpha_t)],[float(alpha_t),float(alpha_t)],[float(alpha_t),float(alpha_t)]] #we chose 0.5 for 0.3
        self.alpha = self.alpha_set[int(float(load)/0.3) -1]
        self.t = 0
        self.t_track = 0
        self.np = [0]*self.ports 
        self.nqa = [0]*self.ports

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
                    packet = self.queues[port][(start+i)%len(self.queues[port])].get_nowait()
                    #print(packet)
                    for j in range(0,self.queues[port][(start+i)%len(self.queues[port])].qsize()+1):
                        if packet.invalid == 0:
                            #print("packetsent")
                            self.voq_rr[port] = (start+i+1)%len(self.queues[port])
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
                                self.voq_port_qsize[port-1][(start+i)%len(self.queues[port])]-=1
                            
                            

                            packet.prvt = 0
                            self.links[port].send(packet, self.addr, currTimeslot)
                            # print(f"sending packet from {i} when other prioritites have length = {self.voq_port_qsize[port-1]}")
                            # if i == 0:
                            #     breakpoint()
                            
                            self.sent+=1
                            
                            flag_1 = 1
                            try:
                                assert(self.port_qsize[port] >= 0)
                            except AssertionError:
                                print(f"Port {port} has negative queue size")
                                breakpoint()
                            break
                        else:
                            print("Invalid packet!!")

                    if flag_1 == 1:
                        
                        break


        for port in self.links.keys():  # in each timeslot, receive a
                                        # pa cket (if any) on each input
                                        # port and handle it
            packet = self.links[port].recv(self.addr, currTimeslot)
            if packet:
                self.handleRecvdPacket(port, packet, currTimeslot)
            else:
                self.final_add[port-1] = 0
        
        #if self.t > self.t_track:
        #    self.t_track+=200
        #    if self.addr == 't1':
        #        print(f"switch {self.addr}, usage = {self.total_usage}, total = {self.total_buffer_size}")
        #        print(f"Threshold output q - 0  = {self.T[0]}")
        #        print(f"Threshold output q - 1= {self.T[13]}")


        
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

    def threshold_calculate(self): # Threshold calculation for ABM - takes alpha into total alpha calculation only if the queue size is > 0 
        np = 0
        for n1 in range(self.ports):
            if self.port_qsize[n1+1] > 0.9*self.T[n1]:
                np+=1    
        if np == 0:
            np = 1
        for n1 in range(self.ports):
            self.T[n1] = self.alpha[1]*(self.total_buffer_size-self.total_usage)*(1/np)
            self.T_h[n1] = self.alpha[0]*(self.total_buffer_size-self.total_usage)*(1/np)
        
    

###############################################################################################################################################################

    def handleRecvdPacket(self, inPort, packet, arrivalTime):
        """Handle the packet received on the specified input port 'inPort'.
           arrivalTime is the timeslot in which the packet was received"""
        outPort = self.getOutPort(self.addr, packet)  # output port the packet needs to be sent out on
        
################################################################################ BIT MAPPER ########################################################################################
        if self.per_port_buffer[outPort-1] == 0:
            self.per_port_buffer[outPort-1] = 1
            # we have to introduce a new field for packet.py
            packet.prvt = 1
            self.queues[outPort][inPort-1].put(packet)
        elif self.total_buffer_size > self.total_usage:
            
            # self.queues[outPort][inPort-1].put(packet)  # add packet to the right VOQ at the output port
            # self.queues have their keys same as the keys for the links but the sublist has its index starting from 0, so does self.port_qsize (first index only)
            # self.voq_port_qsize have their indices starting from 0 (because it doesnt use the keys from the links)
            
            if (self.port_qsize[outPort] < self.T[outPort-1] and packet.priority != 1) or (self.port_qsize[outPort] < self.T_h[outPort-1] and packet.priority == 1):
                self.final_add[inPort-1] = 1
                self.total_usage += 1
                self.queues[outPort][inPort-1].put(packet)
                self.port_qsize[outPort] += 1
                self.voq_port_qsize[outPort-1][inPort-1]+= 1
                self.setECNFlag(packet, outPort)
               
            else:
                self.final_add[inPort-1] = 0
                self.packet_dropped += 1
                pass
            
        else:
            self.final_add[inPort-1] = 0
            print("Packet drop due to space constraint")
            self.packet_dropped += 1
            pass
        
        
        self.threshold_calculate()
        #print(f"{self.T}/{self.total_buffer_size}")
        
                
            
            
####################################################################################################################################################################################
                


