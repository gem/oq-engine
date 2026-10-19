# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Plumbing to run PFD inside the engine's context machinery.

PFD has no ground-shaking intensity models: the displacement exceedance
probabilities come from the ``openquake.pfd`` models evaluated by the
:mod:`openquake.hazardlib.calc.displacement` rate kernel. The engine still
needs a GSIM-like object to drive :class:`~openquake.hazardlib.contexts.
ContextMaker`, which derives the required distances, site parameters and
rupture parameters from the GSIMs. :class:`PFDGMPE` is that object: it
declares the PFD context requirements (``rtor``, ``x_l``, ``length``, ...)
and is never actually computed. :func:`get_pfd_gsim_lt` builds the trivial
one-dummy-per-TRT GSIM logic tree that lets
:class:`~openquake.hazardlib.logictree.FullLogicTree` compose the
source-model logic tree with the PFD runs.
"""
from openquake.baselib.node import Node as N
from openquake.hazardlib.gsim_lt import GsimLogicTree
from openquake.hazardlib.gsim.base import DummyGMPE


class PFDGMPE(DummyGMPE):
    """
    No-op GMPE declaring the PFD context requirements. It is used only to
    make ``ContextMaker`` build contexts with the ``rtor``/``x_l`` distances
    and the ``length`` rupture parameter; the PFD kernel reads those
    contexts directly and never calls ``get_mean_and_stddevs``.
    """
    REQUIRES_DISTANCES = {'rtor', 'x_l', 'rx'}
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'dip', 'rake', 'length', 'ztor'}
    REQUIRES_SITES_PARAMETERS = {'vs30'}


def get_pfd_gsim_lt(trts):
    """
    :param trts: the tectonic region types of the source model
    :returns: a :class:`~openquake.hazardlib.gsim_lt.GsimLogicTree` with a
        single :class:`PFDGMPE` branch per TRT (all with weight 1)
    """
    nodes = []
    for i, trt in enumerate(trts):
        branch = N('logicTreeBranch', {'branchID': 'b1'},
                   nodes=[N('uncertaintyModel', text='PFDGMPE'),
                          N('uncertaintyWeight', text='1.0')])
        nodes.append(N('logicTreeBranchSet',
                       {'applyToTectonicRegionType': trt,
                        'branchSetID': 'pfd_bs%d' % i,
                        'uncertaintyType': 'gmpeModel'},
                       nodes=[branch]))
    ltnode = N('logicTree', {'logicTreeID': 'lt_pfd'}, nodes=nodes)
    return GsimLogicTree('pfd_gmpe.xml', list(trts), ltnode=ltnode)
