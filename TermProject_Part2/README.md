This work consists of implementation, reports and unsuccessful version of the second part of the project. While grading our work, please consider the Version3, Final.
We are putting all of our implementations in the submission folder, because we believe that it is best way to express our effort in this homework/project. These explanations and conclusions will be in the project report as well.


Koray Can YURTSEVEN, 2099547
Aykut YARDIM, 2110278

-----------------------------------------------------------------------------------------------

TO RUN
* Do routing configuration as it is specified in the report (b, r1, r2 and d's routing tables are changing) also in /Version3,Final/Reports/ directory
* For example by default packets are going over b-r2-d route. Delete 10.10.3.2 route in router r2 and add 10.10.3.2 configuration to b.

sudo    route    add    -net    10.10.3.0    netmask255.255.255.0 gw 10.10.2.2 dev eth2
This does: 10.10.3.* ip addresses are put into eth2 interface and goes to the gateway 10.10.2.2
 
* Place d.py and input.txt in d, b.py in b, s.py and input.txt in s
* run d, then b, then s.
* After the run is completed, in the d open python interpreter
	import filecmp
	filecmp.cmp('input.txt', 'received.txt')
	--->Returns true

* Report .pdf and .tex files are inside Version3,Final/Reports
* Figures we have used for pdf is inside Version3,Final/Reports
* Test results are under Version3,Final/results
-----------------------------------------------------------------------------------------------

In both 3 version, we have tried the similar approach.
S reads the file sends to b if the b has empty in its window.
B packetize this into two parts, dividing from middle and sends to d through routers r1 and r2.
When the d receives it, it sends ACK, PACKET NUMBER to back.
B shifts its window appropriately and loops until file transmission is completed

-----------------------------------------------------------------------------------------------

In the version1, we have done the following parameters:

We read the file by decoding into 'hex'. This caused our file size to increase two times.
	When we read 200 bytes, converting it to hex results is 400 bytes.
After sending 400 bytes, b divides this into 2 parts. The payload of our data consists of 200bytes.
In B, we declare a dictionary, put the payload inside, then add the packet number. The checksum calculation is similar to TCP checksum calculation and we calculate checksum only the data, not including the packet number.
	send data format:
	d['data'] = payload
	d['number'] sequence number
	d['checksum'] = checksum of the payload
After packetization, we send the data through routers, and the d will respond back in this format
	f['type'] = ACK or NACK
	f['number'] = sequence number of the received packet
	f['time'] = received time of the file/packet

We have observed that the send packet size is 256 byte and the received feedback packet size is 84 byte, which they add up to 340 byte. Since we have two links and both of them are 500kbits, in the full utilization we can send 128kbyte per second. We have specified the window size as 400 because 256 * 400 equals 102kbyte. The rest are reserved for feedback packets. Although, we believe that we can select a little less window size to achieve better results.


This implementation has bugs. These bugs are:
	1- The payload size is 200 bytes. Our checksum function returns 5 bytes. This causes mapping to same position/number even if the data are different.
	2- We did not protect the sequence number with checksum. In d, we have observed following patterns:
		a. The sequence number is corrupted but still a number. However, it is previously ACKED. We simply ignore that issue and wait for retransmision. This was not a big problem.
		b. The sequence number is corrupted and inserted in an empty position in the buffer of 'd'. Thus, incoming correct packet could not enter the buffer, because it was already data in there.
		c. Everything received correctly in d. While sending feedback packet to b, since the feedback is not protected by checksum, the feedback packet corrupts. If the feedback packet's seqn corrupts and is still a valid number in the b buffer, it may accidentaly ACK not send or resent packets.

-----------------------------------------------------------------------------------------------

In version 1.1, which we did not include in the submission folder, we have protected both payload and checksum number. However, we still have this kind of situation
	data['data'] = payload
	data['number'] = sequence number
	
	check = checksumfunction(data)
	data['checksum'] = check

{u'checksum': u'00052076', u'data': u'06af12aa7997d8694a6ca8d88d6f5927250df9648bc1790ccddddd0b060bd5e0ca5d4b3a0dde08bb3e2
b6c31b0b9d150fce79cc461c45c2e2917625294926657c2a4b463a0390c9f6a955af338d5ff299c6b1da3
e90334ca9ad244a210cc0b93c06d641e', u'number': u'000150'}
{u'checksum': u'00052076', u'data': u'46af12aa7997d8694a6ca8d88d6f5927250df9648bc1790ccddddd0b060bd5e0ca5d4b3a0dde08bb3e2
b6c31b0b9d150fce79cc461c45c2e2917621294926657c2a4b463a0390c9f6a955af338d5ff299c6b1da3
e90334ca9ad244a210cc0b93c06d641e', u'number': u'000150'}

Where the data corrupts on the wire/interface. Sequence number did not change but the data changes. However, the checksum could not identify the error.
		

We have conducted runs on the experiments and 1/2 times inthe 20% corruption experiment, either we observed some empty space in the buffer of the d, or the buffer is full but because of the small capability of the checksum, the data is changed and file is transmitted incorrectly.

-----------------------------------------------------------------------------------------------
In the version 2, we have done the following parameters:

Since the data payload is 200 bytes, the checksum could not fully detect the issue in the payload. We decreased payload to 20 byte, and added protection to both seq number and data, as in version 1.1

In this way, we can almost fully detect bit errors because the payload + seqn is relatively small to the previous implementations. However, due to decreased number of payload, packet number has increased. Morever, the send packet size is 76 bytes and the received feedback packet's size is 84 byte. Experiments take much longer and we did not run all of the experiments because of the reasons above. We also added checksum to feedback packet.

-----------------------------------------------------------------------------------------------

In version 3, which is the final version, we changed several stages of our implementation.
1- In s, instead of reading 20 bytes from file, then decode it in hex and forward it, we simply read all of the files line by line, then put it in a buffer string. After that we transmit 500 byte of this string at each request.
2- In b, instead of packetizing it in to a json object, or python dictionary, we append it to a string and added packet numbers etc to its tail.
	sendpacket = "PAYLOADHERE"
	sendpacket += "PACKETNUMBER"
	check = checksumfunction(sendpacket)
	sendpacket += check
	
In the implementation above, the payload size is 250 byte per package, because we are dividing 500 incoming bytes into two.
Also we have changed our checksum function from TCP checksum to md5 for better accuracy.
3- As previous iterations, we added checksum to feedback function which is md5.
4- In the previous versions, not desired packet could enter the buffer. i.e., the packet 100 should have received, however it corrupts on its way. The checksum could not detect the error, and the received packets seqn is 105. We put this packet into buffer 105 and send back 105ACK message. When the 100 packet times out in b, it will be resent and and it will take its position in d buffer. However, the 105th packet in b already acked due to error. We don't retransmit this even though it is not correctly acked.
5- To avoid the issue above, the d now expects only one packet at a time. If the expected value is 100 and the received packet is 102, d does not accept this. It might have happened either because of the error in the network, or out of order. We don't care this situation, our top priority is reliability. If the expected value is 100 but we have received 98, we have correctly received this previously but we still send a 98 ack to back, to avoid infinite loop or stuck in b.



