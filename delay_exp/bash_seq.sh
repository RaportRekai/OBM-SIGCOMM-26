# ############################################## first session ###########################################

# round_values=1
# incast_value='uniform'
# burst_percent=50
# pipeline_lag=(14 18 20 22)
# alpha=16.0

# rm -rf q_log/*

# echo "Generating workload..."
# python 'two_phase_workload_8_pipeline.py' \
#     "$burst_percent" \
#     "$incast_value" \
#     "$round_values"

# for lag in "${pipeline_lag[@]}"; do
#     echo "========================================"
#     echo "PIPELINE LAG = $lag"
#     echo "========================================"

#     echo "Running OBM latency..."
#     python 'algo_obm_latency.py' \
#         "$burst_percent" \
#         "$incast_value" \
#         "$round_values" \
#         "$lag" \
#         | tee "obm_logs/output_obm_${burst_percent}_${incast_value}_${round_values}_${lag}.txt"

# done

python plot_inversion.py