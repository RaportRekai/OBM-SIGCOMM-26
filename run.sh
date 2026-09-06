cd thrpt_diff_prvt
mkdir -p {spideal_logs,obm_logs,optimal_logs}
bash bash_show_diff.sh
cd ../

cd thrpt_diff_shared
mkdir -p {spideal_logs,obm_logs,optimal_logs}
bash bash_show_diff.sh
cd ../

python plot_thrpt_diff.py