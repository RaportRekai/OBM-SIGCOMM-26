round_values=1
incast_value='uniform'
incast_set=(0 1 2)
alpha=(16.0)

rm -rf q_log/*

# Generate workloads first
for i in ${!incast_set[@]}; do
    python './two_phase_workload_8_show_diff.py' \
        50 \
        "$incast_value" \
        "$round_values" \
        "${incast_set[$i]}"

    echo "Generated workload for incast_set=${incast_set[$i]}"
done

# Run experiments serially
for i in ${!incast_set[@]}; do
    incast="${incast_set[$i]}"

    echo "Running SP-Ideal for incast_set=$incast"
    python 'algo_spideal.py' \
        50 \
        "$incast_value" \
        "$round_values" \
        "$incast" \
        | tee "spideal_logs/output_spideal_50_${incast_value}_${round_values}_incast_set${incast}.txt"

    echo "Running OBM for incast_set=$incast"
    python 'algo_obm_bufferdrop.py' \
        50 \
        "$incast_value" \
        "$round_values" \
        "$incast" \
        | tee "obm_logs/output_obm_50_${incast_value}_${round_values}_incast_set${incast}.txt"

    echo "Running Optimal for incast_set=$incast"
    python 'algo_optimal_attmpt.py' \
        50 \
        "$incast_value" \
        "$round_values" \
        "$incast" \
        | tee "optimal_logs/output_optimal_50_${incast_value}_${round_values}_incast_set${incast}.txt"
done