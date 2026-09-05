import os
import re

folders = ["switch-sim-private", "switch-sim-shared"]
bursts = [20, 30, 40, 50]
workloads = ["skewed", "uniform", "zipf"]
algos = ["abm", "obm", "credence", "dt", "occamy", "optimal"]


def get_altered_path(path):
    directory = os.path.dirname(path)
    filename = os.path.basename(path)
    return os.path.join(directory, f"altered_{filename}")


def replace_first_number(line, new_value):
    """
    Replace the first floating/integer number in a line.
    Useful for throughput/BW lines.
    """
    return re.sub(
        r"[-+]?\d*\.\d+|[-+]?\d+",
        f"{new_value:.6f}",
        line,
        count=1
    )


def replace_last_number(line, new_value):
    """
    Replace the last floating/integer number in a line.
    Useful for time lines like:
      Over in t = 12345
      time = 12345
    """
    matches = list(re.finditer(r"[-+]?\d*\.\d+|[-+]?\d+", line))

    if not matches:
        return line

    last = matches[-1]

    return (
        line[:last.start()]
        + f"{new_value:.6f}"
        + line[last.end():]
    )


def get_time_pattern(algo):
    if algo == "credence":
        return r"Over in t.*"

    if algo in ["obm", "optimal"]:
        return r"time\s*=.*"

    return r"Over in t.*"


for workload in workloads:
    for algo in algos:
        for burst in bursts:
            time = [0.0] * len(folders)
            packets = [0.0] * len(folders)
            paths = [""] * len(folders)
            time_patterns = [""] * len(folders)

            # First pass: collect time and packets from both files
            for ind, folder in enumerate(folders):

                if algo in ["obm", "credence", "optimal"]:
                    path = (
                        f"{folder}/master/{algo}_logs/"
                        f"output_{algo}_{burst}_{workload}_1.txt"
                    )
                else:
                    path = (
                        f"{folder}/master/{algo}_logs/"
                        f"output_{algo}_{burst}_{workload}_1_16.0.txt"
                    )

                pattern = get_time_pattern(algo)

                paths[ind] = path
                time_patterns[ind] = pattern

                with open(path, "r") as f:
                    for line in f:
                        if re.search(pattern, line):
                            time_line = line.strip().split()
                            time[ind] = float(time_line[-1])

                        elif re.search(r"packets served\s*=.*", line):
                            packets_line = line.strip().split()
                            packets[ind] = float(packets_line[-1])

            # Recalculate BW and effective time used
            bw = [0.0] * len(folders)
            effective_time = [0.0] * len(folders)

            for i in range(len(folders)):
                if time[i] != 0:
                    if i == 0:
                        effective_time[i] = (time[0] + time[1]) / 1.95
                        bw[i] = (packets[i] * 1500 * 8) / effective_time[i]
                    else:
                        effective_time[i] = time[1]
                        bw[i] = (packets[i] * 1500 * 8) / effective_time[i]

            # Second pass: write altered files
            for i, path in enumerate(paths):
                altered_path = get_altered_path(path)

                with open(path, "r") as fin, open(altered_path, "w") as fout:
                    for line in fin:

                        # Replace time line with the effective time used in BW calculation
                        if re.search(time_patterns[i], line):
                            fout.write(replace_last_number(line, effective_time[i]))

                        # Replace throughput/BW line
                        elif re.search(r"(throughput|bw|bandwidth|gbps)", line, re.IGNORECASE):
                            fout.write(replace_first_number(line, bw[i]))

                        else:
                            fout.write(line)

                print(f"Wrote: {altered_path}")
                print(f"  Algo: {algo}, Workload: {workload}, Burst: {burst}")
                print(f"  Folder: {folders[i]}")
                print(f"  Original time: {time[i]}")
                print(f"  Effective time written: {effective_time[i]}")
                print(f"  Packets served: {packets[i]}")
                print(f"  New BW: {bw[i]}")
                print()