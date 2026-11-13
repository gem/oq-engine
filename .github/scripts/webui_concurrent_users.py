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
failed. Only the standard library is used.

Usage, against a WebUI already running on --base:
  webui_concurrent_users.py --user u1:pw1 --user u2:pw2 \
      --archive openquake/server/tests/data/archive_ok.zip
Without --archive the users only browse the pages. The users must already
exist in the WebUI database: run_webui_concurrency.sh sets everything up
and runs this file.
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

LOGIN = '/accounts/login/'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    # keep the 302 of a successful login visible instead of following it
    def redirect_request(self, *args, **kwargs):
        return None


def fetch(opener, url, timeout, body=None, headers=None):
    """Return (HTTP code, seconds, response bytes, problem or None)."""
    req = urllib.request.Request(url, data=body, headers=headers or {})
    t0 = time.monotonic()
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, time.monotonic() - t0, resp.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, time.monotonic() - t0, b'', None
    except (socket.timeout, TimeoutError):
        return None, time.monotonic() - t0, b'', 'timeout'
    except urllib.error.URLError as exc:
        secs = time.monotonic() - t0
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            return None, secs, b'', 'timeout'
        return None, secs, b'', f'connection error: {exc.reason}'


def multipart_body(filename, data):
    # a multipart/form-data body with one file field named "archive"
    boundary = uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; '
            f'name="archive"; filename="{filename}"\r\n'
            f'Content-Type: application/zip\r\n\r\n').encode()
    body += data + f'\r\n--{boundary}--\r\n'.encode()
    return body, f'multipart/form-data; boundary={boundary}'


class User:
    def __init__(self, name, password, args):
        self.name, self.password, self.args = name, password, args
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar), NoRedirect)
        self.events = []  # (label, HTTP code, seconds, problem or None)
        self.token = None

    def get(self, label, url, body=None, headers=None):
        # one checked request: record it and return (code, data, problem)
        code, secs, data, problem = fetch(
            self.opener, url, self.args.timeout, body, headers)
        if problem is None and code not in (200, 302):
            problem = f'HTTP {code}'
        self.events.append((label, code, secs, problem))
        return code, data, problem

    def login(self):
        url = self.args.base + LOGIN
        _, _, problem = self.get('login page', url)
        self.token = next((c.value for c in self.jar
                           if c.name == 'csrftoken'), None)
        if problem or self.token is None:
            return False
        body = urllib.parse.urlencode({
            'csrfmiddlewaretoken': self.token, 'username': self.name,
            'password': self.password}).encode()
        code, _, _ = self.get('login', url, body, {'Referer': url})
        return code == 302

    def submit(self, archive):
        # return the job id, or None if the calculation was not started
        body, ctype = multipart_body('archive_ok.zip', archive)
        code, data, problem = self.get(
            'submit calc', self.args.base + '/v1/calc/run', body,
            {'Content-Type': ctype, 'X-CSRFToken': self.token})
        if problem:
            return None
        try:
            return json.loads(data)['job_id']
        except (ValueError, KeyError, TypeError):
            self.events.append(('submit calc', code, 0.0,
                                'no job_id in response'))
            return None

    def wait_job(self, job):
        # poll the job until complete or failed; return its status
        url = f'{self.args.base}/v1/calc/{job}/status'
        status = None
        deadline = time.monotonic() + self.args.calc_timeout
        while time.monotonic() < deadline:
            code, _, data, problem = fetch(self.opener, url,
                                           self.args.timeout)
            if problem:
                self.events.append((f'poll calc {job}', code, 0.0,
                                    problem))
                return None
            status = json.loads(data).get('status')
            if status in ('complete', 'failed'):
                break
            time.sleep(2)
        if status == 'failed':
            self.events.append((f'calc {job}', None, 0.0,
                                'calc finished with status failed'))
        elif status != 'complete':
            self.events.append((f'calc {job}', None, 0.0,
                                f'calc stuck: still {status} after '
                                f'{self.args.calc_timeout:g}s'))
        return status

    def run(self, barrier, archive):
        barrier.wait()  # all users start at the same moment
        if not self.login():
            return self.events
        pages = ['/engine/', '/v1/calc/list']
        if archive:
            job = self.submit(archive)
            if job is None:
                return self.events
            pages.append(f'/v1/calc/{job}/status')
            if self.wait_job(job) == 'complete':
                pages.append(f'/engine/{job}/outputs')
        for _ in range(self.args.rounds):
            for page in pages:
                self.get(f'GET {page}', self.args.base + page)
        return self.events


def report(results, args, wall):
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
    print(f'{len(results)} users, {len(lat) + bad} checks in {wall:.1f}s: '
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
    archive = None
    if args.archive:
        with open(args.archive, 'rb') as f:
            archive = f.read()
    users = [User(*u.split(':', 1), args) for u in args.user]
    barrier = threading.Barrier(len(users))
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(users)) as pool:
        futures = [pool.submit(u.run, barrier, archive) for u in users]
        results = [(u.name, f.result()) for u, f in zip(users, futures)]
    bad = report(results, args, time.monotonic() - t0)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
