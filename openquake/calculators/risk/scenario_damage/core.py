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

# pylint: disable=W0232

"""
This module performs risk calculations using the scenario
damage assessment approach.
"""

import math
import numpy
import scipy

from openquake import logs
from openquake.calculators.risk import general
from openquake import kvs
from openquake.db.models import Output, FragilityModel, DmgDistPerAsset
from openquake.db.models import DmgDistPerAssetData
from openquake.db.models import inputs4job
from django.contrib.gis import geos

LOGGER = logs.LOG


class ScenarioDamageRiskCalculator(general.BaseRiskCalculator):
    """Scenario Damage method for performing risk calculations."""

    def pre_execute(self):
        """
        Write the initial db container records for the calculation results.
        """

        oq_job = self.job_ctxt.oq_job

        output = Output(
            owner=oq_job.owner,
            oq_job=oq_job,
            display_name="SDA results for calculation id %s" % oq_job.id,
            db_backed=True,
            output_type="dmg_dist_per_asset")

        output.save()

        fm = _fm(oq_job)

        # temporary, will be removed
        assert fm.format == "continuous"

        dmg_states = list(fm.lss)
        dmg_states.insert(0, "no_damage")

        DmgDistPerAsset(output=output, dmg_states=dmg_states).save()

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
        """

        fm = kwargs["fmodel"]
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)
        oq_job = self.job_ctxt.oq_job

        [dds] = DmgDistPerAsset.objects.filter(
                output__owner=oq_job.owner,
                output__oq_job=oq_job,
                output__output_type="dmg_dist_per_asset")

        for site in block.sites:
            point = self.job_ctxt.region.grid.point_at(site)
            gmf = gmvs(self.job_ctxt.job_id, point)

            assets = general.BaseRiskCalculator.assets_at(
                self.job_ctxt.job_id, site)

            for asset in assets:
                funcs = fm.ffc_set.filter(taxonomy=asset.taxonomy)

                assert len(funcs) > 0, ("no limit states associated "
                        "with taxonomy %s of asset %s.") % (
                        asset.taxonomy, asset.asset_ref)

                # we always have a number of damage states
                # which is len(limit states) + 1
                sum_ds = numpy.zeros((len(gmf), len(funcs) + 1))

                for x, gmv in enumerate(gmf):
                    sum_ds[x] += compute_dm(funcs, gmv)

                nou = asset.number_of_units
                mean = numpy.mean(sum_ds, axis=0) * nou
                stddev = numpy.std(sum_ds, axis=0, ddof=1) * nou

                for x in xrange(len(mean)):
                    ds = fm.lss[x - 1]

                    if x == 0:
                        ds = "no_damage"

                    DmgDistPerAssetData(dmg_dist_per_asset=dds,
                            exposure_data=asset, dmg_state=ds,
                            mean=mean[x], stddev=stddev[x],
                            location=geos.GEOSGeometry(
                            site.point.to_wkt())).save()

    def post_execute(self):
        """
        Export the results to file if the `output-type`
        parameter is set to `xml`.
        """
        pass


def compute_dm(funcs, gmv):

    def compute_poe(iml, mean, stddev):
        variance = stddev ** 2.0
        sigma = math.sqrt(math.log((variance / mean ** 2.0) + 1.0))
        mu = math.exp(math.log(mean ** 2.0 / math.sqrt(
                variance + mean ** 2.0)))

        return scipy.stats.lognorm.cdf(iml, sigma, scale=mu)

    # we always have a number of damage states
    # which is len(limit states) + 1
    damage_states = numpy.zeros(len(funcs) + 1)

    first_poe = compute_poe(gmv, funcs[0].mean, funcs[0].stddev)

    # first damage state is always 1 - the probability
    # of exceedance of first limit state
    damage_states[0] = 1 - first_poe

    last_poe = first_poe

    # starting from one, the first damage state
    # is already computed...
    for x in xrange(1, len(funcs)):
        poe = compute_poe(gmv, funcs[x].mean, funcs[x].stddev)
        damage_states[x] = last_poe - poe
        last_poe = poe

    # last damage state is equal to the probabily
    # of exceedance of the last limit state
    damage_states[len(funcs)] = compute_poe(
        gmv, funcs[len(funcs) - 1].mean,
        funcs[len(funcs) - 1].stddev)

    return numpy.array(damage_states)


def _fm(oq_job):
    [ism] = inputs4job(oq_job.id, input_type="fragility")
    [fm] = FragilityModel.objects.filter(input=ism, owner=oq_job.owner)

    return fm


def gmvs(job_id, point):
    key = kvs.tokens.ground_motion_values_key(job_id, point)
    return [float(x["mag"]) for x in kvs.get_list_json_decoded(key)]
