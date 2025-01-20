#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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

import json
import logging
import requests
from openquake.baselib import config
from openquake.commonlib import oqzip
from openquake.calculators.extract import WebAPIError


def main(zipfile):
    """
    Post one or more zipfiles to the WebUI
    """
    sess = requests.Session()
    for fname in zipfile:
        if config.webapi.username:
            login_url = '%s/accounts/ajax_login/' % config.webapi.server
            logging.info('POST %s', login_url)
            resp = sess.post(
                login_url, data=dict(username=config.webapi.username,
                                     password=config.webapi.password))
            if resp.status_code != 200:
                raise WebAPIError(resp.text)
        if fname.endswith('.ini'):  # not a zip file yet
            archive = fname[:-3] + 'zip'
            oqzip.zip_job(fname, archive)
            fname = archive
        resp = sess.post("%s/v1/calc/run" % config.webapi.server, {},
                         files=dict(archive=open(fname, 'rb')))
        if 'Log in to an existing account' in resp.text:
            raise SystemExit('Wrong credentials %s' % str(config.webapi))
        else:
            print(json.loads(resp.text))


main.zipfile = dict(help='archive with the files of the computation',
                    nargs='+')
