
incast="uniform"  # Set incast to "skewed"

# Define burst values
burst_values=40
alpha=(0.5 1.0 2.0 4.0 6.0 8.0 10.0 12.0 14.0)

echo "Running with burst=$burst_values "
python heyy.py "$incast" "$burst_values"

# Loop through burst values and assign each to a separate core (0-4)
for i in ${!alpha[@]}; do
    # Run algorithms with the corresponding burst value
    echo "Running with burst= ${alpha[$i]}"
    taskset -c $((i*2+0)) python algo_dt.py "$burst_values" "${alpha[$i]}" | tee master/dt_logs/output_dt_${incast}_${burst_values}_${alpha[$i]}.txt &
    # python algo_dt.py "$burst_values" "${alpha[$i]}" | tee master/dt_logs/output_dt_${incast}_${burst_values}_${alpha[$i]}.txt &
done

# Wait for all background processes to finish
wait

python plot_thpt_alpha.py

