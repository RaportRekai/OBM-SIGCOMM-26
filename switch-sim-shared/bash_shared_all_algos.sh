round_values=1
incast_value='skewed'
burst_percent=(20 30 40 50)
alpha=(16.0)
find "q_log" -maxdepth 1 -type f -name '*.csv' -delete

for i in ${!burst_percent[@]}; do
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!burst_percent[@]}; do
    echo "started running abm for ${burst_percent[$i]}"
    taskset -c $((7*i+0)) python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+1)) python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+2)) python 'algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+3)) python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+4)) python 'algo_spreal.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/spreal_logs/output_spreal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+5)) python 'algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/optimal_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+6)) python 'algo_credence_trainer.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee  master/credence_logs/output_credence_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt
done
wait

round_values=1
incast_value='uniform'
burst_percent=(20 30 40 50)
alpha=(16.0)
find "q_log" -maxdepth 1 -type f -name '*.csv' -delete

for i in ${!burst_percent[@]}; do
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!burst_percent[@]}; do
    echo "started running abm for ${burst_percent[$i]}"
    taskset -c $((7*i+0)) python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+1)) python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+2)) python 'algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+3)) python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+4)) python 'algo_spreal.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/spreal_logs/output_spreal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+5)) python 'algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/optimal_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+6)) python 'algo_credence_trainer.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee  master/credence_logs/output_credence_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt
done
wait

round_values=1
incast_value='zipf'
burst_percent=(20 30 40 50)
alpha=(16.0)
find "q_log" -maxdepth 1 -type f -name '*.csv' -delete

for i in ${!burst_percent[@]}; do
    /bin/python 'master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!burst_percent[@]}; do
    echo "started running abm for ${burst_percent[$i]}"
    taskset -c $((7*i+0)) python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+1)) python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+2)) python 'algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+3)) python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((7*i+4)) python 'algo_spreal.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/spreal_logs/output_spreal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+5)) python 'algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee master/optimal_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((7*i+6)) python 'algo_credence_trainer.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee  master/credence_logs/output_credence_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt
done
wait
