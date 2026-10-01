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


def login(session, base_url, username, password, timeout):
    """Log in to the engine API when credentials were supplied."""
    if not username:
        return
    endpoint = urljoin(base_url.rstrip('/') + '/', 'accounts/ajax_login/')
    response = session.post(endpoint, data=dict(
        username=username, password=password), timeout=timeout)
    response.raise_for_status()
    if response.text.strip() != 'Successful login':
        raise RuntimeError(f'Engine API login failed: {response.text}')


def get_hcurves_export_url(base_url, job_id, headers, timeout,
                           username, password):
    """Find the API URL for the job's hcurves result export."""
    endpoint = urljoin(base_url.rstrip('/') + '/',
                       f'v1/calc/{job_id}/results')
    with requests.Session() as session:
        session.headers.update(headers)
        login(session, base_url, username, password, timeout)
        response = session.get(endpoint, timeout=timeout)
        response.raise_for_status()
        results = response.json()
    matches = [result for result in results if result['type'] == 'hcurves']
    if not matches:
        raise RuntimeError(f'Job {job_id} has no exportable hcurves result')
    return urljoin(base_url.rstrip('/') + '/',
                   f"v1/calc/result/{matches[0]['id']}")


def stress_requests(url, base_url, headers, username, password, timeout,
                    iterations, progress_every, concurrency):
    """Issue synchronized requests and return average latency and bytes."""
    timing_lock = threading.Lock()
    completed_rounds = 0
    elapsed_samples = []
    header_samples = []
    bytes_total = 0
    content_type = ''

    def report_progress():
        nonlocal completed_rounds
        completed_rounds += 1
        if completed_rounds % progress_every == 0:
            print(f'Completed {completed_rounds} concurrent request rounds',
                  flush=True)

    start_barrier = threading.Barrier(concurrency)
    barrier = threading.Barrier(concurrency, action=report_progress)

    def worker(_):
        nonlocal bytes_total, content_type
        with requests.Session() as session:
            session.headers.update(headers)
            try:
                login(session, base_url, username, password, timeout)
            except Exception:
                start_barrier.abort()
                barrier.abort()
                raise
            start_barrier.wait()
            for _ in range(iterations):
                started = perf_counter()
                try:
                    response = session.get(
                        url, params={'export_type': 'csv'}, timeout=timeout)
                    response.raise_for_status()
                    header_elapsed = response.elapsed.total_seconds()
                    size = len(response.content)
                    ctype = response.headers.get('Content-Type', '')
                except Exception:
                    barrier.abort()
                    raise
                elapsed = perf_counter() - started
                with timing_lock:
                    elapsed_samples.append(elapsed)
                    header_samples.append(header_elapsed)
                    bytes_total += size
                    content_type = ctype
                barrier.wait()

    wall_started = perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(worker, range(concurrency)))
    wall_elapsed = perf_counter() - wall_started
    calls = concurrency * iterations
    return (sum(elapsed_samples) / calls,
            sum(header_samples) / calls, wall_elapsed,
            bytes_total // calls, content_type)


def main():
    """Run the HTTP export stress test."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8800',
                        help='engine API base URL')
    parser.add_argument('--job-id', type=int, required=True,
                        help='job ID containing hazard curves')
    parser.add_argument('--username', help='engine API login username')
    parser.add_argument('--password', help='engine API login password')
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
    if bool(args.username) != bool(args.password):
        parser.error('--username and --password must be supplied together')
    try:
        headers = parse_headers(args.header)
    except ValueError as exc:
        parser.error(str(exc))

    faulthandler.enable()
    url = get_hcurves_export_url(
        args.base_url, args.job_id, headers, args.timeout,
        args.username, args.password)
    print(f'Exporting hcurves for job {args.job_id} from {url}', flush=True)
    average, header_average, wall_elapsed, average_bytes, content_type = (
        stress_requests(url, args.base_url, headers, args.username,
                        args.password, args.timeout, args.iterations,
                        args.progress_every, args.concurrency))
    print(f'Average time to response headers: {header_average:.6f} seconds',
          flush=True)
    print(f'Average full request time: {average:.6f} seconds', flush=True)
    print(f'Total wall time: {wall_elapsed:.3f} seconds', flush=True)
    print(f'Average response size: {average_bytes} bytes '
          f'({content_type})', flush=True)
    print('Completed without a segfault', flush=True)


if __name__ == '__main__':
    main()
