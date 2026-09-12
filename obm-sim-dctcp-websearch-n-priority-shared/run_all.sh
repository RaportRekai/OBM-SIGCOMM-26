#!/bin/bash

mkdir -p junk_logs

rm -rf net-sim-abm/logs && mkdir -p logs
rm -rf net-sim-obm/logs && mkdir -p logs
rm -rf net-sim-dt/logs && mkdir -p logs
rm -rf net-sim-occamy/logs && mkdir -p logs
rm -rf net-sim-credence/logs && mkdir -p logs
rm -rf net-sim-lqd/logs && mkdir -p logs
rm -rf net-sim-spreal/logs && mkdir -p logs
rm -rf net-sim-lqd-ideal/logs && mkdir -p logs

mkdir -p net-sim-abm/logs
mkdir -p net-sim-obm/logs
mkdir -p net-sim-dt/logs
mkdir -p net-sim-occamy/logs
mkdir -p net-sim-credence/logs
mkdir -p net-sim-lqd/logs
mkdir -p net-sim-spreal/logs
mkdir -p net-sim-lqd-ideal/logs


mkdir -p net-sim-abm/prev_logs/all_logs
mkdir -p net-sim-obm/prev_logs/all_logs
mkdir -p net-sim-dt/prev_logs/all_logs
mkdir -p net-sim-occamy/prev_logs/all_logs
mkdir -p net-sim-credence/prev_logs/all_logs
mkdir -p net-sim-lqd/prev_logs/all_logs
mkdir -p net-sim-spreal/prev_logs/all_logs
mkdir -p net-sim-lqd-ideal/prev_logs/all_logs

touch stats_abm.txt
touch stats_obm.txt
touch stats_dt.txt
touch stats_credence.txt
touch stats_lqd.txt
touch stats_spreal.txt
touch stats_lqd_ideal.txt
touch stats_occamy.txt

export PYTHONUNBUFFERED=1

taskset -c 0 bash run_abm.sh        > junk_logs/abm.txt &

taskset -c 1 bash run_credence.sh   > junk_logs/credence.txt &

taskset -c 2 bash run_dt.sh         > junk_logs/dt.txt &

taskset -c 3 bash run_lqd_ideal.sh  > junk_logs/lqd_ideal.txt &

taskset -c 4 bash run_spreal.sh     > junk_logs/lqd_spreal.txt &

taskset -c 5 bash run_lqd.sh        > junk_logs/lqd.txt &

taskset -c 6 bash run_obm.sh        > junk_logs/obm.txt &

taskset -c 7 bash run_occamy.sh     > junk_logs/occamy.txt &

wait

echo "All simulations finished."