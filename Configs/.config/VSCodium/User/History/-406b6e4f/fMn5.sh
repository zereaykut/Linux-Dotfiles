#!/usr/bin/env bash
source venv/bin/activate

# python 01_preprocess.py
python 02_thermo_calc.py
python 03_visualize.py
python 04_mask.py

deactivate
