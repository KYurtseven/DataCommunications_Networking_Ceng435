#!/usr/bin/env python
from socket import *
from threading import Thread
import datetime
import json
# d listens these connections
UDP_IP_ADDRESS_R1 = '10.10.3.2'
UDP_PORT_NO_R1 = 10032

UDP_IP_ADDRESS_R2 = '10.10.5.2'
UDP_PORT_NO_R2 = 10052

# d will send ack messages to r1 and r2
SEND_ACK_DEST_IP = ['10.10.3.1', '10.10.5.1']
SEND_ACK_DEST_PORT = [20001, 20002]

# d will send ack messages from these interfaces and ports
SEND_ACK_SRC_IP = ['10.10.3.2', '10.10.5.2']
SEND_ACK_SRC_PORT = [20001, 20002]

PACKET_SIZE = 128


# These are for measuring time
epoch = datetime.datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return int((dt - epoch).total_seconds() * 1000.0)




def server(ip, port, name):

	# d will listen sockets for data

	data_receiver = socket(AF_INET,SOCK_DGRAM)
	data_receiver.bind((ip,port))

	acksocket = socket(AF_INET, SOCK_DGRAM)
	
	if(name == "r1"):
		acksocket.bind((SEND_ACK_SRC_IP[0], SEND_ACK_SRC_PORT[0]))
	else:
		acksocket.bind((SEND_ACK_SRC_IP[1], SEND_ACK_SRC_PORT[1]))			
	
	message_count = 0
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
				
				print "Received message from {} is {} | Packet No : {} ".format(name, int(json.loads(data)['data']), int(json.loads(data)['number']) )

				#Calculate current time to feedback data
				cur_time = unix_time_millis(datetime.datetime.utcnow())
				#Create ACK data object 
				ack_data = {}
				ack_data['number'] = json.loads(data)['number']
				ack_data['data'] = str(cur_time)
				#Convert to json to send
				ack_data = json.dumps(ack_data)

			
				#Send feedback to where it originated
				if(name == "r1"):
					acksocket.sendto(ack_data, (SEND_ACK_DEST_IP[0], SEND_ACK_DEST_PORT[0]))
				else:
					acksocket.sendto(ack_data, (SEND_ACK_DEST_IP[1], SEND_ACK_DEST_PORT[1]))

			else:
				#If fata is NULL
				print "Closing connections"
				acksocket.close()
				data_receiver.close()

				break
	except timeout:
		#When timeout exception occurs print closing warning and close sockets
		print "{} ACK UDP connection will be closed".format(name)
		acksocket.close()
		data_receiver.close()


def main():

	# receive data from r1 and r2
	serverR1 = Thread(target = server,args = (UDP_IP_ADDRESS_R1, UDP_PORT_NO_R1, "r1"))
	serverR2 = Thread(target = server,args = (UDP_IP_ADDRESS_R2, UDP_PORT_NO_R2, "r2"))

	serverR1.start()
	serverR2.start()

	serverR1.join()
	serverR2.join()


if __name__ == '__main__':
    main()