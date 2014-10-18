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
import collections

import numpy

from openquake.risklib import scientific
from openquake.lite.calculators import calculator, calc, \
    BaseScenarioCalculator, core
from openquake.lite.export import export


class DmgState(object):
    def __init__(self, dmg_state, lsi):
        self.dmg_state = dmg_state
        self.lsi = lsi

DmgDistPerTaxonomy = collections.namedtuple(
    'DmgDistPerTaxonomy', 'taxonomy dmg_state mean stddev')

DmgDistPerAsset = collections.namedtuple(
    'DmgDistPerAsset', 'exposure_data dmg_state mean stddev')

DmgDistTotal = collections.namedtuple(
    'DmgDistTotal', 'dmg_state mean stddev')

ExposureData = collections.namedtuple(
    'ExposureData', 'asset_ref site')


class Site(object):
    def __init__(self, xy):
        self.x, self.y = xy
        self.wkt = 'POINT(%s %s)' % xy


@calculator.add('scenario_damage')
class ScenarioDamageCalculator(BaseScenarioCalculator):
    """
    Scenario damage calculator
    """
    def post_execute(self, result):
        """
        Process the result dictionary and export three files:

        - dmg_per_asset.xml
        - dmg_per_taxonomy.xml
        - dmg_total.xml
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
                # values are mean and stddev, at D x 2 matrix
                for dmg_state, mean_std in zip(dmg_states, values):
                    dd_asset.append(
                        DmgDistPerAsset(
                            ExposureData(key.id, Site(key.location)),
                            dmg_state, mean_std[0], mean_std[1]))
        dd_total = []
        for dmg_state, total in zip(dmg_states, totals):
            mean, std = scientific.mean_std(total)
            dd_total.append(DmgDistTotal(dmg_state, mean, std))

        # export
        f1 = export('dmg_per_asset_xml', self.oqparam.export_dir,
                    self.riskmodel.damage_states, dd_asset)
        f2 = export('dmg_per_taxonomy_xml', self.oqparam.export_dir,
                    self.riskmodel.damage_states, dd_taxo)
        f3 = export('dmg_total_xml', self.oqparam.export_dir,
                    self.riskmodel.damage_states, dd_total)
        return [f1, f2, f3]


@core(ScenarioDamageCalculator)
def scenario_damage(riskinputs, riskmodel):
    """
    Core function for a damage computation.
    """
    logging.info('Process %d, considering %d risk input(s) of weight %d',
                 os.getpid(), len(riskinputs),
                 sum(ri.weight for ri in riskinputs))
    result = {}  # (key_type, key) -> result
    for loss_type, (assets, fractions) in \
            riskmodel.gen_outputs(riskinputs):
        fracts_by_taxo = {}
        for asset, fraction in zip(assets, fractions):
            fracts = fraction * asset.number
            mean_std = numpy.array(scientific.mean_std(fracts))
            result = calc.add_dicts(result, {('asset', asset): mean_std})

            taxo = asset.taxonomy
            try:
                fracts_by_taxo[taxo] = fracts_by_taxo[taxo] + fracts
            except KeyError:
                fracts_by_taxo[taxo] = fracts
        result = calc.add_dicts(
            result, {('taxonomy', taxo): fracts
                     for taxo, fracts in fracts_by_taxo.iteritems()})
    return result
