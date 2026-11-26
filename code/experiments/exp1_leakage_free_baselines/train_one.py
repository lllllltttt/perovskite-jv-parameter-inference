# -*- coding: utf-8 -*-
"""CLI: train_one.py <family> <seed> <outdir>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exp1_lib import train_one

if __name__ == "__main__":
    family, seed, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    model, history, secs = train_one(family, seed, outdir)
    print(f"TRAINED {family} seed={seed} -> {outdir} ({secs:.0f}s, {len(history.history['loss'])} epochs)")
