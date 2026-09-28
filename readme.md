
# Throughput Experiment

This directory contains the scripts required to run the private-buffer and shared-buffer simulations and generate the normalized throughput plots.

## Hardware Log Prerequisite

The hardware (HD) experiment logs are **not generated automatically by `run.sh`**.

Before running the experiment pipeline, the DT and OBM hardware experiments must be run manually using **Xilinx Vivado 2022.2**.

The generated hardware logs must be placed in the following directories:

```text
switch-sim-shared/master/dt_hd_logs/
switch-sim-shared/master/optimal_hd_logs/

switch-sim-private/master/dt_hd_logs/
switch-sim-private/master/optimal_hd_logs/
```

> **Note:** The OBM hardware results are stored under directories named `optimal_hd_logs`.

Each of the above directories must contain:

```text
FINAL_ALL_RESULTS_UNIFORM.txt
FINAL_ALL_RESULTS_ZIPF.txt
FINAL_ALL_RESULTS_SKEWED.txt
```

---

## Hardware Simulation

### Requirements

The hardware simulations require:

```text
Xilinx Vivado 2022.2
```

The following Vivado project archives are provided:

```text
dt_switch_shared.xpr.zip
obm_switch_shared.xpr.zip

dt_switch_private.xpr.zip
obm_switch_private.xpr.zip
```

The corresponding TCL scripts are:

```text
switch-sim-shared/tcl_script_dt.tcl
switch-sim-shared/tcl_script_obm.tcl

switch-sim-private/tcl_script_dt.tcl
switch-sim-private/tcl_script_obm.tcl
```

### 1. Extract the Vivado Project

Extract the project archive corresponding to the experiment you want to run:

| Experiment  | Vivado Project                 |
| ----------- | ------------------------------ |
| DT Private  | `dt_switch_private.xpr.zip`  |
| OBM Private | `obm_switch_private.xpr.zip` |
| DT Shared   | `dt_switch_shared.xpr.zip`   |
| OBM Shared  | `obm_switch_shared.xpr.zip`  |

Each archive contains the Vivado project required to run the corresponding hardware simulation.

### 2. Open the Project

Open **Xilinx Vivado 2022.2** and load the `.xpr` file from the extracted project.

### 3. Run the TCL Script

Once the project is open, use the **Tcl Console** in Vivado.

For a DT project, run the corresponding DT TCL script:

```tcl
source /path/to/tcl_script_dt.tcl
```

For an OBM project, run:

```tcl
source /path/to/tcl_script_obm.tcl
```

Replace `/path/to/` with the actual path to the corresponding TCL script.

Alternatively, copy and paste the contents of the TCL script directly into the Vivado Tcl Console.

The TCL scripts automatically run the required traffic distributions and burst percentages. Individual configurations do not need to be started manually.

### 4. Generated Hardware Logs

Each TCL script generates three files:

```text
FINAL_ALL_RESULTS_UNIFORM.txt
FINAL_ALL_RESULTS_ZIPF.txt
FINAL_ALL_RESULTS_SKEWED.txt
```

These files are generated in the root directory of the corresponding Vivado project.

### 5. Copy the Hardware Logs

After each Vivado simulation sweep completes, copy the generated files to the appropriate hardware-log directory.

#### DT Shared

```text
switch-sim-shared/master/dt_hd_logs/
├── FINAL_ALL_RESULTS_UNIFORM.txt
├── FINAL_ALL_RESULTS_ZIPF.txt
└── FINAL_ALL_RESULTS_SKEWED.txt
```

#### OBM Shared

```text
switch-sim-shared/master/optimal_hd_logs/
├── FINAL_ALL_RESULTS_UNIFORM.txt
├── FINAL_ALL_RESULTS_ZIPF.txt
└── FINAL_ALL_RESULTS_SKEWED.txt
```

#### DT Private

```text
switch-sim-private/master/dt_hd_logs/
├── FINAL_ALL_RESULTS_UNIFORM.txt
├── FINAL_ALL_RESULTS_ZIPF.txt
└── FINAL_ALL_RESULTS_SKEWED.txt
```

#### OBM Private

```text
switch-sim-private/master/optimal_hd_logs/
├── FINAL_ALL_RESULTS_UNIFORM.txt
├── FINAL_ALL_RESULTS_ZIPF.txt
└── FINAL_ALL_RESULTS_SKEWED.txt
```

The hardware-log processing scripts expect these exact filenames and locations.

> **Important:** The Vivado hardware simulations are not run automatically by `run.sh`. Generate and copy all required hardware logs before running the complete experiment pipeline.

---

## Processing Hardware Logs

The hardware logs are processed using:

```bash
python private_hd_log_reader.py
python shared_hd_log_reader.py
```

These scripts generate the hardware throughput CSV files used by `plt_thrpt.py` for the **DT-hw** and **OBM-hw** results.

---

## Running the Experiment

After generating and placing the hardware logs in the directories described above, run the complete experiment pipeline from the root `OBM` directory:

```bash
bash run.sh
```

The `run.sh` script performs the following steps.

### 1. Run Private-Buffer Simulations

```bash
cd switch-sim-private
bash bash_prvt.sh
cd ../
```

### 2. Run Shared-Buffer Simulations

```bash
cd switch-sim-shared
bash bash_shared_all_algos.sh
cd ../
```

### 3. Process Simulation and Hardware Results

```bash
python regex_time_compare.py
python private_hd_log_reader.py
python shared_hd_log_reader.py
```

`regex_time_compare.py` processes the simulation timing results.

`private_hd_log_reader.py` and `shared_hd_log_reader.py` process the manually generated Vivado hardware logs and generate the throughput CSV files required by the plotting script.

### 4. Generate Throughput Plots

```bash
python plt_thrpt.py _ uniform 1
python plt_thrpt.py _ zipf 1
python plt_thrpt.py _ skewed 1
```

This generates the normalized throughput plots for:

- Uniform
- Zipf
- Skewed
