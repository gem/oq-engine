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


def check_fields(fields, header, fname):
    """
    Make sure the right fields are present in a CSV file. For instance:

    >>> check_fields(['deductible'], [], '*')
    Traceback (most recent call last):
     ...
    openquake.baselib.InvalidFile: *: deductible is missing in the header
    """
    for field in fields:
        if field not in header:
            raise InvalidFile(f'{fname}: {field} is missing in the header')


def parse(fname):
    """
    Parse a reinsurance.xml file and returns (policy_df, treaties)
    """
    rmodel = nrml.read(fname).reinsuranceModel
    fieldmap = {}
    for node in rmodel.fieldMap:
        fieldmap[node['input']] = node['oq']
    policyfname = os.path.join(os.path.dirname(fname), ~rmodel.policies)
    nonprop = [treaty.attrib for treaty in rmodel.nonProportional]
    dic = {col: [] for col in TREATY_COLUMNS}
    for tr in nonprop:
        for name in TREATY_COLUMNS:
            dic[name].append(tr[name])
    df = pd.read_csv(policyfname, keep_default_na=False).rename(columns=fieldmap)
    check_fields(['deductible', 'liability'], df.columns, fname)
    return df, pd.DataFrame(dic)

    
# tested in test_reinsurance.py
def reinsurance(agglosses, pol, treaties):
    '''
    :param DataFrame losses:
        losses aggregated by policy (keys agg_id, event_id)
    :param Series pol:
        Description of policy characteristics
    :param DataFrame treaties:
        Description of reinsurance characteristics
    :returns:
        DataFrame of reinsurance losses by event ID and policy ID
    '''
    out = {}
    df = agglosses[agglosses.agg_id == pol['policy']]
    losses = df.loss.to_numpy()
    ded, lim = get_ded_lim(losses, pol)
    out['claim'] = claim = scientific.insured_losses(losses, ded, lim)
    out['event_id'] = df.event_id.to_numpy()
    out['policy_id'] = [pol['policy']] * len(df)
    if pol['treaty']:
        [treaty_id] = pol['treaty'].split()
        tr = treaties.loc[treaty_id]
        cession = tr['qs_cession'] * claim
        over = cession > tr['treaty_limit']
        cession[over] = tr['treaty_limit']
        out['cession'] = cession
    else:
        out['cession'] = np.zeros_like(claim)
    out['retention'] = claim - out['cession']
    return pd.DataFrame(out)
