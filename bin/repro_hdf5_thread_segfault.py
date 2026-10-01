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
from threading import Barrier

from openquake.calculators.export import export
import openquake.calculators.export.hazard as hazard_export  # noqa: F401
from openquake.commonlib import datastore
from openquake.hazardlib.shakemap.validate import MOSAIC_DIR, get_trts_around


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
    """Synchronize readers and report completed concurrent call rounds."""
    completed_rounds = -1

    def report_progress():
        nonlocal completed_rounds
        completed_rounds += 1
        if (completed_rounds and
                completed_rounds % progress_every == 0):
            print(f'Completed {completed_rounds} concurrent call rounds',
                  flush=True)

    barrier = Barrier(concurrency, action=report_progress)

    def reader(_):
        barrier.wait()  # synchronize the start of the first round
        for _ in range(iterations):
            operation()
            barrier.wait()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(reader, range(concurrency)))


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
    print(f'Stressing {args.operation} concurrently', flush=True)
    stress_reads(operation, args.iterations, args.progress_every,
                 args.concurrency)
    print('Completed without a segfault', flush=True)


if __name__ == '__main__':
    main()
