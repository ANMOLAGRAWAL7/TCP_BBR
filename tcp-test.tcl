# Create a new simulator object
set ns [new Simulator]

# Open trace files
set tracefile [open bbr_trace.tr w]
$ns trace-all $tracefile

set namfile [open bbr_nam.nam w]
$ns namtrace-all $namfile

# Create two nodes
set n0 [$ns node]
set n1 [$ns node]

# Create a duplex link (1Mbps bandwidth, 10ms delay, DropTail queue)
$ns duplex-link $n0 $n1 1Mb 10ms DropTail

# Set up TCP BBR agent
set tcp [new Agent/TCP/Bbr]
$tcp set packetSize_ 1000  ;# Packet size in bytes
$ns attach-agent $n0 $tcp

# Set up TCP sink
set sink [new Agent/TCPSink]
$ns attach-agent $n1 $sink

# Connect TCP BBR to sink
$ns connect $tcp $sink

# Set up FTP application over TCP BBR
set ftp [new Application/FTP]
$ftp attach-agent $tcp

# Schedule events
$ns at 0.1 "$ftp start"    ;# Start FTP at 0.1 seconds
$ns at 4.0 "$ftp stop"     ;# Stop FTP at 4.0 seconds
$ns at 5.0 "finish"        ;# End simulation at 5.0 seconds

# Define finish procedure
proc finish {} {
    global ns tracefile namfile
    $ns flush-trace
    close $tracefile
    close $namfile
    puts "Simulation finished. Run 'nam bbr_nam.nam' to visualize."
    exit 0
}

# Run the simulation
$ns run
