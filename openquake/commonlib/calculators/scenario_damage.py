#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging

import numpy

from openquake.hazardlib import site
from openquake.risklib import scientific
from openquake.baselib.general import AccumDict
from openquake.commonlib.calculators import base, calc
from openquake.commonlib.export import export
from openquake.commonlib.risk_writers import (
    DmgState, DmgDistPerTaxonomy, DmgDistPerAsset, DmgDistTotal,
    ExposureData, Site)


def scenario_damage(riskinputs, riskmodel, rlzs_assoc, monitor):
    """
    Core function for a damage computation.

    :param riskinputs:
        a list of :class:`openquake.risklib.workflows.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.workflows.RiskModel` instance
    :param monitor:
        :class:`openquake.commonlib.parallel.PerformanceMonitor` instance
    :returns:
        a dictionary {('asset', asset): <mean stddev>,
                      ('taxonomy', asset.taxonomy): <damage array>}
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    with monitor:
        result = AccumDict()  # (key_type, key) -> result
        for [(assets, fractions)] in riskmodel.gen_outputs(
                riskinputs, rlzs_assoc):
            for asset, fraction in zip(assets, fractions):
                damages = fraction * asset.number
                result += {('asset', asset): scientific.mean_std(damages)}
                result += {('taxonomy', asset.taxonomy): damages}
    return result


def expand(data_dict, filtered_sites):
    """
    Expand arrays with n elements into arrays of N elements (with N > n)
    by adding zeros. n is the number of filtered sites, N the total number.

    :param data_dict: a dictionary key -> imt -> array with n elements
    :param filtered_sites: a filtered SiteCollection
    :returns: a dictionary key -> imt -> array with N elements
    """
    if isinstance(filtered_sites, site.SiteCollection):
        # nothing was filtered, do nothing
        return data_dict

    expanded = {}
    for key, data_by_imt in data_dict.iteritems():
        expanded[key] = {imt: filtered_sites.expand(array, 0)
                         for imt, array in data_by_imt.iteritems()}
    return expanded


@base.calculators.add('scenario_damage')
class ScenarioDamageCalculator(base.RiskCalculator):
    """
    Scenario damage calculator
    """
    hazard_calculator = 'scenario'
    core_func = scenario_damage
    result_kind = 'damages_by_key'

    def pre_execute(self):
        """
        Compute the GMFs and build the riskinputs.
        """
        super(ScenarioDamageCalculator, self).pre_execute()

        logging.info('Computing the GMFs')
        haz_out, hcalc = base.get_hazard(self)
        gmfs_by_trt_gsim = expand(haz_out['gmfs_by_trt_gsim'], hcalc.sites)
        gmfs_by_imt = calc.data_by_imt(
            gmfs_by_trt_gsim, self.oqparam.imtls, len(self.sitecol))

        logging.info('Preparing the risk input')
        self.rlzs_assoc = haz_out['rlzs_assoc']
        self.riskinputs = self.build_riskinputs(gmfs_by_imt)

    def post_execute(self, result):
        """
        :param result: a dictionary {
             ('asset', asset): <mean stddev>,
             ('taxonomy', asset.taxonomy): <damage array>}
        :returns: a dictionary {
             'dmg_per_asset': /path/to/dmg_per_asset.xml,
             'dmg_per_taxonomy': /path/to/dmg_per_taxonomy.xml,
             'dmg_total': /path/to/dmg_total.xml}
        """
        dmg_states = [DmgState(s, i)
                      for i, s in enumerate(self.riskmodel.damage_states)]
        dd_taxo = []
        dd_asset = []
        shape = self.oqparam.number_of_ground_motion_fields, len(dmg_states)
        totals = numpy.zeros(shape)  # R x D matrix
        for (key_type, key), values in result.iteritems():
            if key_type == 'taxonomy':
                # values are fractions, R x D matrix
                totals += values
                means, stds = scientific.mean_std(values)
                for dmg_state, mean, std in zip(dmg_states, means, stds):
                    dd_taxo.append(
                        DmgDistPerTaxonomy(key, dmg_state, mean, std))
            elif key_type == 'asset':
                means, stddevs = values
                for dmg_state, mean, std in zip(dmg_states, means, stddevs):
                    dd_asset.append(
                        DmgDistPerAsset(
                            ExposureData(key.id, Site(*key.location)),
                            dmg_state, mean, std))
        dd_total = []
        for dmg_state, total in zip(dmg_states, totals.T):
            mean, std = scientific.mean_std(total)
            dd_total.append(DmgDistTotal(dmg_state, mean, std))

        # export
        f1 = export(('dmg_dist_per_asset', 'xml'), self.oqparam.export_dir,
                    dmg_states, dd_asset)
        f2 = export(('dmg_dist_per_taxonomy', 'xml'), self.oqparam.export_dir,
                    dmg_states, dd_taxo)
        f3 = export(('dmg_dist_total', 'xml'), self.oqparam.export_dir,
                    dmg_states, dd_total)
        max_damage = dmg_states[-1]
        # the collapse map is extracted from the damage distribution per asset
        # (dda) by taking the value corresponding to the maximum damage
        collapse_map = [dda for dda in dd_asset if dda.dmg_state == max_damage]
        f4 = export(('collapse_map', 'xml'), self.oqparam.export_dir,
                    dmg_states, collapse_map)
        return f1 + f2 + f3 + f4
