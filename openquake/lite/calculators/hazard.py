#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import logging

from openquake.commonlib.readinput import get_site_collection

from openquake.lite.calculators import calculate, calc
from openquake.lite.export import export


@calculate.add('classical')
def run_classical(oqparam):
    """
    Run a classical PSHA calculation and returns the generated files.
    """
    raise NotImplemented


@calculate.add('event_based')
def run_event_based(oqparam):
    """
    Run an event based PSHA calculation and returns the generated files.
    """
    raise NotImplemented


@calculate.add('scenario')
def run_scenario(oqparam):
    """
    Run a scenario hazard computation and returns the file with the GMFs.
    """
    logging.info('Reading the site collection')
    sitecol = get_site_collection(oqparam)

    logging.info('Computing the GMFs')
    gmfs_by_imt = calc.calc_gmfs(oqparam, sitecol)

    logging.info('Exporting the result')
    scenario_tags = ['scenario-%010d' % i for i in xrange(
                     oqparam.number_of_ground_motion_fields)]
    out = export(
        'gmf_xml', oqparam.export_dir, sitecol, scenario_tags, gmfs_by_imt)
    return [out]
