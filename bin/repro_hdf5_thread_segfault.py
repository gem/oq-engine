#!/usr/bin/env python
"""Stress concurrent HDF5 reads used by IMPACT rupture validation.

Run from the engine virtual environment:

    python -X faulthandler bin/repro_hdf5_thread_segfault.py

On affected stacks, this may terminate with a native segmentation fault.
"""

import argparse
import faulthandler
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from openquake.hazardlib.shakemap.validate import MOSAIC_DIR, get_trts_around


def stress_reads(exposure, model, iterations):
    """Synchronize two threads while repeatedly reading the TRT table."""
    barrier = Barrier(2)

    def reader(_):
        for _ in range(iterations):
            barrier.wait()
            get_trts_around(model, exposure)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(reader, range(2)))


def main():
    """Run the concurrent HDF5 read stress test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='ZAF')
    parser.add_argument('--iterations', type=int, default=1000)
    args = parser.parse_args()

    faulthandler.enable()
    exposure = os.path.join(MOSAIC_DIR, 'exposure.hdf5')
    print(f'Reading {exposure} concurrently', flush=True)
    stress_reads(exposure, args.model, args.iterations)
    print('Completed without a segfault', flush=True)


if __name__ == '__main__':
    main()
