#!/usr/bin/env python

# create the file
file = open("sensor.txt", "w")

# create data
data = ""
for i in range(1024*10):
	data += str(1)
	if((i + 1) % 1024 == 0):
		file.write(data)
		data = ""

