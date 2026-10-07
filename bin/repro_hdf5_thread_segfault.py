#!/usr/bin/env python
"""Stress concurrent HDF5 reads through different engine operations.

Run from the engine virtual environment:

    python -X faulthandler bin/repro_hdf5_thread_segfault.py

On affected stacks, this may terminate with a native segmentation fault.
"""

import argparse
import faulthandler
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from time import perf_counter

from openquake.calculators.export import export
import openquake.calculators.export.hazard as hazard_export  # noqa: F401
from openquake.commonlib import datastore
from openquake.hazardlib.shakemap.validate import (
    MOSAIC_DIR, get_trts_around, hdf5_read_lock_enabled)


def get_operation(args):
    """Build the HDF5 operation selected on the command line."""
    if args.operation == 'get_trts_around':
        exposure = args.exposure or os.path.join(MOSAIC_DIR, 'exposure.hdf5')
        return lambda: get_trts_around(args.model, exposure)

    def run_export(dataset):
        dstore = datastore.read(args.job_id)
        try:
            with tempfile.TemporaryDirectory(
                    prefix='oq-hdf5-stress-') as outdir:
                dstore.export_dir = outdir
                export((dataset, 'csv'), dstore)
        finally:
            dstore.close()

    return lambda: run_export(args.operation)


def stress_reads(operation, iterations, progress_every, concurrency):
    """Stress the operation and return its average call duration."""
    completed_rounds = -1
    timing_lock = Lock()
    elapsed_total = 0.0
    call_count = 0

    def timed_operation():
        nonlocal elapsed_total, call_count
        started = perf_counter()
        operation()
        elapsed = perf_counter() - started
        with timing_lock:
            elapsed_total += elapsed
            call_count += 1

    def report_progress():
        nonlocal completed_rounds
        completed_rounds += 1
        if (completed_rounds and
                completed_rounds % progress_every == 0):
            print(f'Completed {completed_rounds} concurrent call rounds',
                  flush=True)

    start_barrier = Barrier(concurrency)
    barrier = Barrier(concurrency, action=report_progress)

    def reader(_):
        start_barrier.wait()  # synchronize the first round
        for _ in range(iterations):
            timed_operation()
            barrier.wait()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(reader, range(concurrency)))
    return elapsed_total / call_count


def main():
    """Run the concurrent HDF5 read stress test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--operation', choices=(
        'get_trts_around', 'hcurves', 'gmf_data'), default='hcurves',
        help='HDF5 operation to stress (default: hcurves)')
    parser.add_argument('--job-id', type=int, default=-1,
                        help='job ID for hcurves or gmf_data (default: latest)')
    parser.add_argument('--model', default='ZAF',
                        help='mosaic model for get_trts_around')
    parser.add_argument('--exposure',
                        help='exposure HDF5 file for get_trts_around')
    parser.add_argument('--iterations', type=int, default=1000)
    parser.add_argument('--progress-every', type=int, default=10)
    parser.add_argument('--concurrency', type=int, default=2,
                        help='number of concurrent workers (default: 2)')
    args = parser.parse_args()
    if (args.iterations < 1 or args.progress_every < 1 or
            args.concurrency < 2):
        parser.error('iterations and progress-every must be positive, '
                     'and concurrency must be at least 2')

    faulthandler.enable()
    operation = get_operation(args)
    if args.operation == 'get_trts_around':
        state = 'enabled' if hdf5_read_lock_enabled() else 'disabled'
        print(f'HDF5 read lock is {state}', flush=True)
    print(f'Stressing {args.operation} concurrently', flush=True)
    average = stress_reads(operation, args.iterations, args.progress_every,
                           args.concurrency)
    print(f'Average time per call: {average:.6f} seconds', flush=True)
    print('Completed without a segfault', flush=True)


if __name__ == '__main__':
    main()
