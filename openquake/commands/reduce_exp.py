#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import shutil
import logging
import numpy
import pandas
from openquake.baselib import performance
from openquake.commonlib import readinput, oqvalidation


def reduce_files(datafiles, okassets):
    """
    Reduce the original files to the ok assets, by making a .bak copy first
    """
    for fname in datafiles:
        df = pandas.read_csv(fname)
        rdf = df[numpy.isin(df.ASSET_ID, okassets)]
        if len(rdf) < len(df):
            logging.info('Saving %s.bak', fname)
            shutil.copy(fname, fname + '.bak')
            rdf.to_csv(fname, index=None)


def main(exposure_xml, sites_csv):
    """
    Reduce the exposure model to the sites in the site model
    """
    with performance.Monitor() as mon:
        oq = oqvalidation.OqParam(inputs={'job_ini': '<in-memory>',
                                          'sites': sites_csv,
                                          'exposure': [exposure_xml]},
                                  calculation_mode='custom',
                                  asset_hazard_distance='15',
                                  maximum_distance='300')
        _sitecol, _assetcol, _discarded, expo = readinput.get_sitecol_assetcol(
            oq)
    okassets = numpy.array([a.decode('utf-8') for a in expo.assets['id']])
    reduce_files(expo.datafiles, okassets)
    print(mon)


main.exposure_xml = 'path to the exposure file'
main.sites_csv = 'path to the site model file'
