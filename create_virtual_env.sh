#!/bin/bash

sudo apt update
sudo apt install -y python3.10 python3.10-venv

# brew install python@3.10


# rm -rf obm
python3.10 -m venv obm
# Activate virtual environment
source obm/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install required packages
pip install numpy matplotlib pandas joblib scikit-learn

echo "Virtual environment created and packages installed."
echo "Activate it later using:"
echo "source obm/bin/activate"

source obm/bin/activate