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

"""Core functionality for Classical Risk calculations."""

import geohash

from celery.exceptions import TimeoutError

from numpy import empty, linspace
from numpy import array, concatenate
from numpy import subtract, mean

from openquake import kvs
from openquake import logs
from openquake.db import models
from openquake.parser import vulnerability
from openquake.shapes import Curve
from openquake.utils.general import MemoizeMutable
from openquake.calculators.risk import general
from openquake.calculators.risk.general import collect
from openquake.calculators.risk.general import compute_conditional_loss
from openquake.calculators.risk.general import conditional_loss_poes
from openquake.calculators.risk.general import compute_loss_curve
from openquake.calculators.risk.general import loop

LOGGER = logs.LOG


def compute_loss_ratio_curve(vuln_function, hazard_curve, steps,
        distribution=None):
    """Compute a loss ratio curve for a specific hazard curve (e.g., site),
    by applying a given vulnerability function.

    A loss ratio curve is a function that has loss ratios as X values
    and PoEs (Probabilities of Exceendance) as Y values.

    This is the main (and only) public function of this module.

    :param vuln_function: the vulnerability function used
        to compute the curve.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param hazard_curve: the hazard curve used to compute the curve.
    :type hazard_curve: :py:class:`openquake.shapes.Curve`
    :param int steps:
        Number of steps between loss ratios.
    """

    lrem = _compute_lrem(vuln_function, steps, distribution)
    lrem_po = _compute_lrem_po(vuln_function, lrem, hazard_curve)
    loss_ratios = _generate_loss_ratios(vuln_function, steps)

    return Curve(zip(loss_ratios, lrem_po.sum(axis=1)))


def _compute_lrem_po(vuln_function, lrem, hazard_curve):
    """Compute the LREM * PoOs (Probability of Occurence) matrix.

    :param vuln_function: the vulnerability function used
        to compute the matrix.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    :param hazard_curve: the hazard curve used to compute the matrix.
    :type hazard_curve: :py:class:`openquake.shapes.Curve`
    :param lrem: the LREM used to compute the matrix.
    :type lrem: 2-dimensional :py:class:`numpy.ndarray`
    """

    lrem = array(lrem)
    lrem_po = empty(lrem.shape)
    imls = _compute_imls(vuln_function)

    if hazard_curve:
        pos = _convert_pes_to_pos(hazard_curve, imls)
        for idx, po in enumerate(pos):
            lrem_po[:, idx] = lrem[:, idx] * po

    return lrem_po


def _generate_loss_ratios(vuln_function, steps):
    """Generate the set of loss ratios used to compute the LREM
    (Loss Ratio Exceedance Matrix).

    :param vuln_function:
        The vulnerability function where the loss ratios are taken from.
    :type vuln_function:
        :class:`openquake.shapes.VulnerabilityFunction`
    :param int steps:
        Number of steps between loss ratios.
    """

    # we manually add 0.0 as first loss ratio and 1.0 as last loss ratio
    loss_ratios = concatenate(
        (array([0.0]), vuln_function.loss_ratios, array([1.0])))

    return _split_loss_ratios(loss_ratios, steps)


@MemoizeMutable
def _compute_lrem(vuln_function, steps, distribution='LN'):
    """Compute the LREM (Loss Ratio Exceedance Matrix).

    :param vuln_function:
        The vulnerability function used to compute the LREM.
    :type vuln_function:
        :class:`openquake.shapes.VulnerabilityFunction`
    :param int steps:
        Number of steps between loss ratios.
    :param str: The distribution type:
                'LN' LogNormal
                'BT' BetaDistribution
    """

    dist = {'LN': general.Lognorm,
            'BT': general.BetaDistribution}.get(distribution,
                        general.Lognorm)

    loss_ratios = _generate_loss_ratios(vuln_function, steps)

    # LREM has number of rows equal to the number of loss ratios
    # and number of columns equal to the number if imls
    lrem = empty((loss_ratios.size, vuln_function.imls.size), float)

    for col, _ in enumerate(vuln_function):
        for row, loss_ratio in enumerate(loss_ratios):
            lrem[row][col] = dist.survival_function(loss_ratio,
                col=col, vf=vuln_function)

    return lrem


def _split_loss_ratios(loss_ratios, steps):
    """Split the loss ratios, producing a new set of loss ratios.

    :param loss_ratios: the loss ratios to be splitted.
    :type loss_ratios: list
    :param steps: the number of steps we make to go from one loss
        ratio to the next. For example, if we have [1.0, 2.0]:

        steps = 1 produces [1.0, 2.0]
        steps = 2 produces [1.0, 1.5, 2.0]
        steps = 3 produces [1.0, 1.33, 1.66, 2.0]
    :type steps: integer
    """
    splitted_ratios = set()

    for interval in loop(array(loss_ratios), linspace, steps + 1):
        splitted_ratios.update(interval)

    return array(sorted(splitted_ratios))


def _compute_imls(vuln_function):
    """Compute the mean IMLs (Intensity Measure Level)
    for the given vulnerability function.

    :param vuln_function: the vulnerability function where
        the IMLs (Intensity Measure Level) are taken from.
    :type vuln_function: :py:class:`openquake.shapes.VulnerabilityFunction`
    """

    imls = vuln_function.imls

    # "special" cases for lowest part and highest part of the curve
    lowest_iml_value = imls[0] - ((imls[1] - imls[0]) / 2)

    # if the calculated lowest_curve_value goes < 0 we have to force the 0
    # IMLs have to be >= 0
    if lowest_iml_value < 0:
        lowest_iml_value = 0

    highest_iml_value = imls[-1] + ((imls[-1] - imls[-2]) / 2)
    between_iml_values = collect(loop(imls, lambda x, y: mean([x, y])))

    return [lowest_iml_value] + between_iml_values + [highest_iml_value]


def _compute_pes_from_imls(hazard_curve, imls):
    """Return the PoEs (Probability of Exceendance) defined in the
    given hazard curve for each IML (Intensity Measure Level) passed.

    :param hazard_curve: the hazard curve used to extract the PoEs.
    :type hazard_curve: :py:class:`openquake.shapes.Curve`
    :param imls: the IMLs (Intensity Measure Level) of the
        vulnerability function used to interpolate the hazard curve.
    :type imls: :py:class:`list`
    """

    return hazard_curve.ordinate_for(imls)


def _convert_pes_to_pos(hazard_curve, imls):
    """For each IML (Intensity Measure Level) compute the
    PoOs (Probability of Occurence) from the PoEs
    (Probability of Exceendance) defined in the given hazard curve.

    :param hazard_curve: the hazard curve used to compute the PoOs.
    :type hazard_curve: :py:class:`openquake.shapes.Curve`
    :param imls: the IMLs (Intensity Measure Level) of the
        vulnerability function used to interpolate the hazard curve.
    :type imls: :py:class:`list`
    """

    return collect(loop(_compute_pes_from_imls(hazard_curve, imls),
            lambda x, y: subtract(array(x), array(y))))


class ClassicalRiskCalculator(general.ProbabilisticRiskCalculator):
    """Calculator for Classical Risk computations."""

    def execute(self):
        """Core Classical Risk calculation starts here."""
        celery_tasks = []
        for block_id in self.job_ctxt.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.job_ctxt.blocks_keys)))
            celery_tasks.append(
                general.compute_risk.delay(self.job_ctxt.job_id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # kvs).
        for task in celery_tasks:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait()
                if not task.successful():
                    raise Exception(task.result)

            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return

        if self.is_benefit_cost_ratio_mode():
            self.write_output_bcr()
        else:
            self.write_output()

    def _get_db_curve(self, site):
        """Read hazard curve data from the DB"""
        gh = geohash.encode(site.latitude, site.longitude, precision=12)
        job = models.OqJob.objects.get(id=self.job_ctxt.job_id)
        hc = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job,
            hazard_curve__statistic_type='mean').extra(
            where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

        return Curve(zip(job.profile().imls, hc.poes))

    def _compute_loss(self, block_id):
        """
        Calculate and store in the kvs the loss data.
        """
        block = general.Block.from_kvs(self.job_ctxt.job_id, block_id)

        vuln_curves = vulnerability.load_vuln_model_from_kvs(
            self.job_ctxt.job_id)

        for point in block.grid(self.job_ctxt.region):
            hazard_curve = self._get_db_curve(point.site)

            assets = self.assets_for_cell(self.job_ctxt.job_id, point.site)
            for asset in assets:
                LOGGER.debug("processing asset %s" % asset)

                loss_ratio_curve = self.compute_loss_ratio_curve(
                    point, asset, hazard_curve, vuln_curves)

                if loss_ratio_curve:
                    loss_curve = self.compute_loss_curve(
                        point, loss_ratio_curve, asset)

                    for poe in conditional_loss_poes(self.job_ctxt.params):
                        compute_conditional_loss(
                            self.job_ctxt.job_id, point.column,
                            point.row, loss_curve, asset, poe)

        return True

    def _compute_bcr(self, block_id):
        """
        Calculate and store in the kvs the benefit-cost ratio data for block.

        A value is stored with key :func:`openquake.kvs.tokens.bcr_block_key`.
        See :func:`openquake.risk.job.general.compute_bcr_for_block` for result
        data structure spec.
        """
        job_ctxt = self.job_ctxt
        points = list(general.Block.from_kvs(
            job_ctxt.job_id, block_id).grid(job_ctxt.region))
        hazard_curves = dict((point.site, self._get_db_curve(point.site))
                             for point in points)

        def get_loss_curve(point, vuln_function, asset):
            "Compute loss curve basing on hazard curve"
            job_profile = self.job_ctxt.oq_job_profile
            hazard_curve = hazard_curves[point.site]
            loss_ratio_curve = compute_loss_ratio_curve(
                    vuln_function, hazard_curve,
                    job_profile.lrem_steps_per_interval)
            return compute_loss_curve(loss_ratio_curve, asset.value)

        bcr = general.compute_bcr_for_block(job_ctxt.job_id, points,
            get_loss_curve, float(job_ctxt.params['INTEREST_RATE']),
            float(job_ctxt.params['ASSET_LIFE_EXPECTANCY'])
        )
        bcr_block_key = kvs.tokens.bcr_block_key(job_ctxt.job_id, block_id)
        kvs.set_value_json_encoded(bcr_block_key, bcr)
        LOGGER.debug('bcr result for block %s: %r', block_id, bcr)
        return True

    def compute_loss_curve(self, point, loss_ratio_curve, asset):
        """
        Computes the loss ratio and store it in kvs to provide
        data to the @output decorator which does the serialization.

        :param point: the point of the grid we want to compute
        :type point: :py:class:`openquake.shapes.GridPoint`
        :param loss_ratio_curve: the loss ratio curve
        :type loss_ratio_curve: :py:class `openquake.shapes.Curve`
        :param asset: the asset for which to compute the loss curve
        :type asset: :py:class:`dict` as provided by
               :py:class:`openquake.parser.exposure.ExposureModelFile`
        """

        loss_curve = compute_loss_curve(loss_ratio_curve, asset.value)
        loss_key = kvs.tokens.loss_curve_key(
            self.job_ctxt.job_id, point.row, point.column, asset.asset_ref)

        kvs.get_client().set(loss_key, loss_curve.to_json())

        return loss_curve

    def compute_loss_ratio_curve(self, point, asset,
                                 hazard_curve, vuln_curves):
        """ Computes the loss ratio curve and stores in kvs
            the curve itself

        :param point: the point of the grid we want to compute
        :type point: :py:class:`openquake.shapes.GridPoint`
        :param asset: the asset used to compute the loss curve
        :type asset: :py:class:`dict` as provided by
            :py:class:`openquake.parser.exposure.ExposureModelFile`
        :param hazard_curve: the hazard curve used to compute the
            loss ratio curve
        :type hazard_curve: :py:class:`openquake.shapes.Curve`
        """

        # we get the vulnerability function related to the asset

        vuln_function_reference = asset.taxonomy
        vuln_function = vuln_curves.get(vuln_function_reference, None)

        if not vuln_function:
            LOGGER.error("Unknown vulnerability function %s for asset %s"
                         % (asset.taxonomy, asset.asset_ref))

            return None

        lrem_steps = self.job_ctxt.oq_job_profile.lrem_steps_per_interval
        loss_ratio_curve = compute_loss_ratio_curve(
            vuln_function, hazard_curve, lrem_steps,
            self.job_ctxt.params.get("probabilisticDistribution"))

        loss_ratio_key = kvs.tokens.loss_ratio_key(
            self.job_ctxt.job_id, point.row, point.column, asset.asset_ref)

        kvs.get_client().set(loss_ratio_key, loss_ratio_curve.to_json())

        return loss_ratio_curve
