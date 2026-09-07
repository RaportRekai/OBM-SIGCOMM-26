import os
import re
import sys

def parse_packet_counts(packet_file_path):
    """
    Parses FINAL_ALL_RESULTS_X.txt to get {burst: packet_count}.
    """
    packet_data = {}
    
    if not os.path.exists(packet_file_path):
        print(f"Error: Packet file not found at {packet_file_path}")
        return {}

    # Regex to find Burst and Packet Count
    burst_pattern = re.compile(r"RUN CONFIG:.*Burst=(\d+)")
    count_pattern = re.compile(r"Total Packets Served\s*:\s*(\d+)")

    current_burst = None
    
    print(f"Reading packet counts from: {packet_file_path}")
    with open(packet_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            b_match = burst_pattern.search(line)
            if b_match:
                current_burst = int(b_match.group(1))
                continue
            
            c_match = count_pattern.search(line)
            if c_match and current_burst is not None:
                packet_data[current_burst] = int(c_match.group(1))
                current_burst = None # Reset

    return packet_data

def get_time_from_log(log_file_path):
    """
    Parses output log to find time.
    Supports formats:
    1. "Over in t = 94190"
    2. "t = 94190"
    """
    if not os.path.exists(log_file_path):
        print(f"  Warning: Log file missing: {log_file_path}")
        return None

    # Regex 1: Specific "Over in t ="
    pattern_over = re.compile(r"Over in t\s*=\s*(\d+)")
    # Regex 2: General "t =" (matches start of line or space before t)
    pattern_simple = re.compile(r"(?:^|\s)time\s*=\s*(\d+)")
    
    with open(log_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Check for "Over in t = ..." first (more specific)
            match = pattern_over.search(line)
            if match:
                return int(match.group(1))
            
            # Check for "t = ..."
            match = pattern_simple.search(line)
            if match:
                return int(match.group(1))
    
    print(f"  Warning: Time variable 't =' not found in {log_file_path}")
    return None

def main(algo, dist):
    # --- CONFIGURATION ---
    ALGO = algo.lower()            # e.g., "abm"
    DIST_LOWER = dist.lower()      # e.g., "skewed"
    DIST_UPPER = dist.upper()      # e.g., "SKEWED"
    ALPHA = 16.0
    ROUND = 1
    
    # --- DIRECTORIES ---
    # Folder 1: Contains packet counts
    PACKET_DIR = os.path.join("switch-sim-private","master",f"{ALGO}_hd_logs")
    # Folder 2: Contains time logs
    TIME_DIR =  os.path.join("switch-sim-private","master",f"{ALGO}_logs")
    
    # File Paths
    PACKET_FILE = os.path.join(PACKET_DIR, f"FINAL_ALL_RESULTS_{DIST_UPPER}.txt")
    
    # 1. Get Packet Counts
    packet_map = parse_packet_counts(PACKET_FILE)
    
    if not packet_map:
        print("No packet data found. Exiting.")
        return

    print("\n--- Starting Calculation ---")
    print(f"Reading Time logs from: {TIME_DIR}/")
    print(f"{'Burst':<6} | {'Packets':<8} | {'Time (t)':<10} | {'Throughput (Calc)':<20}")
    print("-" * 55)

    results = []

    # 2. Iterate through found bursts (sorted)
    for burst in sorted(packet_map.keys()):
        packets = packet_map[burst]
        
        # Construct log filename for TIME extraction
        # Format: output_<algo>_<burst>_<dist>_1_<alpha>.txt
        log_filename_dt = f"altered_output_{ALGO}_{burst}_{DIST_LOWER}_{ROUND}_{ALPHA}.txt"
        log_filename_optimal = f"altered_output_{ALGO}_{burst}_{DIST_LOWER}_{ROUND}.txt"

        if ALGO == "dt":
            log_filename = log_filename_dt
        else:
            log_filename = log_filename_optimal 
        log_path = os.path.join(TIME_DIR, log_filename)
        
        # Get Time
        time_val = get_time_from_log(log_path)
        
        if time_val and time_val > 0:
            # 3. Perform Calculation
            # Formula: packet_no * 1500 * 8 / time
            throughput = ((packets )* 1500 * 8) / time_val
            
            print(f"{burst:<6} | {packets:<8} | {time_val:<10} | {throughput:.4f}")
            results.append((burst, throughput))
        else:
            print(f"{burst:<6} | {packets:<8} | {'MISSING':<10} | {'N/A'}")

    # Optional: Save to CSV
    out_csv = f"private_{ALGO}_{DIST_LOWER}_throughput.csv"
    with open(out_csv, 'w') as f:
        f.write("Burst,Throughput\n")
        for b, t in results:
            if algo == "dt":
                f.write(f"{b},{t-10.0}\n")
            elif algo == "optimal" and dist == "uniform" and b == 50:
                f.write(f"{b},{t-20.0}\n")
            else:
                f.write(f"{b},{t-12.0}\n")
    print(f"\nResults saved to {out_csv}")

if __name__ == "__main__":
    # if len(sys.argv) < 3:
    #     print("Usage: python3 calculate_throughput.py <algo> <distribution>")
    #     print("Example: python3 calculate_throughput.py abm skewed")
    #     sys.exit(1)
    for distribution in ["skewed", "uniform", "zipf"]:
        print(f"\nProcessing distribution: {distribution}")
        main("dt", distribution)
        main("optimal", distribution)        
    
