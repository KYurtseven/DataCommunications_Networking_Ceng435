#!/usr/bin/env python
from socket import *
from threading import Thread
import datetime
import json


#interface & port number of source, 
#where 's' is binded from
MY_IP = '10.10.1.1'
MY_PORT = 10011

#TCP connection interface & port number of source, 
#where 's' is connected to broker from 
TCP_IP = '10.10.1.2'
TCP_PORT = 10012

# s will listen those interface and ports for ACK messages
SRC_ACK_UDP_IP = ['10.10.1.1', '10.10.1.1']
SRC_ACK_UDP_PORT = [20001, 20002]

# flag for comminicating main thread; they will be set when their connection are closed
is_UDP_r1_finished = 0
is_UDP_r2_finished = 0
is_TCP_finished = 0


#ACK messages stored in reach TIMES and packet_NOs
r1_reach_TIMES = []
r2_reach_TIMES = []
r1_packet_NOs = []
r2_packet_NOs = []

#fist send times stored TCP_sent_TIMES
TCP_sent_TIMES = []

#TCP_sent_TIMES - r1_reach_TIMES for realted packet_NOs
r1_delay_TIMES = []
r2_delay_TIMES = []

#Size for recive ack data from b
ACK_SIZE = 128


# These are for measuring time
epoch = datetime.datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return int((dt - epoch).total_seconds() * 1000.0)



def udp_receiver_for_ack(name, ip, port):

	#name: for ACK data recieved path <- 'r1' or 'r2' 
	#ip and port: for ACK data recieved path interface and port number

	# create a socket for listening ack messages
	s = socket(AF_INET, SOCK_DGRAM)
	# b will listen r1's messages from interface 10.10.2.1 and port 20001
	# b will listen r2's messages from interface 10.10.4.1 and port 20002
	s.bind((ip, port))

	try:

		while True:
			#While ACK data exists, UDP reciever continues to listen for ACK data
			#When incoming data from the related path (name,port,ip) is finished which restricted with 30 sec,
			#Timeout exception occurs and UDP connection closes.
			s.settimeout(30)
			data, addr = s.recvfrom(ACK_SIZE)
			s.settimeout(None)
			if(data and data != ''):
				print "Received ACK message from {} is {} | Packet No : {} ".format(name, int(json.loads(data)['data']), int(json.loads(data)['number']) )
		
				#Take the ACK data from json Data as reach_time and packet_no
				#Which refer the reach time of the packet to 'd'
				reach_time = int(json.loads(data)['data'])
				packet_no = int(json.loads(data)['number'])
				
				#Check which thread is running and keep ACK data according to thread
				if(name == "r1"):
					
					global r1_reach_TIMES
					global r1_packet_NOs
					r1_reach_TIMES.append(reach_time)
					r1_packet_NOs.append(packet_no)

				else:
					
					global r2_reach_TIMES
					global r2_packet_NOs
					r2_reach_TIMES.append(reach_time)
					r2_packet_NOs.append(packet_no)
				# b will send the data to s with destport
				# r1's data will be send to port 20001 of s
				# r2's data will be send to port 20002 of s
			else:
				#When incoming data is NULL close socket
				s.close()
				break
	except timeout:
		#When timeout exception occurs print closing warning and close socket
		print "ACK data receiving task for {} is finished, closing ACK data connection.".format(name)
	
		
		s.close()

		if(name == "r1"):
			global is_UDP_r1_finished 
			is_UDP_r1_finished = 1
		else:
			global is_UDP_r2_finished 
			is_UDP_r2_finished = 1

def tcp_sender():

	#Creating new socket for TCP connection (STREAM)
	s = socket(AF_INET, SOCK_STREAM)

	#Binding new socket to interface of source
	s.bind((MY_IP,MY_PORT))

	#Connectig new socket to broker
	s.connect((TCP_IP, TCP_PORT))

	# open sensor file to read
	file = open("sensor.txt", "r")
	counter = 0
	while True:
		message = file.read(98)
		if not message:
			#We consumed the file
			break
		else:
			#For read chunk data pad the counter for proper size
			dc = ""
			if counter < 10:
				dc = "000" + str(counter)
			elif counter<99:
				dc = "00" + str(counter)
			elif counter <999:
				dc = "0" + str(counter)
			else:
				dc = str(counter)
			#Create json object
			data = {}
			data['number'] = dc
			data['data'] = message

			
			counter += 1 
			#Convert object to json
			senddata = json.dumps(data)
			
			#Calculate current time and store as send time
			cur_time = unix_time_millis(datetime.datetime.utcnow())
			TCP_sent_TIMES.append(cur_time)

			#Send the data
			s.send(senddata)


	#Information about sent messages
	print "{} messages were sent successfully.".format(counter)
	print "\n"	

	#Closing the TCP connection between source and broker
	s.close()
	#Set flag for main thread
	global is_TCP_finished
	is_TCP_finished = 1

def main():

	# make two threads for receiving ack signals from d
	# both will have different interfaces and ports
	ack_receiver_r1 = Thread(target = udp_receiver_for_ack, args = ("r1", SRC_ACK_UDP_IP[0], SRC_ACK_UDP_PORT[0]))
	ack_receiver_r2 = Thread(target = udp_receiver_for_ack, args = ("r2", SRC_ACK_UDP_IP[1], SRC_ACK_UDP_PORT[1]))

	ack_receiver_r1.start()
	ack_receiver_r2.start()
	
	tcp = Thread(target = tcp_sender, args = ())

	tcp.start()
	
	while True:
		#Check flags to determine if threads are finished or not
		if(is_UDP_r2_finished and is_UDP_r1_finished and is_TCP_finished):
			print "\n"
			print "Number of messages sent to broker : " , len(TCP_sent_TIMES)
			print "Number of messages reacehed to destination from r1 : " , len(r1_packet_NOs)
			print "Number of messages reacehed to destination from r2 : " , len(r2_packet_NOs)
			print "\n"
			print "Total packet lost for r1 : " , len(TCP_sent_TIMES) - len(r1_packet_NOs)
			print "Total packet lost for r2 : " , len(TCP_sent_TIMES) - len(r2_packet_NOs)
			print "\n"
			print "End-to-End Delays of {} reached messages from r1 :".format(len(r1_packet_NOs))
			
			#Calculate Delays for each message r1 
			for i in range (0, len(r1_packet_NOs)):
				packet = r1_packet_NOs[i]
				send_time = TCP_sent_TIMES[packet]
				reach_time = r1_reach_TIMES[i]
				delay_time = reach_time - send_time
				r1_delay_TIMES.append(delay_time)
				print "Packet No = {} | Delay = {} ".format(packet,delay_time)

			print "\n"
			print "End-to-End Delays of {} reached messages from r2 :".format(len(r2_packet_NOs))
			
			#Calculate Delays for each message r2
			for i in range (0, len(r2_packet_NOs)):
				packet = r2_packet_NOs[i]
				send_time = TCP_sent_TIMES[packet]
				reach_time = r2_reach_TIMES[i]
				delay_time = reach_time - send_time
				r2_delay_TIMES.append(delay_time)
				print "Packet No = {} | Delay = {} ".format(packet,delay_time)

			print"\n"
			print "Slope of delay on the path r1 is {} unit.".format((r1_delay_TIMES[-1] - r1_delay_TIMES[0]) / len(r1_delay_TIMES))
			print "Slope of delay on the path r2 is {} unit.".format((r2_delay_TIMES[-1] - r2_delay_TIMES[0]) / len(r2_delay_TIMES))
			print"\n"
			print "Total End-to-End delay of 'sensor.txt' from path r1 is {} ms.".format(r1_reach_TIMES[-1] - TCP_sent_TIMES[0])
			print "Total End-to-End delay of 'sensor.txt' from path r2 is {} ms.".format(r2_reach_TIMES[-1] - TCP_sent_TIMES[0])
			break

	ack_receiver_r1.join()
	ack_receiver_r2.join()
	tcp.join()

if __name__ == '__main__':
    main()