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

from openquake.baselib import python3compat
from openquake.calculators import base
from openquake.risklib.reinsurance import reinsurance_losses


@base.calculators.add('reinsurance_risk')
class ReinsuranceCalculator(base.RiskCalculator):
    """
    Reinsurance calculator used in the tests, working for fixed losses
    """
    def execute(self):
        assets = self.assetcol.to_dframe()
        assets['id'] = python3compat.decode(assets.id.to_numpy())
        losses_df = reinsurance_losses(assets,
                                       self.ins_loss_df,
                                       self.policy_df,
                                       self.treaty_df)
        self.datastore.create_df('reinsurance_losses', losses_df)

    def post_execute(self):
        pass
