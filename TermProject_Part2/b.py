#!/usr/bin/env python
from socket import *
from threading import Thread, Lock, Condition
import datetime
from time import sleep
import md5

S_DATA_INTERFACE = '10.10.1.1'
DATA_PORT = 10000
ACK_PORT = 20000

# B's interface to s
B_DATA_INTERFACE = '10.10.1.2'

# destination interfaces
D_R1_INTERFACE = '10.10.3.2'
D_R2_INTERFACE = '10.10.5.2'

# b's interface
B_R1_INTERFACE = '10.10.2.1'
B_R2_INTERFACE = '10.10.4.1'

# receive 500 bytes from s
# divide into two and packetize
DATA_SIZE = 500

# ack size
ACK_SIZE = 25

# SHARED VARIABLES

# mutex for protecting shared variables
MUTEX = Lock()
BUFFER_FULL = False
C_BUFFER_FULL = Condition(MUTEX)

# BUFFER_DATA will be used for retransmiting the original data
BUFFER_DATA = []
# TCP_SENT will be used for retrx, time calculation etc.
TCP_SENT = []
# initial start and end values
START = 0
END = 16
# END OF SHARED VARIABLES

# constant window size
WINDOW_SIZE = 16

# if send count exceeds window size, stop until receiving ACK
SEND_COUNT = 0
# counter for packet numbers
COUNTER = 0

# global flags for feedback state
R1_FINISHED = False 
R2_FINISHED = False

# if no error in our buffer, all ack, we can do calculations
FILE_FINISHED = False

# These are for measuring time
epoch = datetime.datetime.utcfromtimestamp(0)

def cur_time():
	dt = datetime.datetime.utcnow()
	return int((dt - epoch).total_seconds() * 1000.0)

def packetize(message, counter):
	#For read chunk data pad the counter for proper size
	dc = ""
	if counter < 10:
		dc = "00000" + str(counter)
	elif counter<100:
		dc = "0000" + str(counter)
	elif counter <1000:
		dc = "000" + str(counter)
	elif counter < 10000:
		dc = "00" + str(counter)
	elif counter < 100000:
		dc = "0" + str(counter)
	else:
		dc = str(counter)

	# [0:250] data
	# [250:256] counter
	# [256:272] checksum
	payload = ""
	payload += message
	payload += dc
	m = md5.new()
	m.update(payload)
	c = m.digest()
	payload += c

	return payload, int(dc)

def recvExactly(sock):
	# store incoming messages in bytearray
	buff = bytearray()
	# the size of the aray is DATA_SIZE
	# initially all of the array is empty
	left = DATA_SIZE

	while left:
		# receive data from socket
		data = sock.recv(left)
		if(not data):
			# if there is no data incoming send the buffer
			return buff
		# append data to buff
		buff += data
		left = left - len(data)
	# if DATA_SIZE byte is received return the data
	return buff


def retransmission(d1, d2):

	global BUFFER_DATA, TCP_SENT, WINDOW_SIZE
	
	try:
		for i in range(WINDOW_SIZE):
			cur = TCP_SENT[START + i]
			if cur['type'] == "ACK":
				continue
	
			elif cur['type'] == "SEND":
				# look at time difference between sent and current
				c = cur_time() - cur['senttime']
				# 500 ms
				if c > 500:
					payload = BUFFER_DATA[START + i]

					cur['type'] = "RESEND"

					# store them globally   
					cur['resenttime'] = cur_time()

					n = int(cur['number'])
					if (n%2) == 0:
						d1.sendto(payload,(D_R1_INTERFACE, DATA_PORT))
					else:
						d2.sendto(payload,(D_R2_INTERFACE, DATA_PORT))
				else:
					pass
			elif cur['type'] == "RESEND":
				# look at the time difference between last send and current
				c = cur_time() - cur['resenttime']
				# 500 ms
				if c > 500:
					payload = BUFFER_DATA[START + i]
					cur['type'] = "RESEND"

					# store them globally   
					cur['resenttime'] = cur_time()
					n = int(cur['number'])

					if (n%2) == 0:
						d1.sendto(payload,(D_R1_INTERFACE, DATA_PORT))
					else:
						d2.sendto(payload,(D_R2_INTERFACE, DATA_PORT))
				else:
					pass
	except:
		# index error occured because we are trying to reach out of index
		# do nothing
		return

def send_msg(d1, d2, msg):

	global BUFFER_DATA, TCP_SENT, SEND_COUNT, COUNTER

	# divide packets into two
	ms1 = msg[0:250]
	ms2 = msg[250:500]

	payload1, n1 = packetize(ms1, COUNTER)
	COUNTER += 1
	payload2, n2 = packetize(ms2, COUNTER)
	COUNTER += 1

	# append it to buffers
	# The buffer data contains our messages to be sent
	# we manupulate times and types in TCP_SENT buffer
	# in this way, when a timeout occurs, i.e. checking the senttime of the packet
	# we can immediately send the BUFFER_DATA[n], without preparing it again
	BUFFER_DATA.append(payload1)
	BUFFER_DATA.append(payload2)

	tcp_senddata1 = {}
	tcp_senddata1['data'] = payload1
	tcp_senddata1['type'] = "SEND"
	tcp_senddata1['senttime'] = cur_time()
	tcp_senddata1['number'] = n1

	tcp_senddata2 = {}
	tcp_senddata2['data'] = payload2
	tcp_senddata2['type'] = "SEND"
	tcp_senddata2['senttime'] = cur_time()
	tcp_senddata2['number'] = n2
	
	TCP_SENT.append(tcp_senddata1)
	TCP_SENT.append(tcp_senddata2)

	d1.sendto(payload1,(D_R1_INTERFACE, DATA_PORT))
	d2.sendto(payload2,(D_R2_INTERFACE, DATA_PORT))
	SEND_COUNT += 2


def file_receiver(sock):

	# sockets for sending message to D through R1 and R2
	d1 = socket(AF_INET, SOCK_DGRAM)
	d1.bind((B_R1_INTERFACE, DATA_PORT))

	d2 = socket(AF_INET, SOCK_DGRAM)
	d2.bind((B_R2_INTERFACE, DATA_PORT))

	# Global shared variables
	global BUFFER_DATA, TCP_SENT, BUFFER_FULL
	global WINDOW_SIZE, START, END, SEND_COUNT
	global FILE_FINISHED
	
	isFinished = False

	MUTEX.acquire()

	while True:

		# I can take this many element
		empty = WINDOW_SIZE - SEND_COUNT
		for i in range(empty / 2):

			msg = recvExactly(sock)

			# send immeditely incoming message
			if(len(msg) == DATA_SIZE or len(msg) > 0):
				send_msg(d1, d2, msg)

			else:
				print "No more data is coming from s"
				print "Close receiving connection"
				isFinished = True
				break

		if isFinished:
			break
		
		if SEND_COUNT >= WINDOW_SIZE:
			BUFFER_FULL = True

		# wait till buffer is empty
		while BUFFER_FULL:

			retransmission(d1, d2)
			# will release mutex
			C_BUFFER_FULL.wait()
			# will take mutex

			# if the first two packet is sent
			# we can move the window and receive more messages
			if TCP_SENT[START]['type'] == "ACK":
				if TCP_SENT[START + 1]['type'] == "ACK":
					START = START + 2
					END = END + 2

					SEND_COUNT -= 2
					BUFFER_FULL = False

		# try to move window for possible remaining ACK in the buffer
		while True:
			if START >= len(TCP_SENT):
				break
			# advance two at once
			# in this way, we can receive a packet, divide it into two
			# and add it to the Buffer

			if TCP_SENT[START]['type'] == "ACK":
				if TCP_SENT[START + 1]['type'] == "ACK":
					START = START + 2
					END = END + 2
					SEND_COUNT -= 2
				else:
					break
			else:
				break

	MUTEX.release()
	print "SOCK CLOSED"
	# close s connection
	sock.close()

	print "Retransmit remaining items"

	MUTEX.acquire()

	while True:
		fin = True
		for i in range(len(TCP_SENT)):
			if(TCP_SENT[i]['type'] != "ACK"):
				#print TCP_SENT[i]
				fin = False
				break
		if fin:
			# everything is transferred
			# we can peacefully exit
			break

		retransmission(d1, d2)

		C_BUFFER_FULL.wait()
		
	MUTEX.release()
	
	# send main thread that it can calculate file transfer time
	FILE_FINISHED = True
	

	d1.close()
	d2.close()


def feedback_receiver(name):

	print "Thread created for sending ack messages to " , name
	# create a socket for listening ack messages
	udp_receiver = socket(AF_INET, SOCK_DGRAM)

	# b will listen r1's and r2's messages
	if(name == "r1"):
		udp_receiver.bind((B_R1_INTERFACE, ACK_PORT))
	else:
		udp_receiver.bind((B_R2_INTERFACE, ACK_PORT))

	try:
		while True:
			#While feedback exists, UDP reciever continues to listen for feedback
			#When incoming data from the related path (name,port,ip) is finished which restricted with 40 sec,
			#Timeout exception occurs and UDP connection closes.
			udp_receiver.settimeout(40)
			fb, addr = udp_receiver.recvfrom(ACK_SIZE)
			udp_receiver.settimeout(None)
			MUTEX.acquire()

			if(fb and fb != ''):
				global TCP_SENT, WINDOW_SIZE, BUFFER_FULL
				try:
					# fb[0:3] gives message
					# fb[3:9] gives packet number
					# fb[9:25] gives checksum
					t = fb[0:3]
					seqn = fb[3:9]
					m = md5.new()
					# feedbacks payload, message + paket number
					fpay = t + seqn
					m.update(fpay)
					c1 = m.digest()
					c2 = fb[9:25]

					if(c1 == c2):
						#print "checksums are equal"
						# feedback is not corrupted
						if t == "ACK":
							#print "message is ACK"
							if(TCP_SENT[int(seqn)]['type'] == "SEND" or TCP_SENT[int(seqn)]['type'] == "RESEND"):
								print "ACKED", int(seqn)
								TCP_SENT[int(seqn)]['type'] = "ACK"
								C_BUFFER_FULL.notify()

							# else, duplicate ack
							# do nothing

					else:
						print "\tNot equal checksum"
						# else, do nothing, not equal checksum
						# timer will handle retransmission

				except Exception as e:
					# cannot read feedback
					print "\tCorruption", e.message, e.args
			
			else:
				print 100*"-"
				print "\tFeedback is Null"
				# do nothing, timer will handle it

			MUTEX.release()

	except timeout:
		#When timeout exception occurs print closing warning and close sockets
		print "{} ACK UDP connection will be closed".format(name)
		global R1_FINISHED, R2_FINISHED
		
		if(name == "r1"):
			R1_FINISHED = True
		else:
			R2_FINISHED = True
		
		udp_receiver.close()


def tcp_server():
		
	# socket for receiving data from s
	s = socket(AF_INET, SOCK_STREAM)
	s.bind((B_DATA_INTERFACE, DATA_PORT))

	print "TCP connection is listening"
	# Wait for s connection
	s.listen(1)

	try:
		while(True):
			s.settimeout(10)
			ns, peer = s.accept()
			s.settimeout(None)

			print "Peer{} is connected to broker tcp\t".format(peer)

			# create a new thread that serves s's requests
			clientThread = Thread(target = file_receiver, args = (ns, ))
			clientThread.start()
			clientThread.join()


	except timeout:
		print "Timeout exception"

	s.close()
	
def main():
	
	fc_r1 = Thread(target = feedback_receiver, args = ("r1",))
	fc_r2 = Thread(target = feedback_receiver, args = ("r2",))

	fc_r1.start()
	fc_r2.start()

	# create a thread for TCP connection
	tcp = Thread(target = tcp_server, args= ())

	tcp.start()

	global R1_FINISHED, R2_FINISHED, FILE_FINISHED, START, END
	
	# for waking up the sender
	# sometimes all of the packets might have been dropped
	# in that case feedback_receiver cannot notify the sender thread
	# notify sender thread from here periodically
	while True:
		# at every 200ms
		# incase all of packets are acked but only one is not acked
		# the feedback receiver might not receive an ack, it might lost
		# to wait for infinity, at every 200ms
		# wake the sender, look at the type of the packets
		# retransmit if necessary
		sleep(0.2)
		MUTEX.acquire()
		C_BUFFER_FULL.notify()
		MUTEX.release()
		
		if(R1_FINISHED and R2_FINISHED and FILE_FINISHED):
			print "All of them has finished"
			break

	timecalculations()

	fc_r1.join()
	fc_r2.join()
	
	tcp.join()

def timecalculations():

	global BUFFER_DATA

	print "Starting experiment calculations"
	# we are using senttime to calculate file transfer time
	# because the previous implementation showed us that there is very very little difference
	# between last packets receive time and sent time, compared to the whole transfer time
	# also, by removing received time in the feedback packet, we have gained more space
	# in the wire 
	t0 = TCP_SENT[0]['senttime']
	
	print "last packet"
	print TCP_SENT[-1]
	t1 = TCP_SENT[-1]['senttime']

	dif = t1-t0
	print "dif: ", dif

if __name__ == '__main__':
    main()
