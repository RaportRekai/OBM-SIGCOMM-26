############################################## first session ###########################################
# at the top of your script
rm -f -- ./*.csv

round_values=1
incast_value='uniform'
burst_percent=(30)
alpha=(0.3 1.0 2.0 4.0 6.0 8.0 10.0 12.0 14.0)

for i in ${!burst_percent[@]}; do
    /bin/python 'LQD/master/heyy.py' ${burst_percent[$i]} $incast_value $round_values
    echo "Generating LQD/master/heyy.py ${burst_percent[$i]} $incast_value $round_values"
done

for i in ${!alpha[@]}; do
    echo "started running abm for ${alpha[$i]}"
    # taskset -c $((2*i+0)) /bin/python 'LQD/algo_abm.py' $burst_percent $incast_value $round_values ${alpha[$i]} | tee LQD/master/abm_logs/output_abm_${burst_percent}_${incast_value}_${round_values}_${alpha[$i]}.txt &
    taskset -c $((2*i+1)) /bin/python 'LQD/algo_dt.py' $burst_percent $incast_value $round_values ${alpha[$i]} | tee LQD/master/dt_logs/output_dt_${burst_percent}_${incast_value}_${round_values}_${alpha[$i]}.txt &
    #taskset -c $((4*i+3)) /bin/python 'LQD/algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/LQD_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    #taskset -c $((3*i+2)) /bin/python 'LQD/algo_obm_bufferdrop.py' $burst_percent $incast_value $round_values | tee LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
done
wait

############################################## second session #######################################

# round_values=10
# incast_value='skewed'
# burst_percent=(10 20 30 40 50)

# for i in ${!burst_percent[@]}; do
#     /bin/python 'LQD/master/heyy.py' ${burst_percent[$i]} $incast_value $round_values
#     echo "Generating LQD/master/heyy.py ${burst_percent[$i]} $incast_value $round_values"
# done

# for i in ${!burst_percent[@]}; do
#     echo "started running abm for ${burst_percent[$i]}"
#     taskset -c $((2*i+0)) /bin/python 'LQD/algo_abm.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
#     taskset -c $((2*i+1)) /bin/python 'LQD/algo_dt.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    #taskset -c $((4*i+3)) /bin/python 'LQD/algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/LQD_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
    #taskset -c $((4*i+4)) /bin/python 'LQD/algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
# done
# wait

# # # # ############################################## third session #######################################


# round_values=10
# incast_value='uniform'
# burst_percent=(10 20 30 40 50 60)

# for i in ${!burst_percent[@]}; do
#     /bin/python 'LQD/master/heyy.py' ${burst_percent[$i]} $incast_value $round_values
#     echo "Generating LQD/master/heyy.py ${burst_percent[$i]} $incast_value $round_values"
# done

# for i in ${!burst_percent[@]}; do
#     echo "started running abm for ${burst_percent[$i]}"
#     taskset -c $((2*i+0)) /bin/python 'LQD/algo_abm.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/abm_logs/output_abm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
#     taskset -c $((2*i+1)) /bin/python 'LQD/algo_dt.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/dt_logs/output_dt_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
#     #taskset -c $((4*i+3)) /bin/python 'LQD/algo_optimal_attmpt.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/LQD_logs/output_optimal_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
#     #taskset -c $((4*i+4)) /bin/python 'LQD/algo_obm_bufferdrop.py' ${burst_percent[$i]} $incast_value $round_values | tee LQD/master/obm_logs/output_obm_${burst_percent[$i]}_${incast_value}_${round_values}.txt &
# done
# wait
