# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
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

import numpy
from openquake.baselib import sap
from openquake.commonlib import datastore, readinput
from openquake.calculators.classical import store_mean_disagg_bysrc

U32 = numpy.uint32


def main(parent_id):
    """
    :param parent_id: filename or ID of the parent calculation
    """
    try:
        parent_id = int(parent_id)
    except ValueError:
        pass
    parent = datastore.read(parent_id)
    dstore, log = datastore.build_dstore_log(parent=parent)
    with dstore, log:
        full_lt = readinput.get_full_lt(parent['oqparam'])
        csm = parent['_csm']
        csm.init(full_lt)
        store_mean_disagg_bysrc(dstore, csm)


if __name__ == '__main__':
    sap.run(main)
