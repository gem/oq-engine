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

import sys
import traceback
from pdb import post_mortem
from openquake.commonlib import datastore
from openquake.calculators import base


def main(calc_id: int, calculation_mode=None, pdb=False):
    parent = datastore.read(calc_id)
    oq = parent['oqparam']
    if calculation_mode:
        oq.calculation_mode = calculation_mode
    oq.hazard_calculation_id = calc_id
    oq._amplifier = None
    oq._sec_perils = ()
    log, dstore = datastore.create_job_dstore(oq.description, parent)
    with dstore, log:
        calc = base.calculators(oq, log.calc_id)
        calc.sitecol = parent['sitecol']
        try:
            calc.execute()
        except Exception as exc:
            if pdb:  # post-mortem debug
                tb = sys.exc_info()[2]
                traceback.print_tb(tb)
                post_mortem(tb)
            else:
                raise exc from None

main.calc_id = 'calculation ID or datastore path'
main.calculation_mode = 'calculation mode'

