# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
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
from openquake.baselib import sap
from openquake.commonlib import datastore, readinput
from openquake.calculators.base import run_calc

def main(calc_id: int):
    """
    An utility to debug postprocessors. Use it as
    $ python -m openquake.calculators.postproc.debug <calc_id>
    """
    dstore = datastore.read(calc_id)  # read the original calculation
    oq = dstore['oqparam']  # extract the original job.ini file
    job_ini = oq.inputs['job_ini']

    # overwrite the original imtls with the stored imtls, needed for AELO
    imtls = {imt: [float(x) for x in imls] for imt, imls in oq.imtls.items()}
    params = readinput.get_params(job_ini)
    params['intensity_measure_types_and_levels'] = str(imtls)

    run_calc(params, hazard_calculation_id=calc_id)


if __name__ == '__main__':
    sap.run(main)
