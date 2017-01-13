# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

"""
Reading risk models for risk calculators
"""
import re
import collections

import numpy

from openquake.hazardlib import valid, nrml
from openquake.baselib.node import Node
from openquake.hazardlib.sourcewriter import obj_to_node

F64 = numpy.float64

COST_TYPE_REGEX = '|'.join(valid.cost_type.choices)

LOSS_TYPE_KEY = re.compile(
    '(%s|occupants|fragility)_([\w_]+)' % COST_TYPE_REGEX)


def get_risk_files(inputs):
    """
    :param inputs: a dictionary key -> path name
    :returns: a pair (file_type, {cost_type: path})
    """
    vfs = {}
    names = set()
    for key in inputs:
        if key == 'fragility':
            # backward compatibily for .ini files with key fragility_file
            # instead of structural_fragility_file
            vfs['structural'] = inputs['structural_fragility'] = inputs[key]
            names.add('fragility')
            del inputs['fragility']
            continue
        match = LOSS_TYPE_KEY.match(key)
        if match and 'retrofitted' not in key and 'consequence' not in key:
            vfs[match.group(1)] = inputs[key]
            names.add(match.group(2))
    if not names:
        return None, {}
    elif len(names) > 1:
        raise ValueError('Found inconsistent keys %s in the .ini file'
                         % ', '.join(names))
    return names.pop(), vfs


# ########################### vulnerability ############################## #

def filter_vset(elem):
    return elem.tag.endswith('discreteVulnerabilitySet')


@obj_to_node.add('VulnerabilityFunction')
def build_vf_node(vf):
    """
    Convert a VulnerabilityFunction object into a Node suitable
    for XML conversion.
    """
    nodes = [Node('imls', {'imt': vf.imt}, vf.imls),
             Node('meanLRs', {}, vf.mean_loss_ratios),
             Node('covLRs', {}, vf.covs)]
    return Node(
        'vulnerabilityFunction',
        {'id': vf.id, 'dist': vf.distribution_name}, nodes=nodes)


def get_risk_models(oqparam, kind=None):
    """
    :param oqparam:
        an OqParam instance
    :param kind:
        vulnerability|vulnerability_retrofitted|fragility|consequence;
        if None it is extracted from the oqparam.file_type attribute
    :returns:
        a dictionary taxonomy -> loss_type -> function
    """
    kind = kind or oqparam.file_type
    rmodels = {}
    for key in sorted(oqparam.inputs):
        mo = re.match('(occupants|%s)_%s$' % (COST_TYPE_REGEX, kind), key)
        if mo:
            key_type = mo.group(1)  # the cost_type in the key
            # can be occupants, structural, nonstructural, ...
            rmodel = nrml.parse(oqparam.inputs[key])
            rmodels[key_type] = rmodel
            if rmodel.lossCategory is None:  # NRML 0.4
                continue
            cost_type = str(rmodel.lossCategory)
            rmodel_kind = rmodel.__class__.__name__
            kind_ = kind.replace('_retrofitted', '')  # strip retrofitted
            if not rmodel_kind.lower().startswith(kind_):
                raise ValueError(
                    'Error in the file "%s_file=%s": is '
                    'of kind %s, expected %s' % (
                        key, oqparam.inputs[key], rmodel_kind,
                        kind.capitalize() + 'Model'))
            if cost_type != key_type:
                raise ValueError(
                    'Error in the file "%s_file=%s": lossCategory is of type '
                    '"%s", expected "%s"' % (key, oqparam.inputs[key],
                                             rmodel.lossCategory, key_type))
    rdict = collections.defaultdict(dict)
    if kind == 'fragility':
        limit_states = []
        for loss_type, fm in sorted(rmodels.items()):
            # build a copy of the FragilityModel with different IM levels
            newfm = fm.build(oqparam.continuous_fragility_discretization,
                             oqparam.steps_per_interval)
            for (imt, taxo), ffl in newfm.items():
                if not limit_states:
                    limit_states.extend(fm.limitStates)
                # we are rejecting the case of loss types with different
                # limit states; this may change in the future
                assert limit_states == fm.limitStates, (
                    limit_states, fm.limitStates)
                rdict[taxo][loss_type] = ffl
                # TODO: see if it is possible to remove the attribute
                # below, used in classical_damage
                ffl.steps_per_interval = oqparam.steps_per_interval
        oqparam.limit_states = [str(ls) for ls in limit_states]
    elif kind == 'consequence':
        rdict = rmodels
    else:  # vulnerability
        cl_risk = oqparam.calculation_mode in ('classical', 'classical_risk')
        # only for classical_risk reduce the loss_ratios
        # to make sure they are strictly increasing
        for loss_type, rm in rmodels.items():
            for (imt, taxo), rf in rm.items():
                rdict[taxo][loss_type] = (
                    rf.strictly_increasing() if cl_risk else rf)
    return rdict
