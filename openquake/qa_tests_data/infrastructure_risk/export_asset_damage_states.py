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

# NOTE: this postprocessing algorithm is used after connectivity analysis to
# export a csv file containing damage by asset and event

from openquake.commonlib.datastore import read
import pandas as pd

dstore = read(-1)

oq = dstore["oqparam"]
calculation_mode = oq.calculation_mode
assert calculation_mode in ("event_based_damage", "scenario_damage")

assetcol = dstore["assetcol"]
tagnames = sorted(tn for tn in assetcol.tagnames if tn != "id")
tags = {t: getattr(assetcol.tagcol, t) for t in tagnames}
exposure_df = (
    assetcol.to_dframe()
    .replace(
        {
            tagname: {i: tag for i, tag in enumerate(tags[tagname])}
            for tagname in tagnames
        }
    )
    .assign(id=lambda df: df.id.str.decode("utf-8"))
    .set_index("id")
)

agg_keys = pd.DataFrame(
    {"id": [key.decode() for key in dstore["agg_keys"][:]]})
# damage_df = (
#     dstore.read_df("risk_by_event", "event_id")
#     .join(agg_keys.id, on="agg_id")
#     .dropna(subset=["id"])
#     .set_index("id", append=True)
#     .drop(columns=["agg_id", "loss_id"])
#     .sort_index(level=["event_id", "id"])
#     .astype(int)
#     .join(exposure_df)
# )

damage_df = (
    dstore.read_df("risk_by_event", "event_id")
    .join(agg_keys.id, on="agg_id")
    .dropna(subset=["id"])
    .set_index("id", append=True)
    .drop(columns=["agg_id", "loss_id"])
    .sort_index(level=["event_id", "id"])
    .astype(int)
)

# Delete assets with no damage
# damage_df['dmg_sum'] = (
#     damage_df['dmg_1'] + damage_df['dmg_2']
#     + damage_df['dmg_3'] + damage_df['dmg_4'])
# damage_df = damage_df[damage_df['dmg_sum']!=0]
# damage_df.drop(columns=['dmg_sum'], inplace=True)
damage_df.to_csv("Damage_by_Asset_and_Event.csv", float_format="%.0f")

# Save only assets with complete damge
# damage_df = damage_df[damage_df['dmg_4']!=0]
# damage_df.drop(columns=['dmg_1', 'dmg_2', 'dmg_3', 'dmg_4'], inplace=True)
# damage_df.to_csv(
#     "Damage_by_Asset_and_Event_no_exposure_complete_damage_48037.csv",
#     float_format="%.0f")
