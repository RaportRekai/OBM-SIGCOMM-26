############################################## first session ###########################################

round_values=1
incast_value='uniform'
burst_percent=(20 30 40 50)
alpha=(16.0)

rm -rf q_log/*

for i in ${!burst_percent[@]}; do
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8_last_s.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!burst_percent[@]}; do
    #echo "started running abm for ${burst_percent[$i]}"
    taskset -c $((7*i+0)) /bin/python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+1)) /bin/python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    # taskset -c $((7*i+2)) /bin/python 'LQD/algo_obm_latency.py' ${burst_percent[$i]} $incast_value $round_values 10| tee  LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+3)) /bin/python 'algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values | tee  master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+4)) /bin/python 'algo_spreal.py' ${burst_percent[$i]} $incast_value $round_values | tee  master/spreal_logs/output_spreal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+5)) /bin/python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+6)) /bin/python 'algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee  master/optimal_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+2)) /bin/python 'algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16 
    #taskset -c $((6*i+5)) /bin/python 'LQD/algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16
done
wait

############################################## first session ###########################################

round_values=1
incast_value='zipf'
burst_percent=(20 30 40 50)
alpha=(16.0)

rm -rf q_log/*

for i in ${!burst_percent[@]}; do
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8_last_s.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!burst_percent[@]}; do
    #echo "started running abm for ${burst_percent[$i]}"
    taskset -c $((7*i+0)) /bin/python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+1)) /bin/python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    # taskset -c $((7*i+2)) /bin/python 'LQD/algo_obm_latency.py' ${burst_percent[$i]} $incast_value $round_values 10| tee  LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+3)) /bin/python 'algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values | tee  master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+4)) /bin/python 'algo_spreal.py' ${burst_percent[$i]} $incast_value $round_values | tee  master/spreal_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+5)) /bin/python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+6)) /bin/python 'algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee  master/optimal_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+2)) /bin/python 'algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16 
    #taskset -c $((6*i+5)) /bin/python 'LQD/algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16
done
wait

############################################## first session ###########################################

round_values=1
incast_value='skewed'
burst_percent=(20 30 40 50)
alpha=(16.0)

rm -rf q_log/*

for i in ${!burst_percent[@]}; do
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8_last_s.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!burst_percent[@]}; do
    #echo "started running abm for ${burst_percent[$i]}"
    taskset -c $((7*i+0)) /bin/python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+1)) /bin/python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    # taskset -c $((7*i+2)) /bin/python 'LQD/algo_obm_latency.py' ${burst_percent[$i]} $incast_value $round_values 10| tee  LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+3)) /bin/python 'algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values | tee  master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+4)) /bin/python 'algo_spreal.py' ${burst_percent[$i]} $incast_value $round_values | tee  master/spreal_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+5)) /bin/python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+6)) /bin/python 'algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee  master/optimal_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+2)) /bin/python 'algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16 
    #taskset -c $((6*i+5)) /bin/python 'LQD/algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16
done
wait