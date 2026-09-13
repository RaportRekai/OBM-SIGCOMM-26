#!/bin/bash

mkdir -p junk_logs

taskset -c 0 bash run_abm.sh        > junk_logs/abm.txt        2>&1 &
taskset -c 1 bash run_credence.sh   > junk_logs/credence.txt   2>&1 &
taskset -c 2 bash run_dt.sh         > junk_logs/dt.txt         2>&1 &
taskset -c 3 bash run_lqd_ideal.sh  > junk_logs/lqd_ideal.txt  2>&1 &
taskset -c 4 bash run_lqd_spreal.sh > junk_logs/lqd_spreal.txt 2>&1 &
taskset -c 5 bash run_lqd.sh        > junk_logs/lqd.txt        2>&1 &
taskset -c 6 bash run_obm.sh        > junk_logs/obm.txt        2>&1 &
taskset -c 7 bash run_occamy.sh     > junk_logs/occamy.txt     2>&1 &

wait

echo "All simulations finished."