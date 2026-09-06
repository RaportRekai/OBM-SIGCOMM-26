import re
import matplotlib.pyplot as plt
import os
import copy

def plot_two_bar_series(x_labels, y1, y2):
    import numpy as np
    import matplotlib.pyplot as plt

    plt.rcParams["hatch.linewidth"] = 2.0

    CUSTOM_LABELS = {
        "OBM":      "OBM",
        "Optimal":  "LQD",
    }

    COLOR = {
        "OBM":      "#FF0000",
        "Optimal":  "#32CD32",
    }

    label1 = "Optimal"   # LQD
    label2 = "OBM"

    xlabel = "Buffer Size"
    ylabel = "Normalized Throughput"

    save_path = "normalized_throughput_vs_buffer.png"

    # Normalize wrt y1 / LQD
    y1_norm = []
    y2_norm = []

    for a, b in zip(y1, y2):
        if a != 0:
            y1_norm.append(1.0)
            y2_norm.append(b / a)
        else:
            y1_norm.append(0.0)
            y2_norm.append(0.0)

    x = np.arange(len(x_labels))

    # Smaller width = thinner bars
    bar_width = 0.22

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        x - bar_width / 2,
        y1_norm,
        width=bar_width,
        label=CUSTOM_LABELS[label1],
        color=COLOR[label1],
        edgecolor="black",
        linewidth=1,
        alpha=1.0,
    )

    ax.bar(
        x + bar_width / 2,
        y2_norm,
        width=bar_width,
        label=CUSTOM_LABELS[label2],
        color=COLOR[label2],
        edgecolor="black",
        linewidth=1,
        alpha=1.0,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=30)

    ax.tick_params(axis="y", labelsize=30)
    ax.tick_params(axis="x", labelsize=30)

    ax.set_xlabel(
        xlabel,
        fontsize=30,
        fontweight="normal",
        labelpad=12,
    )

    ax.set_ylabel(
        ylabel,
        fontsize=30,
        fontweight="normal",
        labelpad=14,
    )

    ax.set_ylim(0, 1.5)

    ax.yaxis.grid(True, linestyle=":", color="black")
    ax.set_axisbelow(True)

    lgd = ax.legend(
        loc="upper left",
        frameon=True,
        fontsize=25,
        borderpad=0.3,
        ncol=2,
    )
    lgd.get_frame().set_edgecolor("black")

    fig.tight_layout()

    fig.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.12,
)

    plt.close()



def plot_one_bar_series(x_labels, y1):
    import numpy as np
    import matplotlib.pyplot as plt

    plt.rcParams["hatch.linewidth"] = 2.0

    CUSTOM_LABELS = {
        "OBM":      "OBM",
    }

    COLOR = {
        "OBM":      "#FF0000",
    }

    label1 = "OBM"

    xlabel = "Buffer Size"
    ylabel = "Corrupted Packets (%)"

    save_path = "corrupted_packets_vs_buffer.png"

    # Normalize wrt y1 / LQD
    y1_norm = []

  
    x = np.arange(len(x_labels))

    # Smaller width = thinner bars
    bar_width = 0.22

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        x,
        y1,
        width=bar_width,
        label=CUSTOM_LABELS[label1],
        color=COLOR[label1],
        edgecolor="black",
        linewidth=1,
        alpha=1.0,
    )

    

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=30)

    ax.tick_params(axis="y", labelsize=30)
    ax.tick_params(axis="x", labelsize=30)

    ax.set_xlabel(
        xlabel,
        fontsize=30,
        fontweight="normal",
        labelpad=12,
    )

    ax.set_ylabel(
        ylabel,
        fontsize=30,
        fontweight="normal",
        labelpad=14,
    )

    #ax.set_ylim(0, 1.5)

    ax.yaxis.grid(True, linestyle=":", color="black")
    ax.set_axisbelow(True)

    lgd = ax.legend(
        loc="upper left",
        frameon=True,
        fontsize=25,
        borderpad=0.3,
        ncol=2,
    )
    lgd.get_frame().set_edgecolor("black")

    fig.tight_layout()

    fig.savefig(
    save_path,
    dpi=300,
    bbox_inches="tight",
    pad_inches=0.12,
)

    plt.close()

def crct_throughput(throughput):
    for i in range(len(BUFFER_SIZE)):
        throughput[1][i] = throughput[1][i]*time[1][i]/time[0][i]
def parse_delay_file(filename,i,j):
    global throughput
    val = 0
    print(filename)
    with open(filename, 'r') as f:
        print(f'****************{filename}**************')
        for line in f:
            line_strip = line.strip()
            if re.search(r'gbps\sper\sport', line_strip):
                data = re.split(r'gbps\sper\sport', line_strip)
                print(float(data[0]))
                throughput[i][j] = float(data[0])
                #val = float(data[0])
            elif re.search(r'time\s=', line_strip):
                data = re.split(r'time\s=\s', line_strip)
                print(data[-1])
                time[i][j] = float(data[-1])
                #val = float(data[-1])
            elif re.search(r'packets\sserved\s=\s', line_strip):
                data = re.split(r'packets\sserved\s=\s', line_strip)
                print(data[-1])
                packets[i][j] = float(data[-1])
                #val = float(data[-1])
            elif re.search(r'dropped\spackets\s=\s', line_strip):
                data = re.split(r'dropped\spackets\s=\s', line_strip)
                print(data[-1])
                dropped_packets[i][j] = int(data[-1])
                #val = float(data[-1])
                
    # if val!=0:
    #     throughput.append(val) 

DIST = "uniform"
BASE_PATH = "master"
ALGO_NAME = ["optimal","obm"]
BUFFER_SIZE = [20000,14000,8000,4000,2000]
X_LABELS = ['10MB', '6MB', '3MB', '1.5MB', '0.75MB']
throughput = [[0 for _ in range(len(BUFFER_SIZE))] for i in range(len(ALGO_NAME))]
time = [[0 for _ in range(len(BUFFER_SIZE))] for i in range(len(ALGO_NAME))]
packets = [[0 for _ in range(len(BUFFER_SIZE))] for i in range(len(ALGO_NAME))]
dropped_packets = [[0 for _ in range(len(BUFFER_SIZE))] for i in range(len(ALGO_NAME))]

for i in range(len(ALGO_NAME)):
    for j in range(len(BUFFER_SIZE)):
        filename = f"{ALGO_NAME[i]}_logs/output_{ALGO_NAME[i]}_50_{DIST}_1_{BUFFER_SIZE[j]}.txt"
        if os.path.exists(filename):
            parse_delay_file(filename,i,j)
old_throughput = copy.deepcopy(throughput)
print(throughput)
crct_throughput(throughput)
for i in range(len(BUFFER_SIZE)):
    print(throughput[1][i],throughput[0][i])

#plot_two_bar_series(X_LABELS, throughput[0], throughput[1])

broken_packet_perc = [0 for _ in range(len(BUFFER_SIZE))]
for j in range(len(BUFFER_SIZE)):
    broken_packet_perc[j] = (packets[0][j] - packets[1][j])/(dropped_packets[0][j] + packets[0][j])

plot_one_bar_series(X_LABELS, broken_packet_perc)