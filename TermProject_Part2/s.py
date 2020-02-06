#!/usr/bin/env python
from socket import *
from threading import Thread, Lock, Condition
import datetime
import json
import copy

S_DATA_INTERFACE = '10.10.1.1'

B_DATA_INTERFACE = '10.10.1.2'

DATA_PORT = 10000

def file_sender():

	s = socket(AF_INET, SOCK_STREAM)

	# Binding new socket to interface of source
	s.bind((S_DATA_INTERFACE,DATA_PORT))
	# Connect to the broker
	s.connect((B_DATA_INTERFACE, DATA_PORT))

	file1 = open("input.txt", "rb")
	arr = file1.readlines()
	buff = ""
	for i in range(len(arr)):
		buff += arr[i]
		
	counter = 0
	try:
		#while True:
		# send 10k equal size packets, each is 500byte
		n = 500
		arr2 = [buff[i:i+n] for i in range(0, len(buff), n)]
		
		for i in range(10000):
			counter += 1
			s.send(arr2[i])
			print "send ", counter, len(arr2[i])
			
		#Information about sent messages
		print "{} messages were sent successfully.".format(counter)
		print "\n"
		s.close()

	except timeout:
		print("timeout")
		s.close()

	file1.close()

	
def main():

	# start sending the file
	fs = Thread(target = file_sender, args = ())
	fs.start()

	fs.join()

if __name__ == '__main__':
    main()
