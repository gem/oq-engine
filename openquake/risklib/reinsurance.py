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
from openquake.hazardlib import nrml, InvalidFile
from openquake.risklib import scientific

KNOWN_LOSS_TYPES = {
    'structural', 'nonstructural', 'contents',
    'value-structural', 'value-nonstructural', 'value-contents'}

TREATY_COLUMNS = ('id', 'type', 'max_retention', 'limit')


def infer_dtype(df):
    """
    :param df: a non-empty DataFrame
    :returns: a structured dtype with bytes and/or float fields
    """
    lst = []
    for col in df.columns:
        if isinstance(df[col][0], str):
            lst.append((col, (np.string_, 16)))
        else:
            lst.append((col, float))
    return np.dtype(lst)


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
                

def parse(fname):
    """
    Parse a reinsurance.xml file and returns
    (policy_df, treaty_df, max_cession, field_map)
    """
    rmodel = nrml.read(fname).reinsuranceModel
    fieldmap = {}
    reversemap = {} # prop1->name1
    max_cession = []
    for node in rmodel.fieldMap:
        fieldmap[node['input']] = col = node['oq']
        reversemap[col] = node['input']
        mce = node.get('max_cession_event')
        if mce:
            max_cession.append(mce)
    for name, col in fieldmap.items():
        if col.startswith('prop'):
            reversemap['overspill' + col[4:]] = 'overspill_' + name
    policyfname = os.path.join(os.path.dirname(fname), ~rmodel.policies)
    nonprop = [treaty.attrib for treaty in rmodel.nonProportional]
    dic = {col: [] for col in TREATY_COLUMNS}
    for tr in nonprop:
        for name in TREATY_COLUMNS:
            dic[name].append(tr[name])
    df = pd.read_csv(policyfname, keep_default_na=False).rename(
        columns=fieldmap)
    check_fields(['deductible', 'liability'], df, fname)
    df['deductible_abs'] = np.ones(len(df), bool)
    df['liability_abs'] = np.ones(len(df), bool)
    return df, pd.DataFrame(dic), np.array(max_cession), reversemap


def claim_to_cessions(claim, fractions, nonprop=None):
    """
    Converts an array of claims into a dictionary of arrays

    >>> claim_to_cessions(np.array([900_000]), [.3, .5], {'max_retention': 100_000, 'limit': 200_000})
    {'claim': array([900000]), 'prop1': array([270000.]), 'prop2': array([450000.]), 'retention': array([100000.]), 'nonprop1': array([80000.])}

    >>> claim_to_cessions(np.array([1_800_000]), [.4, .4], {'max_retention': 100_000, 'limit': 200_000})
    {'claim': array([1800000]), 'prop1': array([720000.]), 'prop2': array([720000.]), 'retention': array([160000.]), 'nonprop1': array([200000.])}

    >>> claim_to_cessions(np.array([80_000]), [.4, .4], {'max_retention': 100_000, 'limit': 200_000})
    {'claim': array([80000]), 'prop1': array([32000.]), 'prop2': array([32000.]), 'retention': array([0.]), 'nonprop1': array([16000.])}
    """
    # proportional cessions
    assert sum(fractions) < 1
    out = {'claim': claim}
    for i, frac in enumerate(fractions, 1):
        cession = 'prop%d' % i
        out[cession] = claim * frac
    out['retention'] = claim * (1. - sum(fractions))
    if nonprop is None:
        return {k: np.round(v, 6) for k, v in out.items()}

    # nonproportional cessions
    out['nonprop1'] = out['retention'] - nonprop['max_retention']
    neg = out['nonprop1'] < 0
    neg_ret = (out['retention'][neg]).copy()
    over = (out['nonprop1'] > nonprop['limit']) & (out['nonprop1'] > 0)
    out['retention'][over] = (nonprop['max_retention'] +
                              out['nonprop1'][over] - nonprop['limit'])
    out['nonprop1'][over] = nonprop['limit']
    out['retention'][~over] = nonprop['max_retention']
    out['nonprop1'][neg] = neg_ret
    out['retention'][neg] = 0
    return {k: np.round(v, 6) for k, v in out.items()}


# tested in test_reinsurance.py
def by_policy(agglosses_df, pol, treaty_df):
    '''
    :param DataFrame losses:
        losses aggregated by policy (keys agg_id, event_id)
    :param Series pol:
        Description of policy characteristics
    :param DataFrame treaty_df:
        Description of reinsurance characteristics
    :returns:
        DataFrame of reinsurance losses by event ID and policy ID
    '''
    out = {}
    df = agglosses_df[agglosses_df.agg_id == pol['policy'] - 1]
    losses = df.loss.to_numpy()
    ded, lim = get_ded_lim(losses, pol)
    claim = scientific.insured_losses(losses, ded, lim)
    out['event_id'] = df.event_id.to_numpy()
    out['policy_id'] = [pol['policy']] * len(df)
    fractions = [pol[col] for col in pol if col.startswith('prop')]
    try:
        nonprop = treaty_df.loc[pol['nonprop1']]
    except KeyError:
        nonprop = None
    out.update(claim_to_cessions(claim, fractions, nonprop))
    return pd.DataFrame(out)


def by_event(by_policy_df, max_cession):
    """
    :param by_policy_df: output of by_policy
    :param max_cession: maximum cession for each proportional treaty
    """
    df = by_policy_df.groupby('event_id').sum()
    del df['policy_id']
    for col in by_policy_df.columns:
        if col.startswith('prop'):
            cession = max_cession[int(col[4:]) - 1]
            over = df[col] > cession
            df['overspill' + col[4:]] = np.maximum(df[col] - cession, 0)
            df['retention'][over] += df[col][over] - cession
            df[col][over] = cession
    return df.reset_index()
