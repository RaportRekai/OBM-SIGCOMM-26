# OBM: Optimal Shared Packet Buffer Management in Switches

This repository contains the artifacts for the paper:

**OBM: Optimal Shared Packet Buffer Management in Switches**
ACM SIGCOMM 2026

The artifact is organized using one Git branch per figure in the paper.
For example, the branch `fig-21` contains the code and instructions required
to reproduce **Figure 21**.

Each figure branch contains its own `README.md` with detailed instructions
for running the corresponding experiment and generating the result/plot.

---

## 1. Repository Organization

The `master` branch contains the common environment setup.

The experiments are organized into the following branches:

```text
fig-2
fig-3
fig-9
fig-10
fig-11
fig-12
fig-13
fig-14
fig-15
fig-16
fig-17
fig-18
fig-19
fig-20
fig-21
```

The branch name directly corresponds to the figure number in the paper.

For example:

```text
fig-9  -> Figure 9
fig-10 -> Figure 10
fig-21 -> Figure 21
```

---

## 2. Clone the Repository

Clone the artifact repository and enter the repository directory.

```bash
git clone https://github.com/RaportRekai/OBM-SIGCOMM-26.git
cd OBM-SIGCOMM-26
```

Make sure that you start from the `master` branch:

```bash
git switch master
```

For older Git versions, the equivalent command is:

```bash
git checkout master
```

---

## 3. Environment Setup

The common Python environment only needs to be created **once** before
running the experiments.

From the `master` branch, run the provided environment setup script.

the script is named `create_virtual_env.sh`:

```bash
chmod +x create_virtual_env.sh
./create_virtual_env.sh
```

The setup script performs the following operations:

```bash
sudo apt update
sudo apt install python3.10-venv

python3 -m venv obm

source obm/bin/activate

python -m pip install --upgrade pip

pip install numpy matplotlib pandas joblib scikit-learn
```

After setup, activate the environment with:

```bash
source obm/bin/activate
```

The same virtual environment can be reused while switching between the
different figure branches.

> **Important:** Do not recreate the virtual environment for every figure.
> Create it once on `master`, activate it, and then switch to the desired
> figure branch.

---

## 4. Reproducing the Paper Figures

We recommend evaluating the figures in the following order:

```text
Figure 21
Figure 20
Figure 19
Figure 18
Figure 17
Figure 16
Figure 15
Figure 13
Figure 12
Figure 11
Figure 14
Figure 2
Figure 3
Figure 9
Figure 10
```

This is the recommended artifact-evaluation order rather than numerical
figure order.

For each figure:

1. Switch to the corresponding branch.
2. Read the `README.md` in that branch.
3. Follow the instructions in that README.
4. Run the experiment and/or plotting scripts described there.
5. Compare the generated result with the corresponding figure in the paper.

---

## 5. Example: Reproducing Figure 21

Activate the Python environment:

```bash
source obm/bin/activate
```

Switch to the Figure 21 branch:

```bash
git switch fig-21
```

Then read the branch-specific instructions:

```bash
cat README.md
```

Follow the instructions in that README to run the experiment and generate
Figure 21.

After completing Figure 21, move to Figure 20:

```bash
git switch fig-20
cat README.md
```

Continue in the same manner for the remaining figures.


---

## 7. Quickly Switching Between Experiments

Once the environment has been created, the general workflow for every
experiment is simply:

```bash
source obm/bin/activate

git switch fig-<figure-number>

cat README.md
```

For example:

```bash
git switch fig-17
cat README.md
```

Do **not** use:

```bash
git branch fig-17
```

The `fig-*` branches are already part of this repository.
`git branch` is used to create a new local branch, whereas `git switch`
selects the existing experiment branch.

---

## 8. Mapping Branches to Paper Experiments

| Branch     | Paper Figure | Experiment                                                              |
| ---------- | -----------: | ----------------------------------------------------------------------- |
| `fig-2`  |     Figure 2 | DT throughput versus alpha                                              |
| `fig-3`  |     Figure 3 | Single versus multiple priority-class behavior                          |
| `fig-9`  |     Figure 9 | Switch throughput under different traffic distributions and burst sizes |
| `fig-10` |    Figure 10 | FPGA resource utilization and clock-speed scaling                       |
| `fig-11` |    Figure 11 | Incast / DCTCP — single priority class                                 |
| `fig-12` |    Figure 12 | Incast / SWIFT — single priority class                                 |
| `fig-13` |    Figure 13 | Websearch / DCTCP — single priority class                              |
| `fig-14` |    Figure 14 | Websearch / SWIFT — single priority class                              |
| `fig-15` |    Figure 15 | Incast / DCTCP — three priority classes                                |
| `fig-16` |    Figure 16 | Incast / SWIFT — three priority classes                                |
| `fig-17` |    Figure 17 | Websearch / DCTCP — three priority classes                             |
| `fig-18` |    Figure 18 | Websearch / SWIFT — three priority classes                             |
| `fig-19` |    Figure 19 | Priority-first versus fairness-first push-out behavior                  |
| `fig-20` |    Figure 20 | Priority-inversion stress test                                          |
| `fig-21` |    Figure 21 | Packet-corruption stress test                                           |

Detailed commands, dependencies, expected outputs, and plotting instructions
are provided in the `README.md` of each corresponding branch.

---

## 9. Hardware Experiments

Some experiments contain FPGA/Vivado components and therefore cannot be
reproduced using the Python environment alone.

For those branches, please follow the branch-specific `README.md` carefully.
The README identifies the required Vivado projects, scripts, and any steps
that must be run manually.

Software simulation and plotting instructions are also described separately
inside the relevant figure branch.

---

## 10. Troubleshooting

### Python environment is not active

Run:

```bash
source obm/bin/activate
```

You should then see `(obm)` in the shell prompt.

### Verify the current experiment branch

Run:

```bash
git branch --show-current
```

For example:

```text
fig-21
```

means that the repository is currently configured for the Figure 21
experiment.

### Return to the main branch

```bash
git switch master
```

### List all experiment branches

```bash
git branch -a
```

If a remote branch has not yet been created locally, it can normally be
checked out directly using:

```bash
git switch fig-<figure-number>
```

Git will create the corresponding local tracking branch automatically.

---

## 12. Artifact Evaluation Order Summary

For convenience, the recommended order is:

```text
fig-21
   ↓
fig-20
   ↓
fig-19
   ↓
fig-18
   ↓
fig-17
   ↓
fig-16
   ↓
fig-15
   ↓
fig-13
   ↓
fig-12
   ↓
fig-11
   ↓
fig-14
   ↓
fig-2
   ↓
fig-3
   ↓
fig-9
   ↓
fig-10
```

Please use the `README.md` contained in each branch as the authoritative
instructions for reproducing that particular figure.
