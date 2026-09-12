cd obm-sim-dctcp-websearch-n-priority-shared
bash run_all.sh
cd ../
cd obm-sim-dctcp-websearch-n-priority-private
bash run_all.sh
cd ../
python plot_fct.py
python plot_thrpt.py