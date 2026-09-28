# Experiment 10: FPGA Resource Utilization and Maximum Frequency

This experiment evaluates the FPGA resource utilization and maximum achievable clock frequency of OBM for different numbers of ports and link bandwidths.

Two separate sets of Vivado projects are provided:

```text
resource_util/
freq/
```

- `resource_util/` contains the projects used to reproduce the **LUT and Flip-Flop (FF) utilization** results.
- `freq/` contains the projects used to reproduce the **maximum frequency** results.

The values obtained from Vivado should be compared against the values provided in:

```text
res.csv
```

After verifying the results, the plots can be generated using:

```text
plot_resource_util.py
```

---

## Requirements

The hardware projects should be implemented using:

```text
Xilinx Vivado 2022.2
```

The Python dependencies required for plotting are:

```bash
pip install numpy pandas matplotlib
```

---

# 1. Resource Utilization

The projects used for the resource utilization experiment are located in:

```text
resource_util/
```

The following projects are provided:

```text
resource_util/
├── obm_switch_2_port_10G.xpr.zip
├── obm_switch_2_port_25G.xpr.zip
├── obm_switch_2_port_50G.xpr.zip
├── obm_switch_2_port_100G.xpr.zip
├── obm_switch_4_port_10G.xpr.zip
├── obm_switch_4_port_25G.xpr.zip
├── obm_switch_4_port_50G.xpr.zip
├── obm_switch_8_port_10G.xpr.zip
├── obm_switch_8_port_25G.xpr.zip
└── obm_switch_16_port_10G.xpr.zip
```

Each archive corresponds to a specific combination of:

- Number of switch ports
- Link bandwidth

## Run the Resource Utilization Experiments

For each project:

1. Extract the corresponding `.xpr.zip` archive.
2. Open the extracted `.xpr` project using **Xilinx Vivado 2022.2**.
3. Run **Implementation**.
4. Open the implemented design.
5. Open the **Utilization Report / Implementation Summary**.
6. Record the number of:
   - LUTs
   - Flip-Flops (FFs)
7. Compare the values with the corresponding `# LUT` and `# FF` entries in `res.csv`.

Repeat this process for all projects under `resource_util/`.

---

# 2. Maximum Frequency

The maximum-frequency experiment uses a separate set of Vivado projects located in:

```text
freq/
```

The following projects are provided:

```text
freq/
├── obm_switch_2_port_freq.xpr.zip
├── obm_switch_4_port_freq.xpr.zip
├── obm_switch_8_port_freq.xpr.zip
└── obm_switch_16_port_freq.xpr.zip
```

These projects should be used to reproduce the timing results. Do **not** use the projects in `resource_util/` to reproduce the maximum-frequency results.

There is **one frequency experiment for each port count**, independent of the bandwidth configuration.

Therefore, **all bandwidth configurations with the same number of ports use the same WNS value**.

For example:

```text
2-port:
    10G  -> WNS = 0.512 ns
    25G  -> WNS = 0.512 ns
    50G  -> WNS = 0.512 ns
    100G -> WNS = 0.512 ns

4-port:
    10G  -> WNS = 0.449 ns
    25G  -> WNS = 0.449 ns
    50G  -> WNS = 0.449 ns

8-port:
    10G  -> WNS = 0.188 ns
    25G  -> WNS = 0.188 ns

16-port:
    10G  -> WNS = 0.001 ns
```

For example, the WNS obtained from `obm_switch_2_port_freq.xpr.zip` is used for all 2-port configurations (10G, 25G, 50G, and 100G).

Similarly, the WNS obtained from the 4-port frequency project is used for all 4-port bandwidth configurations.

The WNS values are obtained from the projects in `freq/`, while the LUT and FF values for each individual port/bandwidth configuration are obtained from the projects in `resource_util/`.

## Run the Frequency Experiments

For each project:

1. Extract the corresponding `.xpr.zip` archive.
2. Open the extracted `.xpr` project using **Xilinx Vivado 2022.2**.
3. Run **Implementation**.
4. Open the implemented design.
5. Open the **Timing Summary**.
6. Record the **WNS (Worst Negative Slack)**.
7. Use the obtained WNS value for all bandwidth configurations corresponding to that port count.
8. Verify that the WNS matches the corresponding entries in `res.csv`.

Repeat this process for:

```text
2 ports
4 ports
8 ports
16 ports
```

---

# 3. Verify `res.csv`

The implementation results used by the plotting script are stored in:

```text
res.csv
```

The expected format is:

```csv
# Ports,Bandwidth,WNS,# LUT,# FF
2,10,0.512,251,314
2,25,0.512,251,314
2,50,0.512,251,442
2,100,0.512,251,698
4,10,0.449,573,488
4,25,0.449,573,488
4,50,0.449,573,744
8,10,0.188,1134,968
8,25,0.188,1134,968
16,10,0.001,4634,2877
```

The values in `res.csv` come from two different sets of Vivado experiments:

| Value     | Vivado Projects    |
| --------- | ------------------ |
| `# LUT` | `resource_util/` |
| `# FF`  | `resource_util/` |
| `WNS`   | `freq/`          |

> **Note:** WNS is determined by the number of ports in this experiment. Therefore, all rows in `res.csv` with the same `# Ports` value use the same WNS obtained from the corresponding project in `freq/`. LUT and FF values are obtained separately for each port/bandwidth configuration from `resource_util/`.

Verify that the implementation reports from the provided Vivado projects match the values recorded in `res.csv`.

---

# 4. Maximum Frequency Calculation

The frequency projects use a constrained clock period of:

```text
2.5 ns
```

The maximum achievable frequency is calculated from the WNS obtained from the projects under `freq/`.

The effective minimum clock period is calculated as:

```text
T_min = 2.5 ns - WNS
```

The maximum frequency is then calculated as:

```text
F_max (MHz) = 1000 / T_min
```

Therefore:

```text
F_max (MHz) = 1000 / (2.5 - WNS)
```

For example, for the 2-port design:

```text
WNS = 0.512 ns

T_min = 2.5 - 0.512
      = 1.988 ns

F_max = 1000 / 1.988
      ≈ 503 MHz
```

This calculation is performed automatically by `plot_resource_util.py`.

Because all bandwidth configurations for a given port count use the same WNS, they also have the same calculated maximum frequency.

---

# 5. Resource Utilization Calculation

The plotting script normalizes the LUT and Flip-Flop usage using:

```text
LUT denominator = 11822.40
FF denominator  = 23644.80
```

The normalized resource utilization is calculated as:

```text
LUT Utilization = # LUT / 11822.40
FF Utilization  = # FF / 23644.80
```

These calculations are performed automatically by `plot_resource_util.py`.

---

# 6. Generate the Plots

After verifying the Vivado implementation results against `res.csv`, run:

```bash
python plot_resource_util.py
```

The script reads:

```text
res.csv
```

and generates:

```text
max_freq_plot.png
lut_ff_utilization_combined.png
```

## Maximum Frequency Plot

```text
max_freq_plot.png
```

shows the maximum achievable clock frequency calculated from the WNS obtained from the projects in:

```text
freq/
```

The black horizontal markers in the figure indicate the target clock speeds required for the corresponding bandwidth configurations.

## Resource Utilization Plot

```text
lut_ff_utilization_combined.png
```

shows the normalized:

- LUT utilization
- Flip-Flop utilization

for the different port-count and bandwidth configurations.

The LUT and FF values are obtained from the projects in:

```text
resource_util/
```

---

# Reproducing Experiment 10

The complete reproduction procedure is summarized below.

## Resource Utilization

```text
resource_util/
        |
        v
Extract each Vivado project
        |
        v
Run Implementation
        |
        v
Open Utilization Report
        |
        v
Record LUT and FF counts
        |
        v
Compare with res.csv
```

Run this procedure for every project under `resource_util/`.

## Maximum Frequency

```text
freq/
        |
        v
Extract each Vivado project
        |
        v
Run Implementation
        |
        v
Open Timing Summary
        |
        v
Record WNS
        |
        v
Use the WNS for all bandwidths
with the same port count
        |
        v
Compare with res.csv
```

Run this procedure for the 2-port, 4-port, 8-port, and 16-port frequency projects.

## Generate the Figures

Finally, run:

```bash
python plot_resource_util.py
```

The expected output files are:

```text
max_freq_plot.png
lut_ff_utilization_combined.png
```
