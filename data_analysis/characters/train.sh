#!/bin/bash
#SBATCH --gpus-per-node=1 --constraint=48GB

python ./data_analysis/characters/character_portraits.py
