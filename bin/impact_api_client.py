#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2025-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Example of a client running an impact calculation through the API of an
OpenQuake WebUI in IMPACT mode, then retrieving its results. It needs only
requests, numpy and pandas, so it can be run outside the engine.

The credentials are read from the environment variables OQ_USERNAME and
OQ_PASSWORD (if not set, they are asked interactively). For instance:

    OQ_USERNAME=myname python3 impact_api_client.py us6000phrk \
        --host https://impact.openquake.org

The script exits with a non-zero status if any request fails or if the
calculation does not complete; it is also run by the engine tests.
"""

import os
import sys
import json
import time
import getpass
import argparse
from io import BytesIO

import numpy
import pandas
from requests import Session

TIMEOUT = 60  # seconds, for each request
TERMINAL_STATES = ('complete', 'shared', 'failed', 'aborted', 'deleted')


def fail(msg):
    # print the message and exit with a non-zero status
    sys.exit('ERROR: ' + msg)


class ImpactClient:
    """
    A session logged into the WebUI, with helpers checking the responses
    """
    def __init__(self, host):
        self.host = host.rstrip('/')
        self.session = Session()

    def check(self, resp):
        # the redirects are not followed, so an expired session gives an
        # error instead of the HTML of the login page
        if resp.status_code != 200:
            fail(f'{resp.request.method} {resp.url} returned '
                 f'{resp.status_code} {resp.reason}\n{resp.text[:2000]}')
        return resp

    def get(self, path, timeout=TIMEOUT, **params):
        return self.check(self.session.get(
            self.host + path, params=params, timeout=timeout,
            allow_redirects=False))

    def post(self, path, data, timeout=TIMEOUT):
        return self.check(self.session.post(
            self.host + path, data=data, timeout=timeout,
            allow_redirects=False))

    def get_npz(self, path, **params):
        # the extract endpoints return numpy .npz archives
        return numpy.load(BytesIO(self.get(path, **params).content))

    def login(self, username, password):
        print(f'Logging into {self.host} as {username}...')
        self.post('/accounts/ajax_login/',
                  dict(username=username, password=password))
        print('...done')


def get_credentials():
    username = os.environ.get('OQ_USERNAME') or input('Username: ')
    password = os.environ.get('OQ_PASSWORD') or getpass.getpass()
    return username, password


def choose_shakemap(client, usgs_id, shakemap_id=None):
    """
    :returns: the id of the given ShakeMap version, checking that it exists,
              or the id of the version preferred by the USGS
    """
    # GET ALL AVAILABLE VERSIONS OF THE SHAKEMAP FOR THE SPECIFIED USGS_ID
    print(f'Getting the ShakeMap versions for {usgs_id}...')
    js = client.post('/v1/impact_get_shakemap_versions',
                     dict(usgs_id=usgs_id)).json()
    # the "shakemap_versions" will report for each version its id, number and
    # date/time of publication, as in the following example:
    """
    {
        "shakemap_versions": [
            {
                "id": "urn:usgs-product:us:shakemap:us6000phrk:1738891320927",
                "number": "6",
                "utc_date_time": "2025-02-07 01:22:00"
            },
            ...
            {
                "id": "urn:usgs-product:us:shakemap:us6000phrk:1735953132990",
                "number": "1",
                "utc_date_time": "2025-01-04 01:12:12"
            }
        ],
        "usgs_preferred_version":
            "urn:usgs-product:us:shakemap:us6000phrk:1738891320927",
        "shakemap_versions_issue": null
    }
    """
    if js.get('shakemap_versions_issue'):
        fail(js['shakemap_versions_issue'])
    for version in js['shakemap_versions']:
        print('{number:>3} {utc_date_time} {id}'.format(**version))
    ids = [version['id'] for version in js['shakemap_versions']]
    if shakemap_id is None:
        shakemap_id = js['usgs_preferred_version']
    elif shakemap_id not in ids:
        fail(f'{shakemap_id} is not a ShakeMap version of {usgs_id}')
    print('...done')
    return shakemap_id


def run_calculation(client, usgs_id, shakemap_id, time_event=None):
    """
    Run a calculation using the ShakeMap with the given id

    :returns: the calculation id
    """
    print(f'Running a calculation using the ShakeMap'
          f' for {usgs_id=} and {shakemap_id=}')
    input_params = {
        'usgs_id': usgs_id,
        # NOTE: without shakemap_version, the latest ShakeMap is used
        'shakemap_version': shakemap_id,
        'make_impact_reports': True,
    }
    # NOTE: to override the time of the day determined starting from the
    # localized timestamp of the event, pass time_event ('day', 'night' or
    # 'transit')
    if time_event:
        input_params['time_event'] = time_event
    # NOTE: downloading the shakemap information can be quite slow
    [calc_id] = client.post('/v1/calc/impact_run_with_shakemap',
                            input_params, timeout=300).json()
    print(f'...started calculation {calc_id}')
    return calc_id


def wait_and_print_log(client, calc_id, max_wait):
    """
    Print the log of the calculation while it runs

    :returns: the final status of the calculation
    """
    print('Printing the log of the calculation...')
    start = 0
    status = None
    t0 = time.time()
    while status not in TERMINAL_STATES:
        if time.time() - t0 > max_wait:
            fail(f'Calculation {calc_id} still {status} after {max_wait} s')
        time.sleep(3)
        status = client.get(f'/v1/calc/{calc_id}/status').json().get(
            'status')
        log = client.get(f'/v1/calc/{calc_id}/log/{start}:').json()
        if log:
            print('\n'.join(', '.join(row) for row in log))
            start += len(log)
    print(f'...{status}')
    return status


def print_json(title, data):
    print(title)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print('...done')


def print_npz_table(title, npz):
    # print a table built from the arrays of the archive, failing if empty
    df = pandas.DataFrame({key: npz[key] for key in npz})
    if df.empty:
        fail(f'{title}: no data')
    print(title)
    print(df)
    print('...done')


def get_results(client, calc_id):
    """
    Retrieve and print the results of the calculation
    """
    # GET A LIST OF THE AVAILABLE RESULTS FOR THE CALCULATION
    # NOTE: some outputs are not listed here, and they can be extracted as
    # shown below
    results = client.get(f'/v1/calc/{calc_id}/result/list').json()
    if not results:
        fail('No results')
    print_json('Results of the calculation:', results)

    # GET A LIST OF OTHER IMPACT-RELATED RESOURCES FOR THE CALCULATION
    print_json('Other impact-related resources of the calculation:',
               client.get(f'/v1/calc/{calc_id}/impact_resources').json())

    # GET OQPARAM
    npz = client.get_npz(f'/v1/calc/{calc_id}/extract/oqparam')
    print_json('Parameters of the calculation:',
               json.loads(bytes(npz['json'])))

    # GET THE AVERAGE LOSSES PER ASSET
    npz = client.get_npz(f'/v1/calc/{calc_id}/extract/losses_by_asset')
    rlz = npz['rlz-000']
    print_npz_table('Losses by asset:',
                    {name: rlz[name] for name in rlz.dtype.names})

    # GET THE TOTAL LOSSES PER LOCATION
    print_npz_table('Losses by location:', client.get_npz(
        f'/v1/calc/{calc_id}/extract/losses_by_location'))

    # GET THE TOTAL EXPOSURE PER LOCATION
    print_npz_table('Exposure by location:', client.get_npz(
        f'/v1/calc/{calc_id}/extract/exposure_by_location'))

    # GET THE TOTAL EXPOSURE PER LSE TIERS AND REGIONS
    for secondary_peril in ['liquefaction', 'landslide']:
        print_npz_table(
            f'Exposure by {secondary_peril} LSE tiers and regions:',
            client.get_npz(f'/v1/calc/{calc_id}/extract/exposure_by_lse',
                           secondary_peril=secondary_peril))

    # GET THE IMPACT
    df = pandas.DataFrame(client.get(f'/v1/calc/{calc_id}/impact').json())
    data_rows = df.loc['ID':]
    impact = pandas.DataFrame({col: data_rows.loc[col, 'impact']
                               for col in data_rows.index})
    print('Impact:')
    print(impact)
    print('...done')


def main(usgs_id, host, shakemap_id=None, time_event=None, max_wait=3600):
    client = ImpactClient(host)
    client.login(*get_credentials())
    shakemap_id = choose_shakemap(client, usgs_id, shakemap_id)
    calc_id = run_calculation(client, usgs_id, shakemap_id, time_event)
    status = wait_and_print_log(client, calc_id, max_wait)
    if status not in ('complete', 'shared'):
        tb = client.get(f'/v1/calc/{calc_id}/traceback').json()
        fail(f'Calculation {calc_id} {status}\n' + '\n'.join(tb))
    get_results(client, calc_id)

    # GET THE LIST OF CALCULATIONS VISIBLE BY THE AUTHENTICATED USER
    calculations = client.get('/v1/calc/list', relevant='true').json()
    # PRINT THE FIRST TWO CALCULATIONS
    print_json('The latest calculations visible by the user:',
               calculations[:2])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run an impact calculation through the WebUI API '
        'and retrieve its results',
        epilog='The credentials are read from the OQ_USERNAME and '
        'OQ_PASSWORD environment variables, or asked interactively')
    parser.add_argument('usgs_id', nargs='?', default='us6000phrk',
                        help='USGS event id (default: %(default)s)')
    parser.add_argument('--host', default='http://localhost:8800',
                        help='URL of the WebUI (default: %(default)s)')
    parser.add_argument('--shakemap-id',
                        help='id of the ShakeMap version to use (default: '
                        'the version preferred by the USGS)')
    parser.add_argument('--time-event', choices=['day', 'night', 'transit'],
                        help='override the time of the day of the event')
    parser.add_argument('--max-wait', type=int, default=3600,
                        help='maximum seconds to wait for the calculation')
    args = parser.parse_args()
    main(args.usgs_id, args.host, args.shakemap_id, args.time_event,
         args.max_wait)
