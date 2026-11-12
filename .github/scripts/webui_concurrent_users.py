#!/usr/bin/env python3
"""
Simulate several WebUI users at the same time, to check that the WebUI
does not hang under concurrent use.

Each user (one thread, own cookie jar) waits at a barrier so that all of
them start together, then:
  1. loads the login page and logs in (expects HTTP 302);
  2. submits the --archive zip to /v1/calc/run (expects a job_id);
  3. polls its own job until it is complete or failed, at most
     --calc-timeout seconds;
  4. fetches the pages of the WebUI for --rounds rounds.

Every request is limited to --timeout seconds. Problems are printed as:
  HANG: ...        no answer within --timeout (WebUI worker busy/blocked)
  CALC STUCK: ...  the job was not complete within --calc-timeout
  ERROR: ...       wrong HTTP code, connection error, failed job, ...

The last line gives the number of checks, how many passed, and the
latency of the requests that passed. The exit status is 1 if any check
failed. The stdlib only, so it runs with any Python 3.

Usage, against a WebUI already running on --base:
  webui_concurrent_users.py --user u1:pw1 --user u2:pw2 \
      --archive openquake/server/tests/data/archive_ok.zip
Without --archive the users only browse the pages.
The users must already exist in the WebUI database; see
run_webui_concurrency.sh, which sets everything up and runs this file.
"""
import sys
import json
import time
import uuid
import socket
import argparse
import threading
import statistics
import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # keep the 302 of a successful login visible instead of following it
    def redirect_request(self, *args, **kwargs):
        return None


def make_opener():
    # one cookie jar per user, redirects not followed
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar), NoRedirect)
    opener.jar = jar
    return opener


def fetch(opener, url, timeout, body=None, headers=None):
    # return (http code, seconds, response bytes, problem or None)
    req = urllib.request.Request(url, data=body, headers=headers or {})
    t0 = time.monotonic()
    try:
        with opener.open(req, timeout=timeout) as resp:
            data = resp.read()
            return resp.status, time.monotonic() - t0, data, None
    except urllib.error.HTTPError as exc:
        return exc.code, time.monotonic() - t0, b'', None
    except (socket.timeout, TimeoutError):
        return None, time.monotonic() - t0, b'', 'timeout'
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            return None, time.monotonic() - t0, b'', 'timeout'
        return None, time.monotonic() - t0, b'', \
            f'connection error: {exc.reason}'


def form_body(fields):
    return urllib.parse.urlencode(fields).encode()


def multipart_body(files):
    # files: {field name: (file name, bytes)}
    boundary = uuid.uuid4().hex
    parts = []
    for key, (fname, data) in files.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; '
                     f'name="{key}"; filename="{fname}"\r\n'
                     f'Content-Type: application/zip\r\n\r\n'.encode()
                     + data + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts), f'multipart/form-data; boundary={boundary}'


def run_user(name, password, args, barrier, archive_bytes):
    base = args.base
    opener = make_opener()
    events = []  # (label, http code, seconds, problem or None)

    def record(label, url, body=None, headers=None):
        code, secs, data, problem = fetch(opener, url, args.timeout,
                                          body, headers)
        if problem is None and code not in (200, 302):
            problem = f'HTTP {code}'
        events.append((label, code, secs, problem))
        return code, data

    login_url = base + '/accounts/login/'
    barrier.wait()  # all users start at the same moment
    record('login page', login_url)
    if events[-1][3] is not None:
        return name, events  # no page, so nothing else can be checked
    token = next((c.value for c in opener.jar
                  if c.name == 'csrftoken'), None)
    if token is None:
        events.append(('login', None, 0.0, 'no csrftoken cookie'))
        return name, events
    code, _ = record('login', login_url, body=form_body({
        'csrfmiddlewaretoken': token, 'username': name,
        'password': password}),
        headers={'Referer': login_url})
    if code != 302:
        return name, events  # the failure is already in events

    job = None
    complete = False
    if archive_bytes:
        body, ctype = multipart_body({'archive': ('archive_ok.zip',
                                                  archive_bytes)})
        code, data = record('submit calc', base + '/v1/calc/run',
                            body=body, headers={'Content-Type': ctype,
                                                'X-CSRFToken': token})
        try:
            job = json.loads(data)['job_id']
        except (ValueError, KeyError, TypeError):
            events.append(('submit calc', code, 0.0,
                           'no job_id in response'))
            return name, events
        deadline = time.monotonic() + args.calc_timeout
        status = None
        while time.monotonic() < deadline:
            code, _, data, problem = fetch(
                opener, f'{base}/v1/calc/{job}/status', args.timeout)
            if problem:
                events.append((f'poll calc {job}', code, 0.0, problem))
                break
            status = json.loads(data).get('status')
            if status in ('complete', 'failed'):
                break
            time.sleep(2)
        if status not in ('complete', 'failed'):
            events.append((f'calc {job}', None, 0.0,
                           f'calc stuck: still {status} after '
                           f'{args.calc_timeout:g}s'))
        elif status == 'failed':
            events.append((f'calc {job}', None, 0.0,
                           'calc finished with status failed'))
        complete = status == 'complete'

    pages = ['/engine/', '/v1/calc/list']
    if job is not None:
        pages.append(f'/v1/calc/{job}/status')
    if complete:
        pages.append(f'/engine/{job}/outputs')
    for _ in range(args.rounds):
        for page in pages:
            record(f'GET {page}', base + page)
    return name, events


def report(results, users, args, wall):
    # print one line per problem and the summary; return the bad count
    bad = 0
    lat = []
    for name, events in results:
        for label, code, secs, problem in events:
            if problem is None:
                lat.append(secs)
                continue
            bad += 1
            if problem == 'timeout':
                print(f'HANG: user {name} {label}: no answer within '
                      f'{args.timeout:g}s (WebUI worker busy or blocked)')
            elif problem.startswith('calc stuck'):
                print(f'CALC STUCK: user {name} {label}: {problem}')
            else:
                print(f'ERROR: user {name} {label}: {problem} '
                      f'(HTTP {code}, after {secs:.2f}s)')
    print(f'{users} users, {len(lat) + bad} checks in {wall:.1f}s: '
          f'{len(lat)} ok, {bad} failed')
    if lat:
        print(f'latency of ok requests: median {statistics.median(lat):.3f}s,'
              f' max {max(lat):.3f}s')
    return bad


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--base', default='http://127.0.0.1:8800')
    p.add_argument('--user', action='append', required=True,
                   metavar='NAME:PASSWORD')
    p.add_argument('--archive', help='zip to submit as a calculation; if '
                   'omitted, users only browse pages')
    p.add_argument('--rounds', type=int, default=5)
    p.add_argument('--timeout', type=float, default=60.0)
    p.add_argument('--calc-timeout', type=float, default=300.0)
    args = p.parse_args()
    archive_bytes = None
    if args.archive:
        with open(args.archive, 'rb') as f:
            archive_bytes = f.read()
    users = [u.split(':', 1) for u in args.user]
    barrier = threading.Barrier(len(users))
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(users)) as pool:
        futures = [pool.submit(run_user, n, pw, args, barrier,
                               archive_bytes) for n, pw in users]
        results = [f.result() for f in futures]
    bad = report(results, len(users), args, time.monotonic() - t0)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
