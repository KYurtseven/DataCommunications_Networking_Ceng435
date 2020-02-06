#!/usr/bin/env python
from socket import *
from threading import Thread
import datetime

PACKET_SIZE = 128
ACK_SIZE = 128


def udp_receiver_for_ack():

	print "Thread for receiving ACK messages from d is created"
	'''
	Receive ack messages from d and will send to broker
	ACK messages will be received from udp_receiver socket
	ACK messages will be sent to udp_sender socket
	'''

	# ACK messages will be received from this interface and port
	RECV_ACK_SRC_UDP_IP = '10.10.3.1'
	RECV_ACK_SRC_UDP_PORT = 20001

	# ACK messages will be send to this interface and port
	SEND_ACK_DEST_UDP_IP = '10.10.2.1'
	SEND_ACK_DEST_UDP_PORT = 20001

	# We will send ACK messages from this interface and port
	SEND_ACK_SRC_UDP_IP = '10.10.2.2'
	SEND_ACK_SRC_UDP_PORT = 20001


	udp_receiver = socket(AF_INET, SOCK_DGRAM)
	udp_receiver.bind((RECV_ACK_SRC_UDP_IP, RECV_ACK_SRC_UDP_PORT))

	udp_sender = socket(AF_INET, SOCK_DGRAM)
	udp_sender.bind((SEND_ACK_SRC_UDP_IP, SEND_ACK_SRC_UDP_PORT))
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
				#Forward ACK data to 'b'
				udp_sender.sendto(data, (SEND_ACK_DEST_UDP_IP, SEND_ACK_DEST_UDP_PORT))
			else:
				#If data is null
				print "Closing ACK data connection"
				udp_receiver.close()
				udp_sender.close()
				break
	except timeout:
		#When timeout exception occurs print closing warning and close sockets
		print "ACK UDP connection will be closed"
		udp_receiver.close()
		udp_sender.close()


def udpserver():

	# r1 listens this connection
	RECV_UDP_IP = '10.10.2.2'
	RECV_UDP_PORT = 10022

	# r1 sends the data to that connection (d)
	SEND_DEST_UDP_IP = '10.10.3.2'
	SEND_DEST_UDP_PORT = 10032

	# r1's udp send address is this
	SEND_SRC_UDP_IP = '10.10.3.1'
	SEND_SRC_UDP_PORT = 10031

	# create socket for listening udp connection from broker
	data_receiver = socket(AF_INET, SOCK_DGRAM)
	data_receiver.bind((RECV_UDP_IP, RECV_UDP_PORT))

	# create socket for sending the data to d
	data_sender = socket(AF_INET, SOCK_DGRAM)
	# bind r1's sending interface to this socket
	data_sender.bind((SEND_SRC_UDP_IP, SEND_SRC_UDP_PORT))

	counter = 0
	try:
		while True:
			#While data exists, UDP reciever continues to listen for data
			#When incoming data from the related path (name,port,ip) is finished which restricted with 30 sec,
			#Timeout exception occurs and UDP connection closes.
			data_receiver.settimeout(30)
			data, addr = data_receiver.recvfrom(PACKET_SIZE)
			data_receiver.settimeout(None)
			if(data and data != ''):
				#Forword data to 'd'
				data_sender.sendto(data, (SEND_DEST_UDP_IP, SEND_DEST_UDP_PORT))
			else:
				#If fata is NULL
				data_receiver.close()
				data_sender.close()
				break
	except timeout:
		#When timeout exception occurs print closing warning and close sockets
		print "UDP connection will be closed"
		data_receiver.close()
		data_sender.close()

def main():
	
	# Create thread for receiving ACK messages and send to the broker
	ack_receiver = Thread(target = udp_receiver_for_ack, args = ())
	
	ack_receiver.start()
	
	# Create thread for receiving data from broker and send it to destination
	udp = Thread(target = udpserver, args= ())

	udp.start()

	ack_receiver.join()
	udp.join()
	

if __name__ == '__main__':
    main()