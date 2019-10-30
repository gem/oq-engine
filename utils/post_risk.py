# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019, GEM Foundation
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

import logging
from openquake.baselib import sap
from openquake.commonlib import util
from openquake.calculators.post_risk import PostRiskCalculator
from openquake.server import dbserver


@sap.script
def post_risk(ebr_id):
    """
    Generate loss curves and maps from an event loss table
    """
    dbserver.ensure_on()
    dstore = util.read(ebr_id)
    oq = dstore['oqparam']
    prc = PostRiskCalculator(oq)
    prc.datastore.parent = dstore
    prc.run()
    logging.info('Generated %s', prc.datastore.filename)


post_risk.arg('ebr_id', 'event based risk calculation ID', type=int)


if __name__ == '__main__':
    post_risk.callfunc()
