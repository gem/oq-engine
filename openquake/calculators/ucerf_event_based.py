# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2020 GEM Foundation
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
import collections
import numpy

from openquake.calculators import base, event_based

U16 = numpy.uint16
U32 = numpy.uint32
F32 = numpy.float32
F64 = numpy.float64


# NB: the old name ucerf_hazard is kept for backward compatibility
@base.calculators.add('ucerf_event_based', 'ucerf_hazard')
class UCERFHazardCalculator(event_based.EventBasedCalculator):
    """
    Event based PSHA calculator generating the ruptures and GMFs together
    """
    accept_precalc = ['ucerf_event_based']

    def pre_execute(self):
        """
        parse the logic tree and source model input
        """
        logging.warning('%s is still experimental', self.__class__.__name__)
        self.read_inputs()  # read the site collection
        logging.info('Found %d source model logic tree branches',
                     len(self.csm.sm_rlzs))
        self.datastore['sitecol'] = self.sitecol
        self.eid = collections.Counter()  # sm_id -> event_id
        self.sm_by_grp = self.csm.info.get_sm_by_grp()
        self.init_logic_tree(self.csm.info)
        if not self.oqparam.imtls:
            raise ValueError('Missing intensity_measure_types!')
        self.precomputed_gmfs = False
