# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2025, GEM Foundation
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
import os
import numpy
from openquake.hazardlib.shakemap.maps import get_sitecol_shakemap
from openquake.commonlib import logs
from openquake.hazardlib import logictree
from openquake.commonlib.readinput import get_site_collection
from openquake.calculators.base import calculators, store_gmfs


# see qa_tests_data/scenario/case_21
def main(id, site_model='', *, num_gmfs: int = 1, random_seed: int = 42,
         trunclevel: float = 3, spatialcorr='yes', crosscorr='yes',
         cholesky_limit: int = 10_000):
    """
    Given a shakemap ID and a path to a site_model.csv file build a
    GMFs array corresponding to num_gmfs events. The user can pass
    other parameters, see the --help message.
    Example of usage: oq shakemap2gmfs us2000ar20 site_model.csv -n 10
    """
    fname = '%s.npy' % id
    if os.path.exists(fname):
        dic = {'kind': 'file_npy', 'fname': fname}
    else:
        dic = {'kind': 'usgs_id', 'id': id}
    imts = ['PGA', 'SA(0.3)', 'SA(0.6)', 'SA(1.0)', 'MMI']
    param = dict(number_of_ground_motion_fields=str(num_gmfs),
                 description='Converting ShakeMap->GMFs',
                 truncation_level=str(trunclevel),
                 calculation_mode='scenario',
                 random_seed=str(random_seed),
                 inputs={'job_ini': '<memory>'})
    if site_model:
        param['inputs']['site_model'] = [os.path.abspath(site_model)]
    else:
        param['sites'] = '0 0'
    with logs.init(param) as log:
        oq = log.get_oqparam()
        calc = calculators(oq, log.calc_id)
        sites = get_site_collection(oq) if site_model else None
        try:
            sitecol, shakemap, disc = get_sitecol_shakemap(dic, imts, sites)
        except RuntimeError as err:
            assert 'is required' in str(err), err
            imts = ['PGA', 'SA(0.3)', 'SA(1.0)']
            sitecol, shakemap, disc = get_sitecol_shakemap(dic, imts, sites)
        if not os.path.exists(fname):
            numpy.save(fname, shakemap)
            print(f'Saved {fname}')
        print(f'Got {sitecol}')
        if len(disc):
            print(f'{len(disc)} sites discarded')
        calc.datastore['sitecol'] = sitecol
        calc.datastore['full_lt'] = logictree.FullLogicTree.fake()
        gmfdic = {'kind': 'Silva&Horspool',
                  'spatialcorr': spatialcorr,
                  'crosscorr': crosscorr,
                  'cholesky_limit': cholesky_limit}
        store_gmfs(calc, sitecol, shakemap, gmfdic)
    gmv = float(calc.datastore.read_df('gmf_data')[imts[0]].max())
    print(f'Maximum {gmv=}')
    print('See the output with silx view %s' % calc.datastore.filename)


main.id = 'ShakeMap ID for the USGS'
main.site_model = 'Path to site model file'
main.num_gmfs = 'Number of GMFs to generate'
main.random_seed = 'Random seed to use'
main.trunclevel = 'Truncation level'
main.spatialcorr = 'Spatial correlation'
main.crosscorr = 'Cross correlation among IMTs'
main.cholesky_limit = 'Cholesky Limit'
