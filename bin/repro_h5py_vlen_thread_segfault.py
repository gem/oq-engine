#!/usr/bin/env python
"""Standalone stress test for h5py reads of compound VLEN datasets.

Requires only h5py and NumPy. Run with::

    python -X faulthandler bin/repro_h5py_vlen_thread_segfault.py
    python -X faulthandler bin/repro_h5py_vlen_thread_segfault.py --guard

The unguarded run may segfault on affected h5py/HDF5 builds. The --guard
run serializes each complete file operation and should finish safely.
Each worker opens the same file and reads fixed-width members from a compound
record that also contains a variable-length string member.
"""

import argparse
import faulthandler
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock

import h5py
import numpy


def make_file(path, rows):
    """Create the compound dataset used by the stress test."""
    dtype = numpy.dtype([('model', 'S3'), ('trt', 'S61'),
                         ('gsim', h5py.string_dtype('utf-8')),
                         ('weight', numpy.float64)])
    records = numpy.zeros(rows, dtype=dtype)
    records['model'] = b'ZAF'
    records['trt'] = b'Active'
    records['gsim'] = 'ExampleGSIM'
    records['weight'] = 1.0
    with h5py.File(path, 'w') as h5:
        h5.create_dataset('records', data=records)


def read_selected_fields(dataset):
    """Read fixed-width members from the VLEN-containing compound dataset."""
    model = dataset['model'][:]
    trt = dataset['trt'][:]
    return model, trt


def read_file(path):
    """Open the test file and read its selected compound members."""
    with h5py.File(path, 'r') as h5:
        return read_selected_fields(h5['records'])


def stress(path, concurrency, iterations, guarded):
    """Concurrently open one file and read selected compound members."""
    start = Barrier(concurrency)
    lock = Lock() if guarded else None

    def reader(_):
        start.wait()
        for _ in range(iterations):
            if lock:
                with lock:
                    model, trt = read_file(path)
            else:
                model, trt = read_file(path)
            if len(model) != len(trt):
                raise RuntimeError('Inconsistent field lengths')
        return len(model)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return list(pool.map(reader, range(concurrency)))


def main():
    """Create a temporary file and run the concurrent-read stress test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--concurrency', type=int, default=8,
                        help='number of reader threads (default: 8)')
    parser.add_argument('--iterations', type=int, default=5000,
                        help='reads per thread (default: 5000)')
    parser.add_argument('--rows', type=int, default=1176,
                        help='records in the synthetic dataset (default: '
                        '1176)')
    parser.add_argument('--guard', action='store_true',
                        help='serialize complete file operations with a lock')
    args = parser.parse_args()
    if args.concurrency < 2 or args.iterations < 1 or args.rows < 1:
        parser.error('concurrency must be >= 2; iterations and rows must '
                     'be positive')

    faulthandler.enable()
    print(f'h5py {h5py.__version__}, HDF5 {h5py.version.hdf5_version}',
          flush=True)
    guard_status = 'with' if args.guard else 'without'
    print(f'Starting {args.concurrency} threads x {args.iterations} reads '
          f'{guard_status} the guard', flush=True)
    with tempfile.TemporaryDirectory(prefix='h5py-vlen-thread-') as tmpdir:
        path = os.path.join(tmpdir, 'records.h5')
        make_file(path, args.rows)
        result = stress(path, args.concurrency, args.iterations, args.guard)
    print(f'Completed without a segfault: {result}', flush=True)


if __name__ == '__main__':
    main()
