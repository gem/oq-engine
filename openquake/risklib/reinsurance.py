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

import os
import logging
import pandas as pd
import numpy as np
from openquake.baselib import hdf5
from openquake.baselib.general import BASE183, fast_agg2, gen_slices
from openquake.baselib.performance import compile, Monitor
from openquake.baselib.writers import scientificformat
from openquake.hazardlib import nrml, InvalidFile
from openquake.risklib import scientific
"""
Here is some info about the used data structures.
There are 3 main dataframes:

1. treaty_df (id, type, deductible, limit, code)
   with type in prop, wxlr, catxl
2. policy_df (policy, liability, deductible, prop1, nonprop1, cat1)
3. risk_by_event (event_id, agg_id, loss) with agg_id == policy_id-1
"""
NOLIMIT = 1E100
KNOWN_LOSS_TYPES = {
    'structural', 'nonstructural', 'contents',
    'value-structural', 'value-nonstructural', 'value-contents'}
DEBUG = False
VALID_TREATY_TYPES = 'prop', 'wxlr', 'catxl'


def check_fields(fields, dframe, policyidx, fname, policyfname, treaties,
                 treaty_linenos, treaty_types):
    """
    :param fields: fields to check (the first field is the primary key)
    :param dframe: DataFrame with the contents of fname
    :param policyidx: dictionary key -> index (starting from 1)
    :param fname: file xml containing the fields to check
    :param policyfname: file csv containing the fields to check
    :param treaties: treaty names
    :param treaty_linenos: line numbers where each treaty was read from xml
    :param treaty_types: treaty types
    """
    key = fields[0]
    [indices] = np.where(np.isnan(dframe.deductible.to_numpy()))
    if len(indices) > 0:
        raise InvalidFile(
            '%s (rows %s): empty deductible values were found' % (
                policyfname, [idx + 2 for idx in indices]))
    [indices] = np.where(np.isnan(dframe.liability.to_numpy()))
    if len(indices) > 0:
        raise InvalidFile(
            '%s (rows %s): empty liability values were found' % (
                policyfname, [idx + 2 for idx in indices]))
    [indices] = np.where(dframe.duplicated(subset=[key]).to_numpy())
    if len(indices) > 0:
        # NOTE: reporting only the first row found
        raise InvalidFile(
            '%s (row %d): a duplicate %s was found: "%s"' % (
                policyfname, indices[0] + 2, key, dframe[key][indices[0]]))
    prev_treaty = None
    prev_treaty_type = None
    for lineno, treaty, treaty_type in zip(
            treaty_linenos, treaties, treaty_types):
        if prev_treaty is not None:
            prev_treaty_type_idx = VALID_TREATY_TYPES.index(prev_treaty_type)
            curr_treaty_type_idx = VALID_TREATY_TYPES.index(treaty_type)
            if curr_treaty_type_idx < prev_treaty_type_idx:
                raise InvalidFile(
                    f'{fname} (line {lineno}): treaty types must be'
                    f' specified in the order {VALID_TREATY_TYPES}.'
                    f' Treaty "{treaty}" of type "{treaty_type}" was'
                    f' found after treaty "{prev_treaty}" of type'
                    f' "{prev_treaty_type}"')
        prev_treaty = treaty
        prev_treaty_type = treaty_type
        if treaty not in dframe.columns:
            raise InvalidFile(
                f'{fname} (line {lineno}): {treaty} is missing'
                ' in {policyfname}')
    policies_from_exposure = list(policyidx)[1:]  # discard '?'
    policies_from_csv = list(dframe.policy)
    [indices] = np.where(~np.isin(policies_from_exposure, policies_from_csv))
    if len(indices) > 0:
        # NOTE: reporting only the first missing policy
        first_missing_policy = policies_from_exposure[indices[0]]
        raise InvalidFile(
            f'{policyfname}: policy "{first_missing_policy}" is missing')
    [indices] = np.where(dframe.liability.to_numpy() < 0)
    if len(indices) > 0:
        # NOTE: reporting only the first row found
        raise InvalidFile(
            '%s (row %d): a negative liability was found' % (
                policyfname, indices[0] + 2))
    [indices] = np.where(dframe.deductible.to_numpy() < 0)
    if len(indices) > 0:
        # NOTE: reporting only the first row found
        raise InvalidFile(
            '%s (row %d): a negative deductible was found' % (
                policyfname, indices[0] + 2))
    check_treaties(fields, dframe, policyidx, fname, policyfname,
                   treaties, treaty_types)


def check_treaties(fields, dframe, policyidx, fname, policyfname,
                   treaties, treaty_types):
    prop_treaties = []
    for treaty, treaty_type in zip(treaties, treaty_types):
        if treaty_type == 'prop':
            prop_treaties.append(treaty)
        else:
            [indices] = np.where(~dframe[treaty].isin([0, 1]).to_numpy())
            if len(indices) > 0:
                # NOTE: reporting only the first row found
                raise InvalidFile(
                    '%s (row %d): values for %s must be either 0 or 1' % (
                        policyfname, indices[0] + 2, treaty))
    sums = np.zeros(len(dframe))
    for prop_treaty in prop_treaties:
        fractions = dframe[prop_treaty].to_numpy()
        [indices] = np.where(np.logical_or(fractions < 0, fractions > 1))
        if len(indices) > 0:
            # NOTE: there is at least 1 row with invalid fraction. The error
            # shows the first of them
            raise InvalidFile(
                '%s (row %d): proportional fraction for treaty "%s", %s, is'
                ' not >= 0 and <= 1' % (policyfname, indices[0] + 2,
                                        prop_treaty, fractions[indices[0]]))
        sums += dframe[prop_treaty].to_numpy()
    for i, treaty_sum in enumerate(sums):
        if not 0 <= treaty_sum <= 1:
            raise InvalidFile(
                '%s (row %d): the sum of proportional fractions is %s.'
                ' It must be >= 0 and <= 1' % (
                    policyfname, i+2, np.round(treaty_sum, 5)))
    # replace policy names with policy indices starting from 1
    key = fields[0]
    dframe[key] = [policyidx[pol] for pol in dframe[key]]
    for no, field in enumerate(fields):
        if field not in dframe.columns:
            raise InvalidFile(f'{fname}: {field} is missing in the header')
    prev_treaty = None
    prev_treaty_type = None
    prev_treaty_type_idx = None
    prev_treaty_df_col_idx = None
    for colname in list(dframe.columns):
        if colname not in treaties:
            continue
        treaty = colname
        treaty_type = treaty_types[treaties.index(treaty)]
        if prev_treaty is not None:
            treaty_df_col_idx = dframe.columns.get_loc(treaty)
            treaty_type_idx = VALID_TREATY_TYPES.index(treaty_type)
            if (treaty_df_col_idx > prev_treaty_df_col_idx
                    and treaty_type_idx < prev_treaty_type_idx):
                raise InvalidFile(
                    f'{policyfname}: treaty type columns must be'
                    f' in the order {VALID_TREATY_TYPES}.'
                    f' Treaty "{treaty}" of type "{treaty_type}" was'
                    f' found after treaty "{prev_treaty}" of type'
                    f' "{prev_treaty_type}"')
        prev_treaty = treaty
        prev_treaty_type = treaty_type
        prev_treaty_type_idx = VALID_TREATY_TYPES.index(prev_treaty_type)
        prev_treaty_df_col_idx = dframe.columns.get_loc(prev_treaty)


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
    :param fname: XML file containing the treaties metadata
    :param policy_idx: dictionary policy name -> policy index

    Parse a reinsurance.xml file and returns
    (policy_df, treaty_df, field_map)
    """
    rmodel = nrml.read(fname).reinsuranceModel
    fieldmap = {}
    fmap = {}  # ex: {'deductible': 'Deductible', 'liability': 'Limit'}
    treaty = dict(id=[], type=[], deductible=[], limit=[])
    treaty_linenos = []
    nonprop = set()
    colnames = []
    for node in rmodel.fieldMap:
        col = node.get('oq')
        if col:
            fmap[col] = node['input']
        if col in ('policy', 'deductible', 'liability'):  # not a treaty
            fieldmap[node['input']] = col
            continue
        treaty_type = node.get('type', 'prop')
        if treaty_type not in VALID_TREATY_TYPES:
            raise InvalidFile(
                "%s (line %d): valid treaty types are %s."
                " '%s' was found instead" % (
                    fname, node.lineno, VALID_TREATY_TYPES, treaty_type))
        if treaty_type == 'prop':
            limit = node.get('max_cession_event', NOLIMIT)
            deduc = 0
            colnames.append(node['input'])
        else:
            limit = node['limit']
            deduc = node['deductible']
            nonprop.add(node['input'])
        treaty['id'].append(node['input'])
        treaty['type'].append(treaty_type)
        treaty['deductible'].append(deduc)
        treaty['limit'].append(limit)
        treaty_linenos.append(node.lineno)
    policyfname = os.path.join(os.path.dirname(fname), ~rmodel.policies)
    df = pd.read_csv(policyfname).rename(columns=fieldmap)
    df.columns = df.columns.str.strip()
    all_policies = df.policy.to_numpy()  # ex ['A', 'B']
    exp_policies = np.array(list(policy_idx))  # ex ['?', 'B', 'A']
    if len(all_policies) != len(exp_policies[1:]):
        # reduce the policy dataframe to the policies actually in the exposure
        df = df[np.isin(all_policies, exp_policies[1:])]
    check_fields(['policy', 'deductible', 'liability'], df, policy_idx, fname,
                 policyfname, treaty['id'], treaty_linenos, treaty['type'])

    # validate policy input
    for col in nonprop:
        df[col] = np.bool_(df[col])
    if colnames:
        colvalues = [df[col].to_numpy() for col in colnames]
        check_fractions(colnames, colvalues, policyfname)
    treaty_df = pd.DataFrame(treaty)
    treaty_df['code'] = [BASE183[i] for i in range(len(treaty_df))]
    missing_treaties = set(df.columns) - set(treaty_df.id) - {
        'policy', 'deductible', 'liability'}
    for col in missing_treaties:  # remove missing treaties
        del df[col]
    return df, treaty_df, fmap


@compile(["(float64[:],float64[:],float64,float64)",
          "(float64[:],float32[:],float64,float64)",
          "(float32[:],float32[:],float64,float64)"])
def apply_treaty(cession, retention, deduc, capacity):
    for i, ret in np.ndenumerate(retention):
        overmax = ret - deduc
        if ret > deduc:
            if overmax > capacity:
                retention[i] = deduc + overmax - capacity
                cession[i] = capacity
            else:
                retention[i] = deduc
                cession[i] = overmax


def claim_to_cessions(claim, policy, treaty_df):
    """
    :param claim: an array of claims
    :param policy: a dictionary corresponding to a specific policy
    :param treaty_df: dataframe with treaties

    Converts an array of claims into a dictionary of arrays.
    """
    # proportional cessions
    cols = treaty_df[treaty_df.type == 'prop'].id
    fractions = [policy[col] for col in cols]
    assert sum(fractions) <= 1
    out = {'retention': claim * (1. - sum(fractions)), 'claim': claim}
    for col, frac in zip(cols, fractions):
        out[col] = claim * frac

    # wxlr cessions, totally independent from the overspill
    wxl = treaty_df[treaty_df.type == 'wxlr']
    for col, deduc, limit in zip(wxl.id, wxl.deductible, wxl.limit):
        out[col] = np.zeros(len(claim))
        if policy[col]:
            apply_treaty(out[col], out['retention'], deduc, limit - deduc)

    return {k: np.round(v, 6) for k, v in out.items()}


def build_policy_grp(policy, treaty_df):
    """
    :param policy: policy dictionary
    :param treaty_df: treaty DataFrame
    :returns: the policy_grp for the given policy
    """
    cols = treaty_df.id.to_numpy()
    codes = treaty_df.code.to_numpy()
    types = treaty_df.type.to_numpy()
    key = list(codes)
    for c, col in enumerate(cols):
        if types[c] == 'catxl' and policy[col] == 0:
            key[c] = '.'
    return ''.join(key)


def line(row, fmt='%d'):
    return ''.join(scientificformat(val, fmt).rjust(11) for val in row)


def clever_agg(ukeys, datalist, treaty_df, idx, overdict, eids):
    """
    :param ukeys: a list of unique keys
    :param datalist: a list of matrices of the shape (E, 2+T)
    :param treaty_df: a treaty DataFrame
    :param idx: a dictionary treaty.code -> cession index
    :param overdic: a dictionary treaty.code -> overspill array

    Recursively compute cessions and retentions for each treaty.
    Populate the cession dictionary and returns the final retention.
    """
    if DEBUG:
        print()
        print(line(['event_id', 'policy_grp'] + list(idx)))
        rows = []
        for key, data in zip(ukeys, datalist):
            # printing the losses
            for eid, row in zip(eids, data):
                rows.append([eid, key] + list(row))
        for row in sorted(rows):
            print(line(row))
    if len(ukeys) == 1 and ukeys[0] == '':
        return datalist[0]
    newkeys, newdatalist = [], []
    for key, data in zip(ukeys, datalist):
        code = key[0]
        newkey = key[1:]
        if code != '.':
            tr = treaty_df.loc[code]
            ret = data[:, idx['retention']]
            cession = data[:, idx[code]]
            capacity = tr.limit - tr.deductible
            has_over = False
            if tr.type == 'catxl':
                overspill = ret - tr.deductible - capacity
                has_over = (overspill > 0).any()
                apply_treaty(cession, ret, tr.deductible, capacity)
            elif tr.type == 'prop':
                overspill = cession - capacity
                over = overspill > 0
                has_over = (overspill > 0).any()
                if has_over:
                    ret[over] += cession[over] - tr.limit
                    cession[over] = tr.limit
            if has_over:
                overdict['over_' + code] = np.maximum(overspill, 0)
        newkeys.append(newkey)
        newdatalist.append(data)
    keys, sums = fast_agg2(newkeys, np.array(newdatalist))
    return clever_agg(keys, sums, treaty_df, idx, overdict, eids)


# tested in reinsurance_test.py
def by_policy(rbe, pol_dict, treaty_df):
    '''
    :param DataFrame rbe:
        losses aggregated by policy (agg_id) and event_id
    :param dict pol_dict:
        Policy parameters, with pol_dict['policy'] being an integer >= 1
    :param DataFrame treaty_df:
        All treaties
    :returns:
        DataFrame of reinsurance losses by event ID and policy ID
    '''
    out = {}
    df = rbe[rbe.agg_id == pol_dict['policy'] - 1]
    losses = df.loss.to_numpy()
    ded, lim = pol_dict['deductible'], pol_dict['liability']
    claim = scientific.insured_losses(losses, ded, lim)
    out['event_id'] = df.event_id.to_numpy()
    out['policy_id'] = np.array([pol_dict['policy']] * len(df), int)
    out.update(claim_to_cessions(claim, pol_dict, treaty_df))
    nonzero = out['claim'] > 0  # discard zero claims
    rbp = pd.DataFrame({k: out[k][nonzero] for k in out})
    # ex: event_id, policy_id, retention, claim, surplus, quota_shared, wxlr
    rbp['policy_grp'] = build_policy_grp(pol_dict, treaty_df)
    return rbp


# called by post_risk
def by_event(rbp, treaty_df, mon=Monitor()):
    with mon('processing reinsurance by policy', measuremem=True):
        # this is very fast
        tdf = treaty_df.set_index('code')
        inpcols = ['eid', 'claim'] + [t.id for _, t in tdf.iterrows()
                                      if t.type != 'catxl']
        outcols = ['retention', 'claim'] + list(tdf.index)
        idx = {col: i for i, col in enumerate(outcols)}
        eids, idxs = np.unique(rbp.event_id.to_numpy(), return_inverse=True)
        rbp['eid'] = idxs
        E = len(eids)
        dic = dict(event_id=eids)
        keys, datalist = [], []
        for key, grp in rbp.groupby('policy_grp'):
            logging.info('Processing policy group %r with %d rows',
                         key, len(grp))
            data = np.zeros((E, len(outcols)))
            gb = grp[inpcols].groupby('eid').sum()
            for i, col in enumerate(inpcols):
                if i > 0:  # claim, noncat1, ...
                    data[gb.index, i] = gb[col].to_numpy()
            data[:, 0] = data[:, 1]  # retention = claim - noncats
            for c in range(2, len(outcols)):
                data[:, 0] -= data[:, c]
            keys.append(key)
            datalist.append(data)
        del rbp['eid'], rbp['policy_grp']

    with mon('reinsurance by event', measuremem=True):
        # this is fast
        overspill = {}
        res = clever_agg(keys, datalist, tdf, idx, overspill, eids)

        # sanity check on the result
        ret = res[:, 0]
        claim = res[:, 1]
        cession = res[:, 2:].sum(axis=1)
        np.testing.assert_allclose(cession + ret, claim)

        dic.update({col: res[:, c] for c, col in enumerate(outcols)})
        dic.update(overspill)
        alias = dict(zip(tdf.index, tdf.id))
        df = pd.DataFrame(dic).rename(columns=alias)
    return df


def reins_by_policy(dstore, policy_df, treaty_df, loss_id, monitor):
    """
    Task function called by post_risk
    """
    rbe_mon = monitor('reading risk_by_event')
    policies = [dict(policy) for _, policy in policy_df.iterrows()]
    dfs = []
    with dstore:
        nrows = len(dstore['risk_by_event/agg_id'])
        for slc in gen_slices(0, nrows, hdf5.MAX_ROWS):
            with rbe_mon:
                rbe_df = dstore.read_df(
                    'risk_by_event', sel={'loss_id': loss_id}, slc=slc)
            for policy in policies:
                dfs.append(by_policy(rbe_df, policy, treaty_df))
    if dfs:
        yield pd.concat(dfs)
