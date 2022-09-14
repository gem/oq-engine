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

import pandas as pd
import numpy as np


KNOWN_LOSS_TYPES = {
    'structural', 'nonstructural', 'contents',
    'value-structural', 'value-nonstructural', 'value-contents'}

# !!! This value should be taken from the policy metadata
#     The data include column name and `max_event_cession`
PROP_RI = pd.DataFrame(index=['retention', 'cession_1', 'cession_2', 
                              'cession_3', 'cession_4', 'cession_5'],
                       columns=['col_name', 'max_event_cession'],
                       data=[['Retention', ''],
                             ['Surplus_metro', 10000000 ],
                             ['QS_rural', 100000000 ],
                             ['QS_reg', 25000000 ],
                             ['Sur1_reg', 75000000 ],
                             ['Fac_reg', 75000000 ]]
                       )

def reinsurance_losses(exposure, losses, policy, nonp_treaties):
    '''
    :param DataFrame exposure:
        Exposure in OQ format (id, taxonomy, ...)
    :param DataFrame losses:
        Average annual losses per asset (id, structural, ...)
    :param DataFrame policy:
        Description of policy characteristics in OQ format. It also includes
        the layers of proportional reinsurace treaties
    :param DataFrame nonp_treaties:
        Description of non-proportional reinsurance treaties in OQ format.
    :returns:
        Complete DataFrame with calculation details.
    '''


    # Create single dataframe with total values (exposure and losses)
    assets = tot_cost_losses(exposure, losses)

    # Estimate absolute values for liability, deductible and claims
    # at the policy_unit level
    df = process_policies(assets, policy)
    

    # Estimate proportional reinsurance
    losses = compute_proportional_ri(df)

    # Estimate non-proportional reinsurance
    if 'treaty_id' in losses:
        losses = compute_nonproportional_ri(losses, nonp_treaties)
    else:
        print('The resinsurance programe does not include'
              'non-proportional layers')    

    return losses



def process_policies(assets, df_policy):
    """
    Estimate effective values for the specified `policy_units`
    """

    # Create policy dataframe where all values are applicable per "policy_unit"
    cols = ['id', 'policy', 'total_cost', 'total_losses']

    # DF for policies at `asset` level:
    p_asset = df_policy.policy[df_policy.policy_unit == 'asset']
    df_a = assets[cols][assets.policy.isin(p_asset)]

    # DF for policies at `policy` level:
    p_policy = df_policy.policy[df_policy.policy_unit == 'policy']
    df_p = assets[cols][assets.policy.isin(p_policy)]
    df_p = df_p.groupby(by='policy').sum().reset_index()

    # Unique DF at policy_units
    df = pd.concat([df_a, df_p])
    df = df.merge(df_policy, on='policy')
    assert df.empty is False, 'Empty DataFrame. Check input files'

    # Estimate absolute values 'liability' and 'deductible'
    
    # When values <= 1, then assume input is a fraction
    df.loc[df.liability <= 1, 'liability'] = df.liability * df.total_cost

    if 'deductible' in df.columns:
        df.loc[df.deductible <= 1, 'deductible'] = df.deductible * df.liability
    else:
        df['deductible'] = 0
    
    # Effective deductible
    if 'min_deductible' in df.columns:
        df.loc[df.min_deductible <= 1, 
               'min_deductible'] = df.min_deductible * df.liability

        df.deductible = df[['deductible', 'min_deductible']].max(axis=1)
        df.drop(columns={'min_deductible'}, inplace=True)

    # Estimate 'no_insured' values
    df['no_insured'] = df['total_losses'] - df['liability']
    df.no_insured.clip(lower=0, inplace=True)  # Minimum no_insured = 0

    # Estimate claims
    df['claim'] = df.total_losses - df.no_insured - df.deductible 
    df.claim.clip(lower=0, inplace=True)  # Minimum claim = 0

    return df


def sum_loss_types(df):
    """
    :returns: structural (+ nonstructural) (+ contents)
    """
    losses = np.zeros(len(df))
    for col in df.columns:
        if col in KNOWN_LOSS_TYPES:
            losses += df[col]
    return losses


def tot_cost_losses(exposure, losses):
    """
    Estimate total exposed value and total loss considering all loss types
        (str + nonstr + contents)

    !!! NOTE: If the exposure is specified per area or per building
        (as opposed to total cost), then it is necessary to estimate total cost

    Returns
    -------
    assets:
        DataFrame with total exposure and losses
    """
    exposure['total_cost'] = sum_loss_types(exposure)
    sum_losses = pd.DataFrame(
        dict(id=losses.asset_id.to_numpy(), total_losses=sum_loss_types(losses)))
    assets = exposure.merge(sum_losses, how='inner', on='id')
    assert assets.total_losses.sum() != 0, 'No losses in exposure model'

    return assets


def compute_proportional_ri(df):
    """
    Compute allocations of losses for the proportional reinsurace layers.
    
    It is optional to include proportional layers. To do so, the 
    DataFrame should include at least the columns `retention` and `cession_1`

    When no proportional reinsurance layer are included, then:
        `retention` = `claim` = `total_loss` - `deductible`

    Returns
    -------
    DataFrame with loss allocations to proportional reinsurance treaties.

    """
    
    # Create loss DataFrame
    losses = df[['id', 'policy', 'total_losses', 'deductible', 
                 'claim', 'no_insured']].copy()
    
    # Estimate loss allocations for proportional reinsurance
    if 'retention' in PROP_RI.index:
        
        # Proportional columns
        prop_cols = list(PROP_RI.col_name)
        prop_ri = df[prop_cols].sum(axis=1)
        
        # If sum of layers > 1, then the input data refers to absolute values.
        mask = prop_ri > 1
        if mask.any():
            # Estimate fractions with respect to the liability
            for col in prop_cols:
                df.loc[mask, col] = df.loc[mask, col] / df.liability
        
        # Check that fractions of proportional layers are equal to 1
        prop_ri = df[prop_cols].sum(axis=1)        
        if not (prop_ri == 1).any():
            raise ValueError(
                f'The sum of the fractions specified in proportional'
                f'reinsurance layers must be equal to 1./'
                f'Check policies {df.policy[prop_ri != 1]}')
        
        # Estimate total_losses for each proportional layer
        losses[prop_cols] = df[prop_cols].mul(df.claim, axis=0)
        
    else:
        print('The resinsurance programme does not include '
              'proportional layers')
        # Set all claims to retention
        losses['retention'] = df.claim


    # Include non-proportional treaties if available
    if 'treaty_id' in df.columns:
        losses['treaty_id'] = df.treaty_id.copy()
    
        
    return losses
    
    
def compute_nonproportional_ri(data, treaty):
    """
    Compute allocations of losses for the non-proportional reinsurace layers.
    
    Supported non-proportional treaties:
        - WXL/R: Excess of loss treaty cover which can be triggered by an 
            individual loss
        - CatXL: Excess of loss treaty cover per event (aggregated losses)
    
    Is is optional to include proportional layers. To do so, the 
    DataFrame should include the columns with the treaty allocation.
    
    
    !!! TO BE IMPLEMENTED AFTER THE ALL EVENT LOSSES !!!
    Both WXL/R and CatXL can include a maximum annual_aggregate_limit. 
    When the losses exceed this limit, then the excess loss will be indicated 
    in the overspill column output.
    
    Returns
    -------
    DataFrame with loss allocations to proportional reinsurance treaties

    """
    
    cols = ['treaty_id', 'treaty_type']
    df = data.merge(treaty[cols], 
                    how='left', on='treaty_id')

    # Column name for retention    
    ret_col = PROP_RI.loc['retention', 'col_name']

    # Process WXL/R reinsurance treaties
    for treaty_id in treaty.treaty_id[treaty.treaty_type == 'wxlr']:
        nonp = npri_info(treaty, treaty_id)
        
        # Create column for cession under the reinsurance treaty
        df[nonp.id] = 0        
        mask = df.treaty_id == treaty_id
        df.loc[mask, :] = wxl(df.loc[mask], nonp).copy()

    
    # # Estimate overspill losses
    # Ovespill = losses above 'max_event_cession'
    prop_cols = PROP_RI.col_name[1:]
    agg = df.groupby(cols).sum().reset_index(level=1)
    
    mask = agg.treaty_type == 'catxl'
    for prop_layer in prop_cols:
        max_event = PROP_RI.loc[PROP_RI.col_name==prop_layer, 
                                'max_event_cession'].values[0]
        agg[f'overspill_{prop_layer}'] = agg.loc[mask, prop_layer] - max_event
        agg[f'overspill_{prop_layer}'].clip(lower=0, inplace=True)
        
        # Estimate net loss retentions
        agg[ret_col] = agg[ret_col] + agg[f'overspill_{prop_layer}'].fillna(0)

           

    # Estimate CatXL over net loss retentions
    if 'catxl' in agg.treaty_type.unique():
        for treaty_id in treaty.treaty_id[treaty.treaty_type == 'catxl']:
            # Assign zero values
            agg[treaty_id] = 0
            agg[f'overspill_{treaty_id}'] = 0
            
            nonp = npri_info(treaty, treaty_id)
            retention = agg.loc[treaty_id, ret_col]
            if retention > nonp.deductible:
                cession = min(agg.loc[treaty_id, ret_col] - nonp.deductible,
                              nonp.ri_cover)
            ovs = max(retention - nonp.deductible - cession, 0)
            
            # Assign CatXL params
            agg.loc[treaty_id, treaty_id] = cession
            agg.loc[treaty_id, f'overspill_{prop_layer}'] = ovs
            
    else:
        print('No CatXL treaty types')

    # Estimate event losses
    agg_losses = agg.sum(axis=0, numeric_only=True)

    return df, agg_losses


def npri_info(data, treaty_id):
    """
    Get non-proportional reinsurace parameters

    Returns
    -------
    An object that contains the attributes for the non-proportional treaty:
        `if`: unique identifier for a non-proportional treaty or 
            reinsurance contract.
        `type`: non-proportional reinsurance treaty type. 
            Options ['wxlr', 'catxl'].
        `max_retention`: (deductible or first_loss) limit above which the  
            reinsurer becomes liable for losses up to the upper limit of cover.
        `treaty_limit`: upper limit of cover of the reinsurance treaty.
        `reinsurance_cover`: cover amount between the deductible  
            and the upper limit of cover.
        `aal`: (annual_aggregate_limit) maximum amount of the reinsurance 
            cover for the aggregate of all losses affecting a treaty in a year.

    """    
    df = data.copy()
    df.set_index('treaty_id', inplace=True)
    
    # check mandatory columns
    cols = {'max_retention', 'treaty_limit'}
    
    assert cols.issubset(df.columns), f'Missing mandatory columns {cols}'
    'in non-proportional reinsurance input file.'
    
    npri_info.id = treaty_id    
    npri_info.type = df.loc[treaty_id, 'treaty_type']
    npri_info.deductible = df.loc[treaty_id, 'max_retention']
    npri_info.treaty_limit = df.loc[treaty_id, 'treaty_limit']
    
    npri_info.ri_cover = (npri_info.treaty_limit - npri_info.deductible)

    if 'reinsurance_cover' in df.columns:
        cover = df.loc[treaty_id, 'reinsurance_cover']
        assert cover == npri_info.ri_cover, (' reinsurance_cover != '
        'treaty_limit - max_retention')
    
    # To include in future development
    # npri_info.aal = df.loc[treaty_id, 'annual_aggregate_limit']
    
    return npri_info


def wxl(data, treaty):
    """
    Estimate losses under a WXL/R treaty.
    
    WXL/R (wxlr) is a non-proportional treaty reinsurance under which the  
    reinsurer undertakes, up to the limit of cover, the losses of each  
    individual risk (at the policy_unit level) that exceed the treaty 
    maximum retention (also known as deductible or first loss).
    
    When combined with proportional reinsurance treaties, the WXL/R is applied
    over the net loss retention of the proportional reinsurance programme
    (i.e., applied over the first layer).
    

    Parameters
    ----------
    :param DataFrame df:
        Losses after applying non-proportional reinsurance treaties.
        If only non-proportional treaties exist, then the df includes at least
        the columns ('total_losses', 'deductible', 'claim', 'no_insured')
    treaty : object
        Contains the attributes for the non-proportional treaty
        [id, type, deductible, reinsurance_cover, and 
         aal (annual_aggregate_limit)]     

    Returns
    -------
    DataFrame with losses per reinsurace treaty layer.

    """
    # Copy DataFrame to avoid a copy of a slice
    df = data.copy()
    
    # Column name for retention
    ret_col = PROP_RI.loc['retention', 'col_name']   

    # Losses exceeding the deductible (Minimum cession = 0)
    cession = df[ret_col] - treaty.deductible
    
    # Limit the cession between zero and the treaty cover limit
    cession.clip(lower=0, upper=treaty.ri_cover, inplace=True)
    
    # Estimate WXL/R cession
    df[treaty.id] = cession
        
    # Retention after WXL/R
    df[ret_col] = df[ret_col] - cession
        
    
    return df



#%% CHECK TO BE ADDED

# Input validation (to be implemented):
# ------------------------------------------------------------------------
#  EXPOSURE MODEL
#   - Exposure model in OQ format and with 'policy' column
#
#  POLICY AND REINSURANCE FILES
#   - Check that all policies in assets are within policy file
#   - For the following colummns check:
#       `policy`        : each row should be unique (no duplicated policy)
#       `policy_unit`   : str. Options: ['asset', 'policy']
#       `liability`     : float >= 0
#       `deductible`    : float >= 0
#       `min_deductible`: float >= 0
#
#  PROPORTIONAL REINSURANCE 
#   - Raise value if total_losses not indicated in job_ini

#  NON-PROPORTIONAL REINSURANCE 
#   - Check that all nonprop_ri are within the reinsurance file
#   - For the following colummns check:
#       `treaty`      : each row should be unique (no duplicated treaty)
#       `treaty_type` : str.
#           Options: ['quota_share', 'surplus', 'WXL', 'CatXL']
#       `treaty_unit `: str.
#           Options: ['policy', 'treaty', 'event']
#       `qs_retention`:  0 <= float <= 1
#       `qs_cession`  :  0 <= float <= 1
#       `surplus_line`: float >= 0
#       `treaty_limit`: float >= 0