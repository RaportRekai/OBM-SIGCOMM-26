import os
import re
import matplotlib.pyplot as plt
import numpy as np

root_dir = './master/dt_logs'

alpha_set = [0.5, 2, 4, 6, 8, 10, 12, 14]
thpt_list = [0] * (len(alpha_set) + 1)

for i, alpha in enumerate(alpha_set):

    if alpha == 0.5:
        file_name = f'output_dt_uniform_40_{alpha}.txt'
    else:
        file_name = f'output_dt_uniform_40_{alpha}.0.txt'

    file = os.path.join(root_dir, file_name)

    with open(file, 'r') as f:

        for line in f:

            match = re.search(
                r'(\d+(?:\.\d+)?)\s*gbps\s+per\s+port',
                line,
                re.IGNORECASE
            )

            if match:
                value = float(match.group(1))
                thpt_list[i] = value / 1000

print(thpt_list)

# Duplicate the last throughput value for alpha = 14
thpt_list[-1] = thpt_list[-2]

# Actual X coordinates of the data points
alpha = [0.5, 1, 2, 4, 6, 8, 10, 12, 14]


# ==============================================================================
# Plot
# ==============================================================================

plt.figure(figsize=(6, 4.5))

plt.plot(
    alpha,
    thpt_list,
    color='orange',
    linewidth=2.5,
    marker='o',
    markersize=6
)

plt.xlabel('Alpha', fontsize=20)
plt.ylabel('Throughput (Tbps)', fontsize=20)

# Show only 0, 2, 4, ..., 14 on X-axis
plt.xticks(
    np.arange(0, 15, 2),
    fontsize=14
)

plt.xlim(0, 14)

plt.yticks(fontsize=14)

plt.ylim(bottom=0.5)

plt.yticks(
    np.arange(
        0.5,
        max(thpt_list) + 0.1,
        0.1
    )
)

plt.grid(
    axis='y',
    linestyle=':',
    linewidth=0.8
)

plt.tight_layout()

plt.savefig(
    'alpha_throughput.pdf',
    bbox_inches='tight'
)

plt.show()