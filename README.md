# TCP_BBR
TCP-BBR Congestion Control Algorithm

BBR Congestion Control: Overview:

- BBR = Bottleneck Bandwidth and Round-trip propagation time 
- BBR seeks high throughput with a small queue by probing BW and RTT 
- Ground-up redesign of congestion control - Not loss-based, Not delay-based, Not ECN-based, Not AIMD-based 
- Models the network path: probes and estimates max BW and min RTT 
- Key insight: measure max BW and min RTT at different times 
- Assume path properties are mostly stationary  

Complete Procedure to run the tcp-bbr.cc:

1. Save the File: Save the above code as tcp-bbr.cc in the ns-2.35/tcp/ directory.

2. Modify Makefile.in: Add tcp-bbr.o to the list of object files in ns-2.35/Makefile.in. Find the line starting with OBJ_CC = and append:
tcp/tcp-bbr.o \

Then click ctrl+x to save and ctrl+y to exit

3.Recompile NS-2
       ->  cd ns-2.35
->  ./configure
->  make clean

NOTE: if ./configure doesn’t run, run below command:
 ./configure --with-tcl=/home/desktop/ns-allinone-2.35/tcl8.5.10 --with-tcl-ver=8.5.10  --with-tk=/home/desktop/ns-allinone-2.35/tk8.5.10 --with-tk-ver=8.5.10

4. Run command: make

5. Place the bbr_test.tcl script(in github repo(test.tcl)) in your ns-2.35 directory and run it:

cd ~/ns-allinone-2.35/ns-2.35
./ns bbr_test.tcl

This will execute the simulation and generate out.tr and out.nam.

6.Launch the simulation:
    
nam bbr_nam.nam

The nam tool will launch automatically to visualize the simulation.Use the out.tr file to analyze TCP-BBR’s behavior (e.g., throughput, congestion window, RTT). You can process it with tools like awk, perl, or Python scripts
