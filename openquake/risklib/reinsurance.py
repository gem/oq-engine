# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2022, GEM Foundation
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
import pandas as pd
import numpy as np
from openquake.baselib.performance import compile
from openquake.hazardlib import nrml, InvalidFile
from openquake.risklib import scientific

KNOWN_LOSS_TYPES = {
    'structural', 'nonstructural', 'contents',
    'value-structural', 'value-nonstructural', 'value-contents'}


def get_ded_lim(losses, policy):
    """
    :returns: deductible and liability as arrays of absolute values
    """
    if policy['deductible_abs']:
        ded = policy['deductible']
    else:
        ded = losses * policy['deductible']
    if policy['liability_abs']:
        lim = policy['liability']
    else:
        lim = losses * policy['liability']
    return ded, lim


def check_fields(fields, dframe, fname):
    """
    Make sure the right fields are present in a CSV file. For instance:

    >>> check_fields(['deductible'], pd.DataFrame(), '*')
    Traceback (most recent call last):
     ...
    openquake.baselib.InvalidFile: *: deductible is missing in the header
    """
    for field in fields:
        if field not in dframe.columns:
            raise InvalidFile(f'{fname}: {field} is missing in the header')
        else:
            arr = dframe[field].to_numpy()
            if len(arr) == 0:
                raise InvalidFile(f'{fname}: is empty')
            if isinstance(arr[0], str):  # there was a `%` in the column
                vals = np.zeros(len(arr), float)
                _abs = np.zeros(len(arr), bool)
                for i, x in enumerate(arr):
                    if x.endswith('%'):
                        vals[i] = float(x[:-1]) / 100.
                        _abs[i] = False
                    else:
                        vals[i] = float(x)
                        _abs[i] = True
                dframe[field] = vals
                dframe[field + '_abs'] = _abs
            else:  # assume all absolute
                dframe[field + '_abs'] = np.ones(len(arr))


# validate the file policy.csv
def check_fractions(colnames, colvalues, fname):
    """
    Make sure the sum of the proportional fractions is below 1 and raise
    a clear error if not.
    """
    n = len(colvalues[0])
    for i in range(n):
        tot = 0
        for c, col in enumerate(colnames):
            frac = colvalues[c][i]
            if frac > 1 or frac < 0:
                raise ValueError(
                    f'{fname}:{i+2}: invalid fraction {col}={frac}')
            tot += frac
        if tot > 1:
            raise ValueError(f'{fname}:{i+2} the sum of the fractions must be '
                             f'under 1, got {tot}')


def parse(fname):
    """
    Parse a reinsurance.xml file and returns
    (policy_df, treaty_df, max_cession, field_map)
    """
    rmodel = nrml.read(fname).reinsuranceModel
    fieldmap = {}
    reversemap = {} # propN->nameN
    max_cession = {}  # propN->cessionN
    nonprop = dict(id=[], max_retention=[], limit=[])
    for node in rmodel.fieldMap:
        fieldmap[node['input']] = col = node['oq']
        reversemap[col] = node['input']
        mce = node.get('max_cession_event')
        if mce:
            max_cession[col] = mce
        treaty_type = node.get('type')
        assert treaty_type in (None, 'prop','wxlr', 'catxl'), treaty_type
        if treaty_type in ('wxlr', 'catxl'):
            nonprop['id'].append(col)
            nonprop['max_retention'].append(node['max_retention'])
            nonprop['limit'].append(node['limit'])
    for name, col in fieldmap.items():
        if col.startswith('prop'):
            reversemap['overspill' + col[4:]] = 'overspill_' + name
    policyfname = os.path.join(os.path.dirname(fname), ~rmodel.policies)
    df = pd.read_csv(policyfname, keep_default_na=False).rename(
        columns=fieldmap)
    check_fields(['deductible', 'liability'], df, fname)
    df['deductible_abs'] = np.ones(len(df), bool)
    df['liability_abs'] = np.ones(len(df), bool)

    # validate policy input
    colnames = []
    colvalues = []
    for col, origname in reversemap.items():
        if col.startswith('prop'):
            colnames.append(origname)
            colvalues.append(df[col].to_numpy())
        elif col.startswith('nonprop'):
            df[col] = np.bool_(df[col])
    if colnames:
        check_fractions(colnames, colvalues, policyfname)
    return df, pd.DataFrame(nonprop), max_cession, reversemap


@compile(["(float64[:],float64[:],float64,float64)",
          "(float64[:],float32[:],float64,float64)"])
def apply_nonprop(cession, retention, maxret, limit):
    for i, ret in np.ndenumerate(retention):
        overmax = ret - maxret
        if ret > maxret:
            if overmax > limit:
                retention[i] = maxret + overmax - limit
                cession[i] = limit
            else:
                retention[i] = maxret
                cession[i] = overmax


def claim_to_cessions(claim, policy, nonprops=()):
    """
    Converts an array of claims into a dictionary of arrays

    >>> df = pd.DataFrame({'id': ['nonprop1'], 'max_retention': [100_000],
    ...                    'limit': [200_000]}).set_index('id')
    >>> pol1 = {'prop1': .3, 'prop2': .5, 'nonprop1': True}
    >>> pol2 = {'prop1': .4, 'prop2': .4, 'nonprop1': True}
    >>> claim_to_cessions(np.array([900_000]), pol1, df)
    {'claim': array([900000]), 'prop1': array([270000.]), 'prop2': array([450000.]), 'retention': array([100000.]), 'nonprop1': array([80000.])}

    >>> claim_to_cessions(np.array([1_800_000]), pol2, df)
    {'claim': array([1800000]), 'prop1': array([720000.]), 'prop2': array([720000.]), 'retention': array([160000.]), 'nonprop1': array([200000.])}

    >>> claim_to_cessions(np.array([80_000]), pol2, df)
    {'claim': array([80000]), 'prop1': array([32000.]), 'prop2': array([32000.]), 'retention': array([16000.]), 'nonprop1': array([0.])}
    """
    # proportional cessions
    fractions = [policy[col] for col in policy if col.startswith('prop')]
    assert sum(fractions) < 1
    out = {'claim': claim}
    for i, frac in enumerate(fractions, 1):
        cession = 'prop%d' % i
        out[cession] = claim * frac
    out['retention'] = claim * (1. - sum(fractions))
    if len(nonprops) == 0:
        return {k: np.round(v, 6) for k, v in out.items()}

    # nonproportional cessions
    for col, nonprop in nonprops.iterrows():
        out[col] = np.zeros(len(claim))
        if policy[col]:
            apply_nonprop(out[col], out['retention'],
                          nonprop['max_retention'], nonprop['limit'])
    return {k: np.round(v, 6) for k, v in out.items()}


# tested in test_reinsurance.py
def by_policy(agglosses_df, pol_dict, treaty_df):
    '''
    :param DataFrame losses:
        losses aggregated by policy (keys agg_id, event_id)
    :param dict pol_dict:
        Policy parameters, with pol_dict['policy'] being an integer >= 1
    :param DataFrame treaty_df:
        Non-proportional treaties
    :returns:
        DataFrame of reinsurance losses by event ID and policy ID
    '''
    out = {}
    df = agglosses_df[agglosses_df.agg_id == pol_dict['policy'] - 1]
    losses = df.loss.to_numpy()
    ded, lim = get_ded_lim(losses, pol_dict)
    claim = scientific.insured_losses(losses, ded, lim)
    out['event_id'] = df.event_id.to_numpy()
    out['policy_id'] = [pol_dict['policy']] * len(df)
    out.update(claim_to_cessions(claim, pol_dict, treaty_df))
    return pd.DataFrame(out)


def by_event(by_policy_df, max_cession):
    """
    :param DataFrame by_policy_df: output of `by_policy`
    :param dict max_cession: maximum cession for proportional treaties
    """
    df = by_policy_df.groupby('event_id').sum()
    del df['policy_id']
    dic = {'event_id': df.index.to_numpy()}
    for col in df.columns:
        dic[col] = df[col].to_numpy() 
    for col, cession in max_cession.items():
        over = dic[col] > cession
        overspill = np.maximum(dic[col] - cession, 0)
        if overspill.any():
            dic['overspill' + col[4:]] = overspill
        dic['retention'][over] += dic[col][over] - cession
        dic[col][over] = cession
    return pd.DataFrame(dic)
