round_values=1
incast_value='uniform'
burst_percent=50
buffer=(26214 20000 14000 8000 4000 2000 1000 600)
alpha=16.0

rm -rf q_log/*

for buf in "${buffer[@]}"; do
    echo "========================================"
    echo "BUFFER = $buf"
    echo "========================================"

    echo "Generating workload..."
    python 'two_phase_workload_8_page.py' \
        "$burst_percent" \
        "$incast_value" \
        "$round_values" \
        "$buf"

    echo "Running OBM..."
    python 'algo_obm_bufferdrop.py' \
        "$burst_percent" \
        "$incast_value" \
        "$round_values" \
        "$buf" \
        | tee "obm_logs/output_obm_${burst_percent}_${incast_value}_${round_values}_${buf}.txt"

    echo "Running Optimal..."
    python 'algo_optimal_attmpt.py' \
        "$burst_percent" \
        "$incast_value" \
        "$round_values" \
        "$buf" \
        | tee "optimal_logs/output_optimal_${burst_percent}_${incast_value}_${round_values}_${buf}.txt"


done

python algo_parse_thrgpt.py