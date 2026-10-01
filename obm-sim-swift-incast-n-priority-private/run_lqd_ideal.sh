!/bin/bash

cd net-sim-lqd-ideal/
echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.2.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.2.csv.processed 0.2 1000000
cd ..
echo workloads/incast-trace-100G-degree-0.2.csv.processed > stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.2
python3 stats.py lqd-ideal 0.2 >> stats_lqd_ideal.txt

cd net-sim-lqd-ideal/
echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.4.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.4.csv.processed 0.4 1000000
cd ..
echo workloads/incast-trace-100G-degree-0.4.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.4
python3 stats.py lqd-ideal 0.4 >> stats_lqd_ideal.txt

cd net-sim-lqd-ideal/
echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.6.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.6.csv.processed 0.62 1000000
cd ..
echo workloads/incast-trace-100G-degree-0.6.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.62
python3 stats.py lqd-ideal 0.62 >> stats_lqd_ideal.txt

cd net-sim-lqd-ideal/
echo python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.8.csv.processed 1000000
python3 network.py 144-host-2-tier-fattree.json workloads/incast-trace-100G-degree-0.8.csv.processed 0.8 1000000
cd ..
echo workloads/incast-trace-100G-degree-0.8.csv.processed >> stats_lqd_ideal.txt
python3 stats.py lqd-ideal 0.8
python3 stats.py lqd-ideal 0.8 >> stats_lqd_ideal.txt