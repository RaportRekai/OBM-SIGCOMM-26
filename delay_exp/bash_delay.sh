############################################## first session ###########################################

round_values=1
incast_value='uniform'
burst_percent=(50) # 20 30 40 50)
# pipeline_lag=(2 4 6 20)
# pipeline_lag=(12 14 16 18 20 22)
pipeline_lag=(14 18 20 22) # extend 14 to 12 and 16
alpha=(16.0)

rm -rf q_log/*

for i in ${!burst_percent[@]}; do
    python 'two_phase_workload_8_pipeline.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8_last_s.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!pipeline_lag[@]}; do
     taskset -c $((6*i+2)) python 'algo_obm_latency.py' ${burst_percent} $incast_value $round_values ${pipeline_lag[$i]}| tee  obm_logs/output_obm_${burst_percent}_${incast_value}_${round_values}_${pipeline_lag[$i]}.txt &
done
wait

