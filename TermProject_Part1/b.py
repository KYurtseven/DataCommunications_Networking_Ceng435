#!/usr/bin/env python
from socket import *
from threading import Thread
import datetime

# Broker TCP interface & port number
# where source is listened from
TCP_IP = '10.10.1.2'
TCP_PORT = 10012

#Broker UDP interface & port number
# where source is binded to r1 & r2 from
SRC_UDP_IP_ADDRESS = ['10.10.2.1','10.10.4.1']
SRC_UDP_PORT_NOS = [10021, 10041]


# Routers' UDP interfaces
# where source is connected to r1 & r2 and messages is sent to r1 & r2 from
DEST_UDP_IP_ADDRESS = ['10.10.2.2','10.10.4.2']
DEST_UDP_PORT_NOS = [10022, 10042]


# b will send ack messages to s's interfaces and ports
# s will listen those interfaces and ports 
SEND_ACK_DEST_UDP_IP = ['10.10.1.1', '10.10.1.1']
SEND_ACK_DEST_UDP_PORT =[20001, 20002]

# b will send ack messages from these interfaces and ports
SEND_ACK_SRC_UDP_IP = ['10.10.1.2', '10.10.1.2']
SEND_ACK_SRC_UDP_PORT = [20001, 20002]

# b will listen ack messages from these interfaces and ports
RECV_ACK_SRC_UDP_IP = ['10.10.2.1', '10.10.4.1']
RECV_ACK_SRC_UDP_PORT = [20001, 20002]

# we will packet the stream with this size of bytes
PACKET_SIZE = 128

ACK_SIZE = 128





def udp_connection(req, destip, destport, srcip, srcport):
	'''
	destip = brokers udp connection ip
	destport = brokers udp connection port

	srcip = routers ip
	srcport = router port
	req is the data to be transmitted
	'''

	# create a UDP socket
	s = socket(AF_INET, SOCK_DGRAM)
	# bind this IP and Port to the this socket
	s.bind((srcip, srcport))
	# send packet to the destination
	s.sendto(req,(destip, destport))
	# close the connection
	s.close()		

def recvPacket(sock):
	# store incoming messages in bytearray
	buff = bytearray()
	# the size of the aray is PACKET_SIZE
	# initially all of the array is empty
	left = PACKET_SIZE

	while left:
		# receive data from socket
		data = sock.recv(left)
		if(not data):
			# if there is no data incoming send the buffer
			return buff
		# append data to buff
		buff += data
		left = left - len(data)
	# if PACKET_SIZE byte is received return the data
	return buff

def udp_service(sock):    

	counter = 0

	while True:
		# To have exactly PACKET_SIZE bytes
		# use the recvPacket function
		req = recvPacket(sock)
		if(len(req) == PACKET_SIZE or len(req) > 0):
			# this means the data is received fully
			# or we have received partially
			# since we have the data, send it

			'''
			For each packet, create a thread
			and send the data from there
			'''
			

			udp_to_r1 = Thread(target = udp_connection, args = (req, DEST_UDP_IP_ADDRESS[0], DEST_UDP_PORT_NOS[0], SRC_UDP_IP_ADDRESS[0], SRC_UDP_PORT_NOS[0]))
			udp_to_r2 = Thread(target = udp_connection, args = (req, DEST_UDP_IP_ADDRESS[1], DEST_UDP_PORT_NOS[1], SRC_UDP_IP_ADDRESS[1], SRC_UDP_PORT_NOS[1]))

			udp_to_r1.start()
			udp_to_r2.start()

			udp_to_r1.join()
			udp_to_r2.join()

		else:
			print "TCP connection will be closed"
			sock.close() 
			break
	

def udp_receiver_for_ack(name):

	print "Thread created for sending ack messages to " , name
	# create a socket for listening ack messages
	udp_receiver = socket(AF_INET, SOCK_DGRAM)

	# b will listen r1's messages from interface 10.10.2.1 and port 20001
	# b will listen r2's messages from interface 10.10.4.1 and port 20002
	if(name == "r1"):
		udp_receiver.bind((RECV_ACK_SRC_UDP_IP[0], RECV_ACK_SRC_UDP_PORT[0]))
	else:
		udp_receiver.bind((RECV_ACK_SRC_UDP_IP[1], RECV_ACK_SRC_UDP_PORT[1]))

	udp_sender = socket(AF_INET, SOCK_DGRAM)
	
	# b will send ack message to s
	if(name == "r1"):
		udp_sender.bind((SEND_ACK_SRC_UDP_IP[0], SEND_ACK_SRC_UDP_PORT[0]))
	else:
		udp_sender.bind((SEND_ACK_SRC_UDP_IP[1], SEND_ACK_SRC_UDP_PORT[1]))
	counter = 0
	try:
		while True:
			#While ACK data exists, UDP reciever continues to listen for ACK data
			#When incoming data from the related path (name,port,ip) is finished which restricted with 30 sec,
			#Timeout exception occurs and UDP connection closes.
			udp_receiver.settimeout(30)
			data, addr = udp_receiver.recvfrom(ACK_SIZE)
			udp_receiver.settimeout(None)
			if(data and data != ''):

				# b will send the data to s with destport
				# r1's data will be send to port 20001 of s
				# r2's data will be send to port 20002 of s
				if(name == "r1"):
					udp_sender.sendto(data, (SEND_ACK_DEST_UDP_IP[0], SEND_ACK_DEST_UDP_PORT[0]))
				else:
					udp_sender.sendto(data, (SEND_ACK_DEST_UDP_IP[1], SEND_ACK_DEST_UDP_PORT[1]))
			
			else:
				udp_receiver.close()
				udp_sender.close()
				break
	except timeout:
		#When timeout exception occurs print closing warning and close sockets
		print "{} ACK UDP connection will be closed".format(name)
		udp_receiver.close()
		udp_sender.close()

def tcpserver(ip, port):
	'''
	Broker will receive connections and pass this connection
	to udp service.
	Broker will continue to listen the same TCP port. It is not
	required to do so, since we have only one connection (s). We have
	implemented this because the implementation seems better with this
	approach
	'''
	s = socket(AF_INET, SOCK_STREAM)
	s.bind((ip, port))
	print "TCP connection is listening"
	s.listen(1)

	# To avoid infinite loop for waiting a connection
	# we have set a timeout 
	
	# start accepting connection for 30 sec
	try:
		while True:
			s.settimeout(30)
			ns, peer = s.accept()
			s.settimeout(None)
			# we have a new connection, in this case it is (s)
			print "Peer{} is connected to broker tcp\t".format(peer)

			# create a new thread that serves s's requests
			clientThread = Thread(target = udp_service, args = (ns, ))
			clientThread.start()
			clientThread.join()
	except timeout:
		# close the connection
		print "Closing TCP connections"
		s.close()
def main():
	
	# make two threads for receiving ack signals from d
	# both will have different interfaces and ports
	#ack_receiver_r1 = Thread(target = udp_receiver_for_ack, args = (SRC_UDP_IP_ADDRESS[0], ACK_SRC_DEST_PORT_NOS[0], "r1", ACK_SRC_DEST_IP_ADDRESS[0], ACK_SRC_DEST_PORT_NOS[0]))
	#ack_receiver r2 = Thread(target = udp_receiver_for_ack, args = (SRC_UDP_IP_ADDRESS[1], ACK_SRC_DEST_PORT_NOS[1], "r2", ACK_SRC_DEST_IP_ADDRESS[1], ACK_SRC_DEST_PORT_NOS[1]))

	ack_receiver_r1 = Thread(target = udp_receiver_for_ack, args = ("r1",))
	ack_receiver_r2 = Thread(target = udp_receiver_for_ack, args = ("r2",))


	ack_receiver_r1.start()
	ack_receiver_r2.start()

	# create a thread for TCP connection
	tcp = Thread(target = tcpserver, args= (TCP_IP, TCP_PORT))

	tcp.start()

	ack_receiver_r1.join()
	ack_receiver_r2.join()
	tcp.join()
	

if __name__ == '__main__':
    main()