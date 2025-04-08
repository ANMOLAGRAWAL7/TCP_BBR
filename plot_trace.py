import matplotlib.pyplot as plt
import numpy as np
import os

def parse_trace_file(filename):
    """
    Parse NS-2/NS-3 trace file format and extract throughput data
    
    Args:
        filename: Path to the trace file
        
    Returns:
        tuple: ((time_points, throughput_values), (delay_times, delay_values))
    """
    time_tp = []
    bytes_received = []
    current_time = 0
    bytes_count = 0
    send_times = {}
    delays = []
    delay_times = []
    
    # Time window for throughput calculation (in seconds)
    window = 0.1
    
    print(f"Parsing file: {filename}")
    try:
        with open(filename, 'r') as f:
            for line in f:
                fields = line.split()
                
                # Check if line has enough fields to parse
                if len(fields) <= 10:
                    continue
                    
                try:
                    event = fields[0]
                    event_time = float(fields[1])
                    src_node = int(fields[2])
                    dest_node = int(fields[3])
                    packet_size = int(fields[5])
                    seq_num = fields[10]
                    
                    # Track received packets at destination node (node 1)
                    if event == 'r' and dest_node == 1:
                        if event_time > current_time + window:
                            # Calculate throughput in bits per second
                            if current_time > 0:  # Skip the first window
                                time_tp.append(current_time)
                                throughput = bytes_count * 8 / window  # Convert bytes to bits
                                bytes_received.append(throughput)
                            
                            # Reset counters for new window
                            bytes_count = packet_size
                            current_time = current_time + window
                            
                            # Handle potential time gaps
                            while current_time + window < event_time:
                                time_tp.append(current_time)
                                bytes_received.append(0)  # No throughput in this window
                                current_time = current_time + window
                        else:
                            bytes_count += packet_size
                        
                        # Calculate delay if we have the send time
                        if seq_num in send_times:
                            delay = event_time - send_times[seq_num]
                            delay_times.append(event_time)
                            delays.append(delay)
                            del send_times[seq_num]
                    
                    # Track sent packets from source node (node 0)
                    if event == '+' and src_node == 0:
                        send_times[seq_num] = event_time
                        
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    continue
    
        # Add the last window if there's data
        if bytes_count > 0:
            time_tp.append(current_time)
            bytes_received.append(bytes_count * 8 / window)
    
        print(f"Throughput data points for {filename}: {len(time_tp)}")
        print(f"Delay data points for {filename}: {len(delays)}")
        
        # Convert to Mbps for better readability
        bytes_received = [tp / 1000000 for tp in bytes_received]
        
        return (time_tp, bytes_received), (delay_times, delays)
        
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return ([], []), ([], [])

def plot_single_throughput(time_points, throughput, protocol_name, output_file):
    """
    Plot throughput for a single protocol
    
    Args:
        time_points: List of time points
        throughput: List of throughput values
        protocol_name: Name of the protocol (BBR or Reno)
        output_file: File path for saving the plot
    """
    plt.figure(figsize=(10, 6))
    
    # Choose color based on protocol
    color = 'blue' if protocol_name.lower() == 'bbr' else 'red'
    
    # Plot the throughput data
    plt.plot(time_points, throughput, label=f'TCP {protocol_name}', color=color, linewidth=1.5)
    
    # Calculate and display statistics
    if throughput:
        mean_tp = np.mean(throughput)
        median_tp = np.median(throughput)
        max_tp = max(throughput)
        
        # Add mean line
        plt.axhline(y=mean_tp, color=color, linestyle='--', alpha=0.7,
                   label=f'Mean: {mean_tp:.2f} Mbps')
                   
        # Add stats text box
        stats_text = f"Mean: {mean_tp:.2f} Mbps\nMedian: {median_tp:.2f} Mbps\nMax: {max_tp:.2f} Mbps"
        plt.text(time_points[0], max(throughput) * 0.9, stats_text, 
                fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Throughput (Mbps)', fontsize=12)
    plt.title(f'TCP {protocol_name} Throughput', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Plot saved as {output_file}")

def plot_throughput_comparison(bbr_data, reno_data, output_file="throughput_comparison.png"):
    """
    Plot throughput comparison between BBR and Reno
    
    Args:
        bbr_data: Tuple of (time_points, throughput) for BBR
        reno_data: Tuple of (time_points, throughput) for Reno
        output_file: File path for saving the plot
    """
    bbr_time, bbr_throughput = bbr_data
    reno_time, reno_throughput = reno_data
    
    plt.figure(figsize=(12, 6))
    
    # Plot the throughput data
    if bbr_time and bbr_throughput:
        plt.plot(bbr_time, bbr_throughput, label='TCP BBR', color='blue', linewidth=1.5)
        
        # Calculate and display BBR statistics
        bbr_mean = np.mean(bbr_throughput)
        plt.axhline(y=bbr_mean, color='blue', linestyle='--', alpha=0.7,
                   label=f'BBR Mean: {bbr_mean:.2f} Mbps')
    
    if reno_time and reno_throughput:
        plt.plot(reno_time, reno_throughput, label='TCP Reno', color='red', linewidth=1.5)
        
        # Calculate and display Reno statistics
        reno_mean = np.mean(reno_throughput)
        plt.axhline(y=reno_mean, color='red', linestyle='--', alpha=0.7,
                   label=f'Reno Mean: {reno_mean:.2f} Mbps')
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Throughput (Mbps)', fontsize=12)
    plt.title('TCP Throughput Comparison: BBR vs Reno', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=10)
    
    # Add performance improvement text if both algorithms have data
    if bbr_throughput and reno_throughput:
        bbr_mean = np.mean(bbr_throughput)
        reno_mean = np.mean(reno_throughput)
        improvement = ((bbr_mean - reno_mean) / reno_mean) * 100
        
        # Place text in top left corner
        text_x = min(bbr_time[0] if bbr_time else float('inf'), 
                     reno_time[0] if reno_time else float('inf'))
        text_y = max(max(bbr_throughput) if bbr_throughput else 0, 
                     max(reno_throughput) if reno_throughput else 0) * 0.95
                     
        if improvement > 0:
            plt.text(text_x, text_y, 
                     f"BBR outperforms Reno by {improvement:.1f}%",
                     fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
        else:
            plt.text(text_x, text_y, 
                     f"Reno outperforms BBR by {-improvement:.1f}%",
                     fontsize=10, bbox=dict(facecolor='white', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Plot saved as {output_file}")
    
    return output_file

def calculate_statistics(time_points, throughput):
    """Calculate and return throughput statistics"""
    if not throughput:
        return {
            'mean': 0,
            'median': 0,
            'max': 0,
            'min': 0,
            'std': 0,
            'total_data': 0,
            'duration': 0
        }
    
    stats = {
        'mean': np.mean(throughput),
        'median': np.median(throughput),
        'max': max(throughput),
        'min': min(throughput),
        'std': np.std(throughput),
        'total_data': np.sum(throughput) * 0.1 / 8,  # Convert back to MB
        'duration': max(time_points) - min(time_points) if time_points else 0
    }
    return stats

def print_statistics(bbr_stats, reno_stats):
    """Print throughput statistics for both protocols"""
    print("\n===== TCP Throughput Statistics =====")
    print("\nTCP BBR:")
    print(f"  Mean Throughput: {bbr_stats['mean']:.2f} Mbps")
    print(f"  Median Throughput: {bbr_stats['median']:.2f} Mbps")
    print(f"  Max Throughput: {bbr_stats['max']:.2f} Mbps")
    print(f"  Min Throughput: {bbr_stats['min']:.2f} Mbps")
    print(f"  Standard Deviation: {bbr_stats['std']:.2f} Mbps")
    print(f"  Total Data Transferred: {bbr_stats['total_data']:.2f} MB")
    print(f"  Duration: {bbr_stats['duration']:.2f} seconds")
    
    print("\nTCP Reno:")
    print(f"  Mean Throughput: {reno_stats['mean']:.2f} Mbps")
    print(f"  Median Throughput: {reno_stats['median']:.2f} Mbps")
    print(f"  Max Throughput: {reno_stats['max']:.2f} Mbps")
    print(f"  Min Throughput: {reno_stats['min']:.2f} Mbps")
    print(f"  Standard Deviation: {reno_stats['std']:.2f} Mbps")
    print(f"  Total Data Transferred: {reno_stats['total_data']:.2f} MB")
    print(f"  Duration: {reno_stats['duration']:.2f} seconds")
    
    if bbr_stats['mean'] > 0 and reno_stats['mean'] > 0:
        improvement = ((bbr_stats['mean'] - reno_stats['mean']) / reno_stats['mean']) * 100
        if improvement > 0:
            print(f"\nBBR outperforms Reno by {improvement:.2f}% in average throughput")
        else:
            print(f"\nReno outperforms BBR by {-improvement:.2f}% in average throughput")

def main():
    """Main function to process trace files and generate plots"""
    # Define trace file paths
    bbr_trace = 'bbr_trace.tr'
    reno_trace = 'reno_trace.tr'
    
    # Parse trace files
    (bbr_time, bbr_throughput), (bbr_delay_time, bbr_delays) = parse_trace_file(bbr_trace)
    (reno_time, reno_throughput), (reno_delay_time, reno_delays) = parse_trace_file(reno_trace)
    
    # Calculate statistics
    bbr_stats = calculate_statistics(bbr_time, bbr_throughput)
    reno_stats = calculate_statistics(reno_time, reno_throughput)
    
    # Plot individual graphs
    if bbr_time and bbr_throughput:
        plot_single_throughput(bbr_time, bbr_throughput, "BBR", "bbr_throughput.png")
    
    if reno_time and reno_throughput:
        plot_single_throughput(reno_time, reno_throughput, "Reno", "reno_throughput.png")
    
    # Plot and save throughput comparison
    plot_file = plot_throughput_comparison(
        (bbr_time, bbr_throughput), 
        (reno_time, reno_throughput)
    )
    
    # Print statistics
    print_statistics(bbr_stats, reno_stats)
    
    # Also plot the delay comparison if requested
    if bbr_delay_time and reno_delay_time:
        plt.figure(figsize=(12, 6))
        plt.plot(bbr_delay_time, bbr_delays, label='TCP BBR', color='blue', linestyle='-')
        plt.plot(reno_delay_time, reno_delays, label='TCP Reno', color='red', linestyle='-')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Delay (seconds)')
        plt.title('End-to-End Delay Comparison')
        plt.legend()
        plt.grid(True)
        plt.savefig('delay_comparison.png')
        print("Delay comparison plot saved as delay_comparison.png")
    
    # Show the plots if running in interactive mode
    plt.show()

if __name__ == "__main__":
    main()
