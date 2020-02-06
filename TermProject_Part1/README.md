# 435Network_TP
Network 435 Term Project
Created by Aykut Yardım 2110278 and Koray Yurtseven 2099547

We have scripts in this directory, \\
experiment results in exp_results directory,\\
codes for plotting graphs in matlab_plot_codes directory,\\
and the latex report in report_files directory


To run our program you must put the corresponding scripts to each machine:
s.py and createfilefor_s.py to s
d.py to d
r1.py to r1
r2.py to r2
b.py to b

Before running our program, we must run the createfilefor_s.py to create a dummy sensor.txt file.
s.py will read from that file chunks and will send the data.
Also, we need to execute ntp code to synchronize time for d and s. Only d and s synchronization is enough

The establish connections, we must start first the d, then r1 and r2, then b and at last s.

We have used different paths in our project, namely:

For data flow:
s-d TCP
d-r1 udp
d-r2 udp
r1-d udp
r2-d udp

For ack flow:
d-r2 UDP
d-r1 UDP
r1-b UDP
r2-b UDP
b-s UDP

We assigned the corresponding network interfaces and port numbers at the beginning of the each file.

While the simulation is running, s prints the ACK messages, and d prints the data message and 
their info such as packet number and path

After the simulation is over, i.e. all connections are closed, the main thread in the s reads the
feedback data and the send data times from global array, and calculates measured end to end delay.


We have run this 3 different experiments 10 times and collect the data. Then, we have created 
matlab code for plotting related figures. You can find those codes in matlab_plot_codes directory 
and the conclution of experiment results in exp_results directory. 

