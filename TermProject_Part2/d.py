#!/usr/bin/env python
from socket import *
from threading import Thread
import os
import md5
from time import sleep
# D's interface
D_R1_INTERFACE = '10.10.3.2'
D_R2_INTERFACE = '10.10.5.2'

# B's interface
B_R1_INTERFACE = '10.10.2.1'
B_R2_INTERFACE = '10.10.4.1'

# Ports
DATA_PORT = 10000
ACK_PORT = 20000

# received packet size
PACKET_SIZE = 272

# store incoming packets in this array
BUFFER = 20000 * ['']

# global flags for notifying main thread to write to the file
R1_FINISHED = False
R2_FINISHED = False

def server(ip, port, name):

	# d will listen sockets for data

	data_receiver = socket(AF_INET,SOCK_DGRAM)
	data_receiver.bind((ip,port))

	# create socket for sending ack/nack messages
	acksocket = socket(AF_INET, SOCK_DGRAM)

	if(name == "r1"):
		acksocket.bind((D_R1_INTERFACE, ACK_PORT))
	else:
		acksocket.bind((D_R2_INTERFACE, ACK_PORT))			
	
	print name + "is started listening"
	global BUFFER, R1_FINISHED, R2_FINISHED

	# if seq number of packet is equal to this, accept the packet
	ctr = 0
	if(name == "r1"):
		ctr = 0
	else:
		ctr = 1

	try:
		while True:
			data_receiver.settimeout(40)
			data, addr = data_receiver.recvfrom(PACKET_SIZE)
			data_receiver.settimeout(None)
			if(data and data != ''):
				try:
					# [0:250] data
					# [250:256] counter
					# [256:272] checksum
					m = md5.new()
					newd = data[0:250]
					seqn = data[250:256]
					payload = newd + seqn
					m.update(payload)
					c1 = m.digest()
					c2 = data[256:272]

					if(c1 == c2):
						# data is not corrupted
						# check the sequence number
						if(ctr == int(seqn)):
							# accept if it is expected value
							print "Received message from {} | Packet No : {} ".format(name, ctr)
							
							d = {}
							d['number'] = int(seqn)
							d['data'] = newd

							# fb[0:3] gives message
							# fb[3:9] gives packet number
							# fb[9:25] gives checksum
							feedback = "ACK"
							feedback += seqn

							m2 = md5.new()
							m2.update(feedback)
							cf = m2.digest()
							feedback += cf

							if BUFFER[int(seqn)] == '':
								BUFFER[int(seqn)] = d
								ctr += 2
							else:
								print "\tDuplicate data occured, number ", int(seqn)

							#Send feedback to where it originated
							if(name == "r1"):
								acksocket.sendto(feedback, (B_R1_INTERFACE, ACK_PORT))
							else:
								acksocket.sendto(feedback, (B_R2_INTERFACE, ACK_PORT))
						
						elif(int(seqn) < ctr):
							print "send prev packets ACK", int(seqn) 
							# or, previous values should be acked too

							# fb[0:3] gives message
							# fb[3:9] gives packet number
							# fb[9:25] gives checksum
							feedback = "ACK"
							feedback += seqn

							m2 = md5.new()
							m2.update(feedback)
							cf = m2.digest()
							feedback += cf

							#Send feedback to where it originated
							if(name == "r1"):
								acksocket.sendto(feedback, (B_R1_INTERFACE, ACK_PORT))
							else:
								acksocket.sendto(feedback, (B_R2_INTERFACE, ACK_PORT))

						# otherwise, the correct one will be sent from b
				except Exception as e:
					# do nothing, timer in b will handle retransmission
					print "\t\tCorruption error occured"
					print "\t\texception", e.message, e.args
					# b will retransmit
			else:
				print "\t\tData is null, ", name
	except timeout:
		#When timeout exception occurs print closing warning and close sockets
		print "{} UDP connection will be closed".format(name)
		print "Details for the transmission are"
		print "Received paket: " + str(ctr)
	
	except Exception as e:
		print "HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
		print "name: ", name
		print "exception", e.message, e.args

	# signal main thread for writing to the file
	if name == "r1":
		R1_FINISHED = True
	else:
		R2_FINISHED = True
	data_receiver.close()

def main():

	# receive data from r1 and r2
	serverR1 = Thread(target = server,args = (D_R1_INTERFACE, DATA_PORT, "r1"))
	serverR2 = Thread(target = server,args = (D_R2_INTERFACE, DATA_PORT, "r2"))

	serverR1.start()
	serverR2.start()

	global R1_FINISHED, R2_FINISHED, BUFFER

	while True:
		# at every 1000ms
		sleep(1)
		if(R1_FINISHED and R2_FINISHED):
			break

	isCorrect = True
	try:

		for i in range(len(BUFFER)):
			if i != int(BUFFER[i]['number']): 
				print "not equal"
				print i, BUFFER[i]
				isCorrect = False
	except:
		isCorrect = False
		print "Buffer's this element is empty: ", i

	if isCorrect:
		print "File is transmitted correctly"

		# remove the transmitted file if it exists
		if os.path.exists("received.txt"):
			print "remove existing file"
			os.remove("received.txt")

		file = open("received.txt", "w")
		for i in range(len(BUFFER)):
			curdata = BUFFER[i]['data']
			file.write(curdata)

		print "TODO"
		print "Writing to the received.txt is completed"
		file.close()

	else:
		print "We have errors in the file"

	serverR1.join()
	serverR2.join()
	
if __name__ == '__main__':
    main()
