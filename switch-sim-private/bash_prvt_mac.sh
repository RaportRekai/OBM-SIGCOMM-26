#!/bin/bash

round_values=1
burst_percent=(20 30 40 50)
alpha=16.0

rm -rf q_log/*

for incast_value in uniform zipf skewed; do

    echo "=================================================="
    echo "INCAST DISTRIBUTION: $incast_value"
    echo "=================================================="

    # --------------------------------------------------
    # Generate workloads for this incast distribution
    # --------------------------------------------------
    for i in ${!burst_percent[@]}; do
        burst=${burst_percent[$i]}

        python 'master/two_phase_workload_8.py' \
            "$burst" \
            "$incast_value" \
            "$round_values"

        echo "Generated workload: burst=$burst incast=$incast_value round=$round_values"
    done


    # --------------------------------------------------
    # Run each burst sequentially
    # but algorithms for that burst run in parallel
    # --------------------------------------------------
    for i in ${!burst_percent[@]}; do
        burst=${burst_percent[$i]}

        echo "--------------------------------------------------"
        echo "Running burst=$burst, incast=$incast_value"
        echo "--------------------------------------------------"

        python 'algo_abm.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            "$alpha" \
            | tee "master/abm_logs/output_abm_${burst}_${incast_value}_${round_values}_${alpha}.txt" &

        python 'algo_dt.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            "$alpha" \
            | tee "master/dt_logs/output_dt_${burst}_${incast_value}_${round_values}_${alpha}.txt" &

        python 'algo_obm_bufferdrop.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            | tee "master/obm_logs/output_obm_${burst}_${incast_value}_${round_values}.txt" &

        python 'algo_spreal.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            | tee "master/spreal_logs/output_obm_${burst}_${incast_value}_${round_values}.txt" &

        python 'algo_occamy.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            16 \
            | tee "master/occamy_logs/output_occamy_${burst}_${incast_value}_${round_values}_${alpha}.txt" &

        python 'algo_optimal_attmpt.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            | tee "master/optimal_logs/output_optimal_${burst}_${incast_value}_${round_values}.txt" &

        python 'algo_credence.py' \
            "$burst" \
            "$incast_value" \
            "$round_values" \
            16 

        # Wait for all algorithms for this burst to finish
        wait

        echo "Finished burst=$burst, incast=$incast_value"
    done

    echo "Finished all experiments for $incast_value"
done

echo "=================================================="
echo "ALL EXPERIMENTS COMPLETE"
echo "=================================================="