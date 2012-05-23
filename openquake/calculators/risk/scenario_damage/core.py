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

from django.contrib.gis import geos

from openquake import logs
from openquake.calculators.risk import general
from openquake.db.models import Output, FragilityModel
from openquake.db.models import DmgDistPerAsset, Ffc, Ffd
from openquake.db.models import DmgDistPerAssetData
from openquake.db.models import inputs4job
from openquake.export.risk import export_dmg_dist_per_asset


LOGGER = logs.LOG


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """
    Scenario Damage method for performing risk calculations.
    """

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

        output = Output(
            owner=oq_job.owner,
            oq_job=oq_job,
            display_name="SDA results for calculation id %s" % oq_job.id,
            db_backed=True,
            output_type="dmg_dist_per_asset")

        output.save()

        fm = _fm(oq_job)

        DmgDistPerAsset(
            output=output,
            dmg_states=_damage_states(fm.lss)).save()

    def execute(self):
        """
        Dispatch the computation into multiple tasks.
        """

        LOGGER.debug("Executing scenario damage risk computation.")
        tasks = []

        for block_id in self.job_ctxt.blocks_keys:
            LOGGER.debug("Dispatching task for block %s of %s" % (
                    block_id, len(self.job_ctxt.blocks_keys)))

            task = general.compute_risk.delay(self.job_ctxt.job_id, block_id,
                fmodel=_fm(self.job_ctxt.oq_job))

            tasks.append(task)

        for task in tasks:
            task.wait()

            if not task.successful():
                raise Exception(task.result)

        LOGGER.debug("Scenario damage risk computation completed.")

    def compute_risk(self, block_id, **kwargs):
        """
        Compute the results for a single block.

        Currently we  only support the computation of
        damage distributions per asset (i.e. mean and stddev
        of the distribution for each damage state related to the asset).

        :param block_id: id of the region block data.
        :type block_id: integer
        :keyword fmodel: fragility model associated to this computation.
        :type fmodel: instance of
            :py:class:`openquake.db.models.FragilityModel`
        """

        fm = kwargs["fmodel"]
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        [dds] = DmgDistPerAsset.objects.filter(
                output__owner=self.job_ctxt.oq_job.owner,
                output__oq_job=self.job_ctxt.oq_job,
                output__output_type="dmg_dist_per_asset")

        fset = fm.ffd_set if fm.format == "discrete" else fm.ffc_set

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

                mean, stddev = compute_mean_stddev(gmf, funcs, asset)

                for x in xrange(len(mean)):
                    DmgDistPerAssetData(
                        dmg_dist_per_asset=dds,
                        exposure_data=asset,
                        dmg_state=_damage_states(fm.lss)[x],
                        mean=mean[x],
                        stddev=stddev[x],
                        location=geos.GEOSGeometry(
                        site.point.to_wkt())).save()

    def post_execute(self):
        """
        Export the results to file if the `output-type`
        parameter is set to `xml`.
        """

        if "xml" in self.job_ctxt.serialize_results_to:
            [output] = Output.objects.filter(
                oq_job=self.job_ctxt.oq_job.id,
                output_type="dmg_dist_per_asset")

            target_dir = os.path.join(
                self.job_ctxt.params.get("BASE_PATH"),
                self.job_ctxt.params.get("OUTPUT_DIR"))

            export_dmg_dist_per_asset(output, target_dir)


def compute_mean_stddev(gmf, funcs, asset):
    """
    Compute the mean and the standard deviation distribution
    for the given asset for each damage state.

    :param gmf: ground motion values computed in the grid
        point where the asset is located.
    :type gmf: list of floats
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lower
        limit state to the one with the higher limit state.
    :type funcs: list of
        :py:class:`openquake.db.models.Ffc` instances
    :param asset: asset where the distribution must
        be computed on.
    :type asset: instance of
        :py:class:`openquake.db.models.ExposureData`
    :returns: the mean and the standard deviation for
        each damage state.
    :rtype: two `numpy.array`. The first one contains
        the mean for each damage state, the second one
        contains the standard deviation. Both arrays
        have a number of columns that is equal to the
        number of damage states.
    """

    # we always have a number of damage states
    # which is len(limit states) + 1
    sum_ds = numpy.zeros((len(gmf), len(funcs) + 1))

    for x, gmv in enumerate(gmf):
        sum_ds[x] += compute_dm(funcs, gmv)

    nou = asset.number_of_units
    mean = numpy.mean(sum_ds, axis=0) * nou
    stddev = numpy.std(sum_ds, axis=0, ddof=1) * nou

    return mean, stddev


def compute_dm(funcs, gmv):
    """
    Compute the fraction of buildings for each damage state.

    :param gmv: ground motion value that defines the Intensity
        Measure Level used to interpolate the fragility functions.
    :type gmv: float
    :param funcs: list of fragility functions describing
        the distribution for each limit state. The functions
        must be in order from the one with the lower
        limit state to the one with the higher limit state.
    :type funcs: list of
        :py:class:`openquake.db.models.Ffc` instances
    :returns: the fraction of buildings for each damage state
        computed of the given ground motion value.
    :rtype: 1d `numpy.array`
    """

    def _no_damage(fm, gmv):
        """
        Evaluate condition to apply algorithm.
        """
        discrete = fm.format == "discrete"
        no_damage_limit = fm.no_damage_limit != None

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
