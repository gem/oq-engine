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
import math
import numpy
import scipy

from openquake import logs
from openquake.calculators.risk import general
from openquake.db.models import Output, FragilityModel
from openquake.db.models import DmgDistPerAsset, Ffc, Ffd
from openquake.db.models import DmgDistPerAssetData, DmgDistPerTaxonomy
from openquake.db.models import (DmgDistPerTaxonomyData,
DmgDistTotal, DmgDistTotalData, ExposureModel, CollapseMap, CollapseMapData)
from openquake.db.models import inputs4job
from openquake.utils.tasks import distribute
from openquake.export.risk import export_dmg_dist_per_asset
from openquake.export.risk import export_dmg_dist_per_taxonomy
from openquake.export.risk import export_dmg_dist_total, export_collapse_map

LOGGER = logs.LOG


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Damage method for performing risk calculations.
    """

    def __init__(self, job_ctxt):
        general.BaseRiskCalculator.__init__(self, job_ctxt)

        # fractions of each damage state per building taxonomy
        # for the entire computation
        self.ddt_fractions = {}

        # fractions of each damage state for the distribution
        # of the entire computation
        self.total_fractions = None

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
            dmg_states=_damage_states(fm.lss)).save()

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
            dmg_states=_damage_states(fm.lss)).save()

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
            dmg_states=_damage_states(fm.lss)).save()

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
            tf_args=dict(job_id=self.job_ctxt.job_id,
            fmodel=_fm(self.job_ctxt.oq_job)))

        self._collect_fractions(region_fractions)

        LOGGER.debug("Scenario damage risk computation completed.")

    def _collect_fractions(self, region_fractions):
        """
        Sum the fractions (of each damage state per building taxonomy)
        of each computation block.

        :param region_fractions: fractions for each damage state
            per building taxonomy for each different block computed.
        :type region_fractions: `list` of 2d `numpy.array`.
            Each column of the array represents a damage state (in order from
            the lowest to the highest). Each row represents the
            values for that damage state for a particular
            ground motion value.
        """

        for bfractions in region_fractions:
            for taxonomy in bfractions.keys():
                fractions = self.ddt_fractions.get(taxonomy, None)

                # sum per taxonomy
                if not fractions:
                    self.ddt_fractions[taxonomy] = numpy.array(
                        bfractions[taxonomy])
                else:
                    self.ddt_fractions[taxonomy] += bfractions[taxonomy]

                # global sum
                if self.total_fractions is None:
                    self.total_fractions = numpy.array(
                        bfractions[taxonomy])
                else:
                    self.total_fractions += bfractions[taxonomy]

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

        fm = kwargs["fmodel"]
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)
        fset = fm.ffd_set if fm.format == "discrete" else fm.ffc_set

        # fractions of each damage state per building taxonomy
        # for the given block
        ddt_fractions = {}

        for site in block.sites:
            point = self.job_ctxt.region.grid.point_at(site)
            gmf = general.load_gmvs_at(self.job_ctxt.job_id, point)

            assets = general.BaseRiskCalculator.assets_at(
                self.job_ctxt.job_id, site)

            for asset in assets:
                funcs = fset.filter(
                    taxonomy=asset.taxonomy).order_by("lsi")

                assert len(funcs) > 0, ("no limit states associated "
                        "with taxonomy %s of asset %s.") % (
                        asset.taxonomy, asset.asset_ref)

                fractions = compute_gmf_fractions(
                    gmf, funcs) * asset.number_of_units

                current_fractions = ddt_fractions.get(
                    asset.taxonomy, numpy.zeros((len(gmf), len(funcs) + 1)))

                ddt_fractions[asset.taxonomy] = current_fractions + fractions

                self._store_dda(fractions, asset, fm)

                # the collapse map needs the fractions
                # for each ground motion value of the
                # last damage state (the last column)
                self._store_cmap(fractions[:, -1], asset)

        return ddt_fractions

    def _store_cmap(self, dstate, asset):
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
            value=numpy.mean(dstate),
            std_dev=numpy.std(dstate, ddof=1),
            location=asset.site).save()

    def _store_dda(self, fractions, asset, fm):
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

        mean = numpy.mean(fractions, axis=0)
        stddev = numpy.std(fractions, axis=0, ddof=1)

        for x in xrange(len(mean)):
            DmgDistPerAssetData(
                dmg_dist_per_asset=dds,
                exposure_data=asset,
                dmg_state=_damage_states(fm.lss)[x],
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

        for taxonomy in self.ddt_fractions.keys():
            mean = numpy.mean(self.ddt_fractions[taxonomy], axis=0)
            stddev = numpy.std(self.ddt_fractions[taxonomy], axis=0, ddof=1)

            for x in xrange(len(mean)):
                DmgDistPerTaxonomyData(
                    dmg_dist_per_taxonomy=ddt,
                    taxonomy=taxonomy,
                    dmg_state=_damage_states(fm.lss)[x],
                    mean=mean[x],
                    stddev=stddev[x]).save()

    def _store_total_distribution(self):
        """
        Store the total damage distribution.
        """

        [dd] = DmgDistTotal.objects.filter(
                output__owner=self.job_ctxt.oq_job.owner,
                output__oq_job=self.job_ctxt.oq_job,
                output__output_type="dmg_dist_total")

        fm = _fm(self.job_ctxt.oq_job)

        mean = numpy.mean(self.total_fractions, axis=0)
        stddev = numpy.std(self.total_fractions, axis=0, ddof=1)

        for x in xrange(len(mean)):
            DmgDistTotalData(
                dmg_dist_total=dd,
                dmg_state=_damage_states(fm.lss)[x],
                mean=mean[x],
                stddev=stddev[x]).save()

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


def compute_gmf_fractions(gmf, funcs):
    """
    Compute the fractions of each damage state for
    each ground motion value given.

    :param gmf: ground motion values computed in the grid
        point where the asset is located.
    :type gmf: list of floats
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lowest
        limit state to the one with the highest limit state.
    :type funcs: list of
        :py:class:`openquake.db.models.Ffc` instances
    :returns: the fractions for each damage state.
    :rtype: 2d `numpy.array`. Each column represents
        a damage state (in order from the lowest
        to the highest). Each row represents the
        values for that damage state for a particular
        ground motion value.
    """

    # we always have a number of damage states
    # which is len(limit states) + 1
    fractions = numpy.zeros((len(gmf), len(funcs) + 1))

    for x, gmv in enumerate(gmf):
        fractions[x] += compute_gmv_fractions(funcs, gmv)

    return fractions


def compute_gmv_fractions(funcs, gmv):
    """
    Compute the fractions of each damage state for
    the ground motion value given.

    :param gmv: ground motion value that defines the Intensity
        Measure Level used to interpolate the fragility functions.
    :type gmv: float
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lowest
        limit state to the one with the highest limit state.
    :type funcs: list of
        :py:class:`openquake.db.models.Ffc` instances
    :returns: the fraction of buildings of each damage state
        computed for the given ground motion value.
    :rtype: 1d `numpy.array`. Each value represents
        the fraction of a damage state (in order from the lowest
        to the highest)
    """

    def _no_damage(fm, gmv):
        """
        There is no damage when ground motions values are less
        than the first iml or when the no damage limit value
        is greater than the ground motions value.
        """
        discrete = fm.format == "discrete"
        no_damage_limit = fm.no_damage_limit is not None

        return ((discrete and not no_damage_limit and gmv < fm.imls[0]) or
            (discrete and no_damage_limit and gmv < fm.no_damage_limit))

    def compute_poe_con(iml, func):
        """
        Compute the Probability of Exceedance for the given
        Intensity Measure Level using continuous functions.
        """

        variance = func.stddev ** 2.0
        sigma = math.sqrt(math.log((variance / func.mean ** 2.0) + 1.0))
        mu = math.exp(math.log(func.mean ** 2.0 / math.sqrt(
                variance + func.mean ** 2.0)))

        return scipy.stats.lognorm.cdf(iml, sigma, scale=mu)

    def compute_poe_dsc(iml, func):
        """
        Compute the Probability of Exceedance for the given
        Intensity Measure Level using discrete functions.
        """

        highest_iml = func.fragility_model.imls[-1]
        no_damage_limit = func.fragility_model.no_damage_limit

        # when the intensity measure level is above
        # the range, we use the highest one
        if iml > highest_iml:
            iml = highest_iml

        imls = [no_damage_limit] + func.fragility_model.imls
        poes = [0.0] + func.poes

        return scipy.interpolate.interp1d(imls, poes)(iml)

    ftype_poe_map = {Ffc: compute_poe_con, Ffd: compute_poe_dsc}

    # we always have a number of damage states
    # which is len(limit states) + 1
    damage_states = numpy.zeros(len(funcs) + 1)

    fm = funcs[0].fragility_model

    # when we have a discrete fragility model and
    # the ground motion value is below the lowest
    # intensity measure level defined in the model
    # we simply use 100% no_damage and 0% for the
    # remaining limit states
    if _no_damage(fm, gmv):
        damage_states[0] = 1.0
        return numpy.array(damage_states)

    first_poe = ftype_poe_map[funcs[0].__class__](gmv, funcs[0])

    # first damage state is always 1 - the probability
    # of exceedance of first limit state
    damage_states[0] = 1 - first_poe

    last_poe = first_poe

    # starting from one, the first damage state
    # is already computed...
    for x in xrange(1, len(funcs)):
        poe = ftype_poe_map[funcs[x].__class__](gmv, funcs[x])
        damage_states[x] = last_poe - poe
        last_poe = poe

    # last damage state is equal to the probabily
    # of exceedance of the last limit state
    damage_states[len(funcs)] = ftype_poe_map[
        funcs[len(funcs) - 1].__class__](gmv, funcs[len(funcs) - 1])

    return numpy.array(damage_states)


def _damage_states(limit_states):
    """
    Return the damage states from the given limit states.

    For N limit states in the fragility model, we always
    define N+1 damage states. The first damage state
    should always be 'no_damage'.
    """

    dmg_states = list(limit_states)
    dmg_states.insert(0, "no_damage")

    return dmg_states


def _fm(oq_job):
    """
    Return the fragility model related to the current computation.
    """

    [ism] = inputs4job(oq_job.id, input_type="fragility")
    [fm] = FragilityModel.objects.filter(input=ism, owner=oq_job.owner)

    return fm
