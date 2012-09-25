# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=W0232,R0914

"""
This module performs risk calculations using the scenario
damage assessment approach.
"""

import os

from openquake import logs
from openquake.calculators.risk import general
from openquake.db.models import Output, FragilityModel
from openquake.db.models import DmgDistPerAsset
from openquake.db.models import DmgDistPerAssetData, DmgDistPerTaxonomy
from openquake.db.models import (DmgDistPerTaxonomyData,
DmgDistTotal, DmgDistTotalData, ExposureModel, CollapseMap, CollapseMapData)
from openquake.db.models import inputs4job
from openquake.utils.tasks import distribute
from openquake.export.risk import export_dmg_dist_per_asset
from openquake.export.risk import export_dmg_dist_per_taxonomy
from openquake.export.risk import export_dmg_dist_total, export_collapse_map
from risklib import scenario_damage as risklib

LOGGER = logs.LOG


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Damage method for performing risk calculations.
    """

    def __init__(self, job_ctxt):
        general.BaseRiskCalculator.__init__(self, job_ctxt)

        # fractions of each damage state per building taxonomy
        # for the entire computation
        self.dd_taxonomy_means = {}
        self.dd_taxonomy_stddevs = {}

        # fractions of each damage state for the distribution
        # of the entire computation
        self.total_distribution_means = None
        self.total_distribution_stddevs = None

    def pre_execute(self):
        """
        Perform the following pre-execution tasks:

        * store the exposure model specified in the
        configuration file into database
        * store the fragility model specified in the
        configuration file into database
        * split the interested sites into blocks for
        later processing
        * write the initial database container records
        for calculation results
        """

        self.store_exposure_assets()
        self.store_fragility_model()
        self.partition()

        oq_job = self.job_ctxt.oq_job
        fm = _fm(oq_job)
        damage_states = risklib.damage_states(fm)

        output = Output(
            owner=oq_job.owner,
            oq_job=oq_job,
            display_name="SDA (damage distributions per asset) "
                "results for calculation id %s" % oq_job.id,
            db_backed=True,
            output_type="dmg_dist_per_asset")

        output.save()

        DmgDistPerAsset(
            output=output,
            dmg_states=damage_states).save()

        output = Output(
            owner=oq_job.owner,
            oq_job=oq_job,
            display_name="SDA (damage distributions per taxonomy) "
                "results for calculation id %s" % oq_job.id,
            db_backed=True,
            output_type="dmg_dist_per_taxonomy")

        output.save()

        DmgDistPerTaxonomy(
            output=output,
            dmg_states=damage_states).save()

        output = Output(
            owner=oq_job.owner,
            oq_job=oq_job,
            display_name="SDA (total damage distributions) "
                "results for calculation id %s" % oq_job.id,
            db_backed=True,
            output_type="dmg_dist_total")

        output.save()

        DmgDistTotal(
            output=output,
            dmg_states=damage_states).save()

        output = Output(
            owner=oq_job.owner,
            oq_job=oq_job,
            display_name="SDA (collapse map) "
                "results for calculation id %s" % oq_job.id,
            db_backed=True,
            output_type="collapse_map")

        output.save()

        [ism] = inputs4job(oq_job.id, input_type="exposure")
        [em] = ExposureModel.objects.filter(input=ism, owner=oq_job.owner)

        CollapseMap(
            output=output,
            exposure_model=em).save()

    def execute(self):
        """
        Dispatch the computation into multiple tasks.
        """

        LOGGER.debug("Executing scenario damage risk computation.")

        region_fractions = distribute(
            general.compute_risk, ("block_id", self.job_ctxt.blocks_keys),
            tf_args=dict(job_id=self.job_ctxt.job_id))

        self.dd_taxonomy_means, self.dd_taxonomy_stddevs = \
            risklib.damage_distribution_by_taxonomy(region_fractions)

        self.total_distribution_means, self.total_distribution_stddevs = \
            risklib.total_damage_distribution(region_fractions)

        LOGGER.debug("Scenario damage risk computation completed.")

    def compute_risk(self, block_id, **kwargs):
        """
        Compute the results for a single block.

        Currently we support the computation of:
        * damage distributions per asset
        * damage distributions per building taxonomy
        * total damage distribution
        * collapse maps

        :param block_id: id of the region block data.
        :type block_id: integer
        :keyword fmodel: fragility model associated to this computation.
        :type fmodel: instance of
            :py:class:`openquake.db.models.FragilityModel`
        :return: the sum of the fractions (for each damage state)
            per asset taxonomy for the computed block.
        :rtype: `dict` where each key is a string representing a
            taxonomy and each value is the sum of fractions of all
            the assets related to that taxonomy (represented as
            a 2d `numpy.array`)
        """

        fragility_model = _fm(self.job_ctxt.oq_job)
        frag_functions = fragility_model.functions_by_taxonomy()
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        ground_motion_field_loader = lambda site: general.load_gmvs_at(
            self.job_ctxt.job_id, general.hazard_input_site(
            self.job_ctxt, site))

        assets_loader = lambda site: general.BaseRiskCalculator.assets_at(
            self.job_ctxt.job_id, site)

        def on_asset_complete_cb(asset, damage_distribution_asset,
                                 collapse_map):

            self._store_cmap(asset, collapse_map)
            self._store_dda(asset, risklib.damage_states(fragility_model),
                damage_distribution_asset)

        return risklib.compute_damage(block.sites, assets_loader,
            (fragility_model, frag_functions), ground_motion_field_loader,
            on_asset_complete_cb)

    def _store_cmap(self, asset, (mean, stddev)):
        """
        Store the collapse map data for the given asset.
        """

        [cm] = CollapseMap.objects.filter(
            output__owner=self.job_ctxt.oq_job.owner,
            output__oq_job=self.job_ctxt.oq_job,
            output__output_type="collapse_map")

        CollapseMapData(
            collapse_map=cm,
            asset_ref=asset.asset_ref,
            value=mean,
            std_dev=stddev,
            location=asset.site).save()

    def _store_dda(self, asset, damage_states, (mean, stddev)):
        """
        Store the damage distribution per asset.

        :param fm: fragility model associated to
            the distribution being stored.
        :type fm: instance of
            :py:class:`openquake.db.models.FragilityModel`
        :param asset: asset associated to the distribution being stored.
        :type asset: instance of :py:class:`openquake.db.model.ExposureData`
        :param fractions: fractions for each damage state associated
            to the given asset.
        :type fractions: 2d `numpy.array`. Each column represents
            a damage state (in order from the lowest
            to the highest). Each row represents the
            values for that damage state for a particular
            ground motion value.
        """

        [dds] = DmgDistPerAsset.objects.filter(
                output__owner=self.job_ctxt.oq_job.owner,
                output__oq_job=self.job_ctxt.oq_job,
                output__output_type="dmg_dist_per_asset")

        for x in xrange(len(mean)):
            DmgDistPerAssetData(
                dmg_dist_per_asset=dds,
                exposure_data=asset,
                dmg_state=damage_states[x],
                mean=mean[x],
                stddev=stddev[x],
                location=asset.site).save()

    def _store_ddt(self):
        """
        Store the damage distribution per building taxonomy.
        """

        [ddt] = DmgDistPerTaxonomy.objects.filter(
                output__owner=self.job_ctxt.oq_job.owner,
                output__oq_job=self.job_ctxt.oq_job,
                output__output_type="dmg_dist_per_taxonomy")

        fm = _fm(self.job_ctxt.oq_job)
        damage_states = risklib.damage_states(fm)

        for taxonomy in self.dd_taxonomy_means.keys():

            for x in xrange(len(self.dd_taxonomy_means[taxonomy])):
                DmgDistPerTaxonomyData(
                    dmg_dist_per_taxonomy=ddt,
                    taxonomy=taxonomy,
                    dmg_state=damage_states[x],
                    mean=self.dd_taxonomy_means[taxonomy][x],
                    stddev=self.dd_taxonomy_stddevs[taxonomy][x]).save()

    def _store_total_distribution(self):
        """
        Store the total damage distribution.
        """

        [dd] = DmgDistTotal.objects.filter(
                output__owner=self.job_ctxt.oq_job.owner,
                output__oq_job=self.job_ctxt.oq_job,
                output__output_type="dmg_dist_total")

        fm = _fm(self.job_ctxt.oq_job)

        for x in xrange(len(self.total_distribution_means)):
            DmgDistTotalData(
                dmg_dist_total=dd,
                dmg_state=risklib.damage_states(fm)[x],
                mean=self.total_distribution_means[x],
                stddev=self.total_distribution_stddevs[x]).save()

    def post_execute(self):
        """
        Export the results to file if the `output-type`
        parameter is set to `xml`. We currently export:

        * damage distributions per asset
        * damage distributions per building taxonomy
        * total damage distribution
        """

        self._store_ddt()
        self._store_total_distribution()

        if "xml" in self.job_ctxt.serialize_results_to:
            [output] = Output.objects.filter(
                oq_job=self.job_ctxt.oq_job.id,
                output_type="dmg_dist_per_asset")

            target_dir = os.path.join(
                self.job_ctxt.params.get("BASE_PATH"),
                self.job_ctxt.params.get("OUTPUT_DIR"))

            export_dmg_dist_per_asset(output, target_dir)

            [output] = Output.objects.filter(
                oq_job=self.job_ctxt.oq_job.id,
                output_type="dmg_dist_per_taxonomy")

            export_dmg_dist_per_taxonomy(output, target_dir)

            [output] = Output.objects.filter(
                oq_job=self.job_ctxt.oq_job.id,
                output_type="dmg_dist_total")

            export_dmg_dist_total(output, target_dir)

            [output] = Output.objects.filter(
                oq_job=self.job_ctxt.oq_job.id,
                output_type="collapse_map")

            export_collapse_map(output, target_dir)


def _fm(oq_job):
    """
    Return the fragility model related to the current computation.
    """

    [ism] = inputs4job(oq_job.id, input_type="fragility")
    [fm] = FragilityModel.objects.filter(input=ism, owner=oq_job.owner)

    return fm
