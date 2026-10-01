#!/usr/bin/env python
"""Stress hcurves exports through concurrent OpenQuake API requests.

Example:

    python -X faulthandler bin/repro_hdf5_thread_segfault_http.py \\
        --job-id 123 --concurrency 4 --iterations 100

The script discovers the hcurves result for the job and concurrently downloads
its CSV export from the API. The engine API must be running and the caller must
have permission to access the job.
"""

import argparse
import faulthandler
import threading
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from urllib.parse import urljoin

import requests


def parse_headers(header_args):
    """Parse repeated 'Name: Value' command-line headers."""
    headers = {}
    for header in header_args:
        name, sep, value = header.partition(':')
        if not sep or not name.strip():
            raise ValueError(f'Invalid header: {header!r}')
        headers[name.strip()] = value.strip()
    return headers


def get_hcurves_export_url(base_url, job_id, headers, timeout):
    """Find the API URL for the job's hcurves result export."""
    endpoint = urljoin(base_url.rstrip('/') + '/',
                       f'v1/calc/{job_id}/results')
    response = requests.get(endpoint, headers=headers, timeout=timeout)
    response.raise_for_status()
    results = response.json()
    matches = [result for result in results if result['type'] == 'hcurves']
    if not matches:
        raise RuntimeError(f'Job {job_id} has no exportable hcurves result')
    return urljoin(base_url.rstrip('/') + '/',
                   f"v1/calc/result/{matches[0]['id']}")


def stress_requests(url, headers, timeout, iterations, progress_every,
                    concurrency):
    """Issue synchronized requests and return average latency and bytes."""
    timing_lock = threading.Lock()
    completed_rounds = 0
    elapsed_total = 0.0
    bytes_total = 0
    content_type = ''

    def report_progress():
        nonlocal completed_rounds
        completed_rounds += 1
        if completed_rounds % progress_every == 0:
            print(f'Completed {completed_rounds} concurrent request rounds',
                  flush=True)

    barrier = threading.Barrier(concurrency, action=report_progress)

    def worker(_):
        nonlocal elapsed_total, bytes_total, content_type
        with requests.Session() as session:
            session.headers.update(headers)
            for _ in range(iterations):
                barrier.wait()
                started = perf_counter()
                try:
                    response = session.get(
                        url, params={'export_type': 'csv'}, timeout=timeout)
                    response.raise_for_status()
                    size = len(response.content)
                    ctype = response.headers.get('Content-Type', '')
                except Exception:
                    barrier.abort()
                    raise
                elapsed = perf_counter() - started
                with timing_lock:
                    elapsed_total += elapsed
                    bytes_total += size
                    content_type = ctype
                barrier.wait()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(worker, range(concurrency)))
    calls = concurrency * iterations
    return elapsed_total / calls, bytes_total // calls, content_type


def main():
    """Run the HTTP export stress test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8800',
                        help='engine API base URL')
    parser.add_argument('--job-id', type=int, required=True,
                        help='job ID containing hazard curves')
    parser.add_argument('--concurrency', type=int, default=2,
                        help='number of concurrent workers (default: 2)')
    parser.add_argument('--iterations', type=int, default=100,
                        help='requests per worker (default: 100)')
    parser.add_argument('--progress-every', type=int, default=10)
    parser.add_argument('--timeout', type=float, default=300,
                        help='request timeout in seconds (default: 300)')
    parser.add_argument('--header', action='append', default=[],
                        help="HTTP header, e.g. --header 'Cookie: sessionid=…'")
    args = parser.parse_args()
    if (args.concurrency < 2 or args.iterations < 1 or
            args.progress_every < 1 or args.timeout <= 0):
        parser.error('concurrency must be >= 2; iterations, progress-every, '
                     'and timeout must be positive')
    try:
        headers = parse_headers(args.header)
    except ValueError as exc:
        parser.error(str(exc))

    faulthandler.enable()
    url = get_hcurves_export_url(
        args.base_url, args.job_id, headers, args.timeout)
    print(f'Exporting hcurves for job {args.job_id} from {url}', flush=True)
    average, average_bytes, content_type = stress_requests(
        url, headers, args.timeout, args.iterations, args.progress_every,
        args.concurrency)
    print(f'Average request time: {average:.6f} seconds', flush=True)
    print(f'Average response size: {average_bytes} bytes '
          f'({content_type})', flush=True)
    print('Completed without a segfault', flush=True)


if __name__ == '__main__':
    main()
