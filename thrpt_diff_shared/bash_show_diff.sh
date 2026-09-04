############################################## first session ###########################################

round_values=1
incast_value='uniform'
incast_set=(0 1 2)
alpha=(16.0)

rm -rf q_log/*

for i in ${!incast_set[@]}; do
    python './two_phase_workload_8_show_diff.py' 50 $incast_value $round_values ${incast_set[$i]}
    #/bin/python 'LQD/master/two_phase_workload_8_show_diff.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating master/two_phase_workload_8_last_s.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!incast_set[@]}; do
    #echo "started running abm for ${burst_percent[$i]}"
    #taskset -c $((6*i+0)) /bin/python 'algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    #taskset -c $((6*i+1)) /bin/python 'algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee  master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    #taskset -c $((6*i+2)) /bin/python 'LQD/algo_obm_latency.py' ${burst_percent[$i]} $incast_value $round_values | tee  LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    taskset -c $((6*i+3)) python 'algo_spideal.py' 50 $incast_value $round_values ${incast_set[$i]} | tee  spideal_logs/output_spideal_50_${incast_value}_${round_values}_incast_set${incast_set[$i]}.txt &
    taskset -c $((6*i+4)) python 'algo_obm_bufferdrop.py' 50 $incast_value $round_values ${incast_set[$i]} | tee  obm_logs/output_obm_50_${incast_value}_${round_values}_incast_set${incast_set[$i]}.txt &
    
    #taskset -c $((6*i+3)) /bin/python 'algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values 16 | tee  master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
    taskset -c $((6*i+5)) python 'algo_optimal_attmpt.py' 50 $incast_value $round_values ${incast_set[$i]} | tee  optimal_logs/output_optimal_50_${incast_value}_${round_values}_incast_set${incast_set[$i]}.txt &
    #taskset -c $((6*i+5)) /bin/python 'algo_credence.py' ${burst_percent[$i]} $incast_value $round_values 16
done
wait

# round_values=1
# incast_value='skewed'
# burst_percent=(10 20 30 40 50)
# alpha=(16.0)
# find "/home/dan/LQD/q_log" -maxdepth 1 -type f -name '*.csv' -delete

# for i in ${!burst_percent[@]}; do
#     /bin/python 'LQD/master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
#     echo "Generating LQD/master/two_phase_workload_8.py ${burst_percent[$i]} $incast_value $round_values"
# done

# for i in ${!burst_percent[@]}; do
#     echo "started running abm for ${burst_percent[$i]}"
#     taskset -c $((6*i+0)) /bin/python 'LQD/algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee LQD/master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
#     taskset -c $((6*i+1)) /bin/python 'LQD/algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee LQD/master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
#     taskset -c $((6*i+2)) /bin/python 'LQD/algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values  | tee LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
#     taskset -c $((6*i+3)) /bin/python 'LQD/algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee LQD/master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
#     taskset -c $((6*i+4)) /bin/python 'LQD/algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee LQD/master/lqd_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
# done
# wait

# round_values=1
# incast_value='zipf'
# burst_percent=(10 20 30 40 50)
# alpha=(16.0)
# find "/home/dan/LQD/q_log" -maxdepth 1 -type f -name '*.csv' -delete

# for i in ${!burst_percent[@]}; do
#     /bin/python 'LQD/master/two_phase_workload_8.py' ${burst_percent[$i]} $incast_value $round_values
#     echo "Generating LQD/master/two_phase_workload_8.py ${burst_percent[$i]} $incast_value $round_values"
# done

# for i in ${!burst_percent[@]}; do
#     echo "started running abm for ${burst_percent[$i]}"
#     taskset -c $((5*i+0)) /bin/python 'LQD/algo_abm.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee LQD/master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
#     taskset -c $((5*i+1)) /bin/python 'LQD/algo_dt.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee LQD/master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
#     taskset -c $((5*i+2)) /bin/python 'LQD/algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values  | tee LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
#     taskset -c $((5*i+3)) /bin/python 'LQD/algo_occamy.py' ${burst_percent[$i]} $incast_value $round_values $alpha | tee LQD/master/occamy_logs/output_occamy_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha}.txt &
#     # taskset -c $((4*i+3)) /bin/python 'LQD/algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values  | tee LQD/master/lqd_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
# done
# wait



############################################## second session #######################################

# round_values=10
# incast_value='skewed'
# burst_percent=30
# alpha=(0.2 0.5 1.0 2.0 8.0 14.0)

# /bin/python 'LQD/master/heyy.py' $burst_percent $incast_value $round_values
# echo "Generating LQD/master/heyy.py $burst_percent $incast_value $round_values"

# for i in ${!alpha[@]}; do
#     echo "started running abm for ${alpha[$i]}"
#     taskset -c $((4*i+1)) /bin/python 'LQD/algo_abm.py' $burst_percent $incast_value $round_values ${alpha[$i]} | tee LQD/master/abm_logs/output_abm_${burst_percent}_${incast_value}_${round_values}_${alpha[$i]}.txt &
#     taskset -c $((4*i+2)) /bin/python 'LQD/algo_dt.py' $burst_percent $incast_value $round_values ${alpha[$i]} | tee LQD/master/dt_logs/output_dt_${burst_percent}_${incast_value}_${round_values}_${alpha[$i]}.txt &
# done
# wait

# # # # ############################################## third session #######################################


# round_values=10
# incast_value='uniform'
# burst_percent=30
# alpha=(0.2 0.5 1.0 2.0 8.0 14.0)

# /bin/python 'LQD/master/heyy.py' $burst_percent $incast_value $round_values
# echo "Generating LQD/master/heyy.py $burst_percent $incast_value $round_values"

# for i in ${!alpha[@]}; do
#     echo "started running abm for ${alpha[$i]}"
#     taskset -c $((4*i+1)) /bin/python 'LQD/algo_abm.py' $burst_percent $incast_value $round_values ${alpha[$i]} | tee LQD/master/abm_logs/output_abm_${burst_percent}_${incast_value}_${round_values}_${alpha[$i]}.txt &
#     taskset -c $((4*i+2)) /bin/python 'LQD/algo_dt.py' $burst_percent $incast_value $round_values ${alpha[$i]} | tee LQD/master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}_${alpha[$i]}.txt &
# done
# wait
