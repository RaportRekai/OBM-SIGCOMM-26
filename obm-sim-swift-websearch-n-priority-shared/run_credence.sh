cd net-sim-credence/
echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.3.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.3.csv.processed 0.3 1000000
cd ..
echo workloads/websearch-trace-100G-load-0.3.csv.processed >> stats_credence.txt
python3 stats.py credence 0.3
python3 stats.py credence 0.3 >> stats_credence.txt

cd net-sim-credence/
echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.6.csv.processed 0.6 1000000
cd ..
echo workloads/websearch-trace-100G-load-0.6.csv.processed >> stats_credence.txt
python3 stats.py credence 0.6
python3 stats.py credence 0.6 >> stats_credence.txt

cd net-sim-credence/
echo python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.9.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/websearch-trace-100G-load-0.9.csv.processed 0.9 1000000
cd ..
echo workloads/websearch-trace-100G-load-0.9.csv.processed >> stats_credence.txt
python3 stats.py credence 0.9
python3 stats.py credence 0.9 >> stats_credence.txt