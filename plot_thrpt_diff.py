import re
from turtle import delay
import matplotlib.pyplot as plt

def parse_delay_file(filename, algo, i,p):
    global throughput
    val = 0
    with open(filename, 'r') as f:
        for line in f:
            line_strip = line.strip()
            if re.search(r'gbps\sper\sport', line_strip):
                data = re.split(r'gbps\sper\sport', line_strip)
                #print(float(data[0]))
                val = float(data[0])
            elif re.search(r'time\s=\s', line_strip):
                data = re.split(r'time\s=\s', line_strip)
                print(data)
                #print(float(data[0]))
                t[p][algo][i] = int(data[-1])

    if val!=0:
        throughput[p][algo][i] = val

def plot_single_throughput(plot_idx, output_name):
    import numpy as np
    import matplotlib.pyplot as plt

    plt.rcParams["hatch.linewidth"] = 2.0

    CUSTOM_LABELS = {
        "SP_Ideal": "Selective Pushout",
        "Optimal":  "LQD"
    }

    COLOR = {
        "SP_Ideal": "#DA70D6",
        "Optimal":  "#32CD32",
    }

    labels = ["0.37", "0.5", "0.62"]
    alg_labels = ["SP_Ideal", "Optimal"]

    x = np.arange(len(labels))
    width = 0.16

    fig, ax = plt.subplots(figsize=(10, 6))

    for a, alg in enumerate(alg_labels):
        offset = (a - (len(alg_labels) - 1) / 2) * width
        x_pos = x + offset

        ax.bar(
            x_pos,
            throughput[plot_idx][a],
            width=width,
            label=CUSTOM_LABELS.get(alg, alg),
            color=COLOR[alg],
            edgecolor="black",
            linewidth=1,
            alpha=1.0,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=30)

    ax.tick_params(axis="y", labelsize=30)
    ax.tick_params(axis="x", labelsize=30)

    ax.set_ylim(0, 1.5)

    ax.set_xlabel(
        "Fraction of Output Ports Active",
        fontsize=30,
        fontweight="normal",
        labelpad=10,
    )

    ax.set_ylabel(
        "Normalized Throughput",
        fontsize=30,
        fontweight="normal",
        labelpad=12,
    )



    ax.yaxis.grid(True, linestyle=":", color="black")
    ax.set_axisbelow(True)

    lgd = ax.legend(
        loc="upper left",
        frameon=True,
        fontsize=22,
        borderpad=0.3,
        ncol=2,
    )
    lgd.get_frame().set_edgecolor("black")

    fig.tight_layout()

    fig.savefig(
        output_name,
        dpi=300,
        bbox_inches="tight",
        pad_inches=0.02,
    )

    plt.show()


def plot_throughput():
    # shared = without private buffer
    plot_single_throughput(
        plot_idx=0,
        output_name="throughput_shared_buffer.png",
    )

    # private = with private buffer
    plot_single_throughput(
        plot_idx=1,
        output_name="throughput_private_buffer.png",
    )
load = [0, 1, 2]
PLOTS = ['thrpt_diff_shared','thrpt_diff_prvt']
ALG = ["spideal","optimal"]
throughput = [[[0 for _ in range(3)] for i in range(2)] for p in range(2)]
t = [[[0 for _ in range(3)] for i in range(2)] for p in range(2)]
for p,plot in enumerate(PLOTS):
    for ind,algo in enumerate(ALG):
        for i in load:
            parse_delay_file(f'{plot}/{algo}_logs/output_{algo}_50_uniform_1_incast_set{i}.txt',ind,i,p)
for p,plot in enumerate(PLOTS):
    for ind,algo in enumerate(ALG):
        for i in load:
                
                throughput[p][ind][i] = throughput[p][ind][i]/throughput[p][1][i]

print(throughput)
print(t)
plot_throughput()