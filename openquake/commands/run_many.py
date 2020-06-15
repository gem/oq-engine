# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020 GEM Foundation
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
import logging
import toml

from openquake.baselib import sap, parallel
from openquake.commonlib import readinput, oqvalidation, logs
from openquake.calculators import base
from openquake.server import dbserver
oqvalidation.OqParam.calculation_mode.validator.choices = tuple(
    base.calculators)


@sap.script
def run_many(job_ini, extra):
    """
    Run multiple calculations by using extra parameters
    """
    dbserver.ensure_on()
    oq = readinput.get_oqparam(job_ini)
    calc = base.calculators(oq, logs.init('job'))
    try:
        calc.run_many(extra)
    finally:
        parallel.Starmap.shutdown()


run_many.arg('job_ini', 'calculation configuration file')
run_many.arg('extra', 'parameters for the extra calculations', type=toml.loads)
