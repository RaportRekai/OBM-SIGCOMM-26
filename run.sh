cd switch-sim-private
bash bash_prvt_mac.sh
cd ../
cd switch-sim-shared
bash bash_seq.sh
cd ../
python regex_time_log_reader.py
python private_hd_log_reader.py
python shared_hd_log_reader.py

python plt_thrpt.py