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
from openquake.baselib.general import BASE183
from openquake.baselib.performance import compile
from openquake.hazardlib import nrml, InvalidFile
from openquake.risklib import scientific
"""
Here is some info about the used data structures.
There are 3 main dataframes:

1. treaty_df (id, type, max_retention, limit, code)
   with type in prop, wxlr, catxl
2. policy_df (policy, liability, deductible, prop1, nonprop1, cat1)
3. risk_by_event (event_id, agg_id, loss) with agg_id == policy_id-1
"""
NOLIMIT = 1E100
KNOWN_LOSS_TYPES = {
    'structural', 'nonstructural', 'contents',
    'value-structural', 'value-nonstructural', 'value-contents'}


def get_ded_lim(losses, policy):
    """
    :returns: deductible and liability as arrays of absolute values
    """
    if policy.get('deductible_abs', True):
        ded = policy['deductible']
    else:
        ded = losses * policy['deductible']
    if policy.get('liability_abs', True):
        lim = policy['liability']
    else:
        lim = losses * policy['liability']
    return ded, lim


def check_fields(fields, dframe, idxdict, fname):
    """
    :param fields: fields to check (the first field is the primary key)
    :param dframe: DataFrame with the contents of fname
    :param idxdict: dictionary key -> index (starting from 1)
    :param fname: file containing the fields to check
    """
    key = fields[0]
    idx = [idxdict[name] for name in dframe[key]]  # indices starting from 1
    dframe[key] = idx
    for no, field in enumerate(fields):
        if field not in dframe.columns:
            raise InvalidFile(f'{fname}: {field} is missing in the header')
        elif no > 0:  # for the value fields
            arr = dframe[field].to_numpy()
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


def parse(fname, policy_idx):
    """
    :param fname: CSV file containing the policies
    :param policy_idx: dictionary policy name -> policy index

    Parse a reinsurance.xml file and returns
    (policy_df, treaty_df, field_map)
    """
    rmodel = nrml.read(fname).reinsuranceModel
    fieldmap = {}
    reversemap = {} # propN->nameN
    treaty = dict(id=[], type=[], max_retention=[], limit=[])
    nonprop = set()
    for node in rmodel.fieldMap:
        fieldmap[node['input']] = col = node['oq']
        reversemap[col] = node['input']
        if col in ('policy', 'deductible', 'liability'):  # not a treaty
            continue
        treaty_type = node.get('type', 'prop')
        assert treaty_type in ('prop', 'wxlr', 'catxl'), treaty_type
        if treaty_type == 'prop':
            limit = node.get('max_cession_event', NOLIMIT)
            maxret = 0
        else:
            limit = node['limit']
            maxret = node['max_retention']
            nonprop.add(col)
        treaty['id'].append(col)
        treaty['type'].append(treaty_type)
        treaty['max_retention'].append(maxret)
        treaty['limit'].append(limit)
    for name, col in fieldmap.items():
        if col.startswith('prop'):
            reversemap['overspill' + col[4:]] = 'overspill_' + name
    policyfname = os.path.join(os.path.dirname(fname), ~rmodel.policies)
    df = pd.read_csv(policyfname, keep_default_na=False).rename(
        columns=fieldmap)
    check_fields(['policy', 'deductible', 'liability'], df, policy_idx, fname)
    df['deductible_abs'] = np.ones(len(df), bool)
    df['liability_abs'] = np.ones(len(df), bool)

    # validate policy input
    colnames = []
    colvalues = []
    for col, origname in reversemap.items():
        if col.startswith('prop'):
            colnames.append(origname)
            colvalues.append(df[col].to_numpy())
        elif col in nonprop:
            df[col] = np.bool_(df[col])
    if colnames:
        check_fractions(colnames, colvalues, policyfname)
    treaty_df = pd.DataFrame(treaty)
    treaty_df['code'] = [BASE183[i] for i in range(len(treaty_df))]
    return df, treaty_df, reversemap


@compile(["(float64[:],float64[:],float64,float64)",
          "(float64[:],float32[:],float64,float64)",
          "(float32[:],float32[:],float64,float64)"])
def apply_nonprop(cession, retention, maxret, limit):
    capacity = limit - maxret
    for i, ret in np.ndenumerate(retention):
        overmax = ret - maxret
        if ret > maxret:
            if overmax > capacity:
                retention[i] = maxret + overmax - capacity
                cession[i] = capacity
            else:
                retention[i] = maxret
                cession[i] = overmax


def claim_to_cessions(claim, policy, treaty_df):
    """
    :param claim: an array of claims
    :param policy: a dictionary corresponding to a specific policy
    :param treaty_df: dataframe with treaties

    Converts an array of claims into a dictionary of arrays.
    """
    # proportional cessions
    fractions = [policy[col] for col in policy if col.startswith('prop')]
    assert sum(fractions) < 1
    out = {'claim': claim, 'retention': claim * (1. - sum(fractions))}
    for i, frac in enumerate(fractions, 1):
        cession = 'prop%d' % i
        out[cession] = claim * frac

    # wxlr cessions
    wxl = treaty_df[treaty_df.type == 'wxlr']
    for col, nonprop in wxl.iterrows():
        out[col] = np.zeros(len(claim))
        if policy[col]:
            apply_nonprop(out[col], out['retention'],
                          nonprop['max_retention'], nonprop['limit'])

    return {k: np.round(v, 6) for k, v in out.items()}


def build_treaty_key(pol_dict, treaty_df):
    """
    :returns: the treaty_key for the given policy
    """
    cols = treaty_df.index.to_numpy()
    codes = treaty_df.code.to_numpy()
    key = ['.'] * len(cols)
    for c, col in enumerate(cols):
        if pol_dict[col] > 0:
            key[c] = codes[c]
    return ''.join(key)


# tested in test_reinsurance.py
def by_policy(agglosses_df, pol_dict, treaty_df):
    '''
    :param DataFrame agglosses_df:
        losses aggregated by policy (keys agg_id, event_id)
    :param dict pol_dict:
        Policy parameters, with pol_dict['policy'] being an integer >= 1
    :param DataFrame treaty_df:
        All treaties
    :returns:
        DataFrame of reinsurance losses by event ID and policy ID
    '''
    out = {}
    df = agglosses_df[agglosses_df.agg_id == pol_dict['policy'] - 1]
    losses = df.loss.to_numpy()
    ded, lim = get_ded_lim(losses, pol_dict)
    claim = scientific.insured_losses(losses, ded, lim)
    out['event_id'] = df.event_id.to_numpy()
    out['policy_id'] = np.array([pol_dict['policy']] * len(df))
    out.update(claim_to_cessions(claim, pol_dict, treaty_df))
    nonzero = out['claim'] > 0  # discard zero claims
    out_df = pd.DataFrame({k: out[k][nonzero] for k in out})
    return out_df


def _by_event(by_policy_df, treaty_df):
    """
    :param DataFrame by_policy_df: output of `by_policy`
    :param DataFrame treaty_df: treaties
    """
    df = by_policy_df.groupby('event_id').sum()
    del df['policy_id']
    dic = {'event_id': df.index.to_numpy()}
    for col in df.columns:
        dic[col] = df[col].to_numpy()

    # proportional overspill
    prop = treaty_df[treaty_df.type == 'prop']
    for col, cession in zip(prop.index, prop.limit):
        over = dic[col] > cession
        overspill = np.maximum(dic[col] - cession, 0)
        if overspill.any():
            dic['overspill' + col[4:]] = overspill
        dic['retention'][over] += dic[col][over] - cession
        dic[col][over] = cession

    # catxl applied everywhere
    catxl = treaty_df[treaty_df.type == 'catxl']
    tot = np.zeros(len(df))
    for col, nonprop in catxl.iterrows():
        cession = np.zeros(len(df))
        apply_nonprop(cession, dic[col],
                      nonprop['max_retention'], nonprop['limit'])
        dic[col] = cession
        tot += cession
    dic['retention'] -= tot
    return pd.DataFrame(dic)


def by_policy_event(agglosses_df, policy_df, treaty_df):
    """
    :param DataFrame agglosses_df: losses aggregated by (agg_id, event_id)
    :param DataFrame policy_df: policies
    :param DataFrame treaty_df: treaties
    :returns: (by_policy_df, by_event_df)
    """
    dfs = []
    cats = [name for name, treaty in treaty_df.iterrows()
            if treaty.type == 'catxl']
    assert (treaty_df.limit != NOLIMIT).all()
    tdf = treaty_df[treaty_df.type != 'wxlr']
    for _, policy in policy_df.iterrows():
        df = by_policy(agglosses_df, dict(policy), treaty_df)
        for cat in cats:
            # policy[cat] is 1 if the CatXL applies to the policy, 0 otherwise
            df[cat] = policy[cat] * df.retention
        df['treaty_key'] = build_treaty_key(policy, tdf)
        dfs.append(df)
    rbp = pd.concat(dfs)
    print(df)  # when debugging
    rbe = _by_event(rbp, treaty_df)
    del rbp['treaty_key']
    return rbp, rbe
