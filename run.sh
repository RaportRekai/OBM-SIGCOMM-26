cd switch-sim-private
bash bash_prvt.sh
cd ../

cd switch-sim-shared
bash bash_shared_all_algos.sh
cd ../

python regex_time_compare.py
python private_hd_log_reader.py
python shared_hd_log_reader.py

python plt_thrpt.py _ 'uniform' 1
python plt_thrpt.py _ 'zipf' 1
python plt_thrpt.py _ 'skewed' 1