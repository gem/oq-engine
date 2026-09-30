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


def stress_reads(exposure, model, iterations, progress_every):
    """Synchronize two readers and report completed concurrent call pairs."""
    completed_pairs = -1

    def report_progress():
        nonlocal completed_pairs
        completed_pairs += 1
        if (completed_pairs and
                completed_pairs % progress_every == 0):
            print(f'Completed {completed_pairs} concurrent call pairs',
                  flush=True)

    barrier = Barrier(2, action=report_progress)

    def reader(_):
        barrier.wait()  # synchronize the start of the first pair
        for _ in range(iterations):
            get_trts_around(model, exposure)
            barrier.wait()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(reader, range(2)))


def main():
    """Run the concurrent HDF5 read stress test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='ZAF')
    parser.add_argument('--iterations', type=int, default=1000)
    parser.add_argument('--progress-every', type=int, default=10)
    args = parser.parse_args()
    if args.iterations < 1 or args.progress_every < 1:
        parser.error('iterations and progress-every must be positive')

    faulthandler.enable()
    exposure = os.path.join(MOSAIC_DIR, 'exposure.hdf5')
    print(f'Reading {exposure} concurrently', flush=True)
    stress_reads(exposure, args.model, args.iterations,
                 args.progress_every)
    print('Completed without a segfault', flush=True)


if __name__ == '__main__':
    main()
