# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


# pylint: disable=W0232

""" Mixin for Classical PSHA Risk Calculation """

import geohash

from celery.exceptions import TimeoutError

from openquake import kvs
from openquake import logs

from openquake.db import models

from openquake.parser import vulnerability
from openquake.risk import classical_psha_based as cpsha_based
from openquake.shapes import Curve
from openquake.job import config as job_config

from openquake.risk.common import compute_loss_curve
from openquake.risk.job import general

LOGGER = logs.LOG


class ClassicalPSHABasedMixin:
    """Mixin for Classical PSHA Based Risk Job"""

    def execute(self):
        """ execute -- general mixin entry point """
        general.preload(self)

        celery_tasks = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))
            celery_tasks.append(
                general.compute_risk.delay(self.job_id, block_id))

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

        general.write_output(self)

    def _get_db_curve(self, site):
        """Read hazard curve data from the DB"""
        gh = geohash.encode(site.latitude, site.longitude, precision=12)
        job = models.OqCalculation.objects.get(id=self.job_id)
        hc = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_calculation=job,
            hazard_curve__statistic_type='mean').extra(
            where=["ST_GeoHash(location, 12) = %s"], params=[gh]).get()

        return Curve(zip(job.oq_params.imls, hc.poes))

    def compute_risk(self, block_id):
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in kvs:
         1) list of sites
         2) exposure portfolio (=assets)
         3) vulnerability
         4) vulnerability for retrofitted asset portfolio (only for BCR mode)

        Calls either :meth:`_compute_bcr` or :meth:`_compute_loss` depending
        on the calculation mode.
        """

        if self.params[job_config.CALCULATION_MODE] \
                == job_config.BCR_CLASSICAL_MODE:
            return self._compute_bcr(block_id)
        else:
            return self._compute_loss(block_id)

    def _compute_loss(self, block_id):
        """
        Calculate and store in the kvs the loss data.
        """
        block = general.Block.from_kvs(block_id)

        vuln_curves = vulnerability.load_vuln_model_from_kvs(self.job_id)

        for point in block.grid(self.region):
            hazard_curve = self._get_db_curve(point.site)

            asset_key = kvs.tokens.asset_key(self.job_id,
                            point.row, point.column)
            for asset in kvs.get_list_json_decoded(asset_key):
                LOGGER.debug("processing asset %s" % (asset))

                loss_ratio_curve = self.compute_loss_ratio_curve(
                    point, asset, hazard_curve, vuln_curves)

                if loss_ratio_curve:
                    loss_curve = self.compute_loss_curve(point,
                            loss_ratio_curve, asset)

                    for loss_poe in general.conditional_loss_poes(self.params):
                        general.compute_conditional_loss(self.job_id,
                                point.column, point.row, loss_curve, asset,
                                loss_poe)

        return True

    def _compute_bcr(self, block_id):
        """
        Calculate and store in the kvs the benefit-cost ratio data for block.

        A value is stored with key :func:`openquake.kvs.tokens.bcr_block_key`.
        See :func:`openquake.risk.general.compute_bcr_for_block` for return
        value spec.
        """
        result = []

        points = list(general.Block.from_kvs(block_id).grid(self.region))
        hazard_curves = dict((point.site, self._get_db_curve(point.site))
                             for point in points)

        def get_loss_curve(point, vuln_function, asset):
            "Compute loss curve basing on hazard curve"
            hazard_curve = hazard_curves[point.site]
            loss_ratio_curve = cpsha_based.compute_loss_ratio_curve(
                    vuln_function, hazard_curve)
            return compute_loss_curve(loss_ratio_curve, asset['assetValue'])

        result = general.compute_bcr_for_block(self.job_id, points,
            get_loss_curve, float(self.params['INTEREST_RATE']),
            float(self.params['ASSET_LIFE_EXPECTANCY'])
        )
        bcr_block_key = kvs.tokens.bcr_block_key(self.job_id, block_id)
        kvs.set_value_json_encoded(bcr_block_key, result)
        LOGGER.debug('bcr result for block %s: %r', block_id, result)
        return True

    def compute_loss_curve(self, point, loss_ratio_curve, asset):
        """
        Computes the loss ratio and store it in kvs to provide
        data to the @output decorator which does the serialization
        in the RiskJobMixin, more details inside
        openquake.risk.job.general.RiskJobMixin -- for details see
        RiskJobMixin._write_output_for_block and the output decorator

        :param point: the point of the grid we want to compute
        :type point: :py:class:`openquake.shapes.GridPoint`
        :param loss_ratio_curve: the loss ratio curve
        :type loss_ratio_curve: :py:class `openquake.shapes.Curve`
        :param asset: the asset for which to compute the loss curve
        :type asset: :py:class:`dict` as provided by
               :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
        """

        loss_curve = compute_loss_curve(loss_ratio_curve, asset['assetValue'])
        loss_key = kvs.tokens.loss_curve_key(self.job_id, point.row,
            point.column, asset['assetID'])

        kvs.set(loss_key, loss_curve.to_json())

        return loss_curve

    def compute_loss_ratio_curve(self, point, asset,
                                 hazard_curve, vuln_curves):
        """ Computes the loss ratio curve and stores in kvs
            the curve itself

        :param point: the point of the grid we want to compute
        :type point: :py:class:`openquake.shapes.GridPoint`
        :param asset: the asset used to compute the loss curve
        :type asset: :py:class:`dict` as provided by
            :py:class:`openquake.parser.exposure.ExposurePortfolioFile`
        :param hazard_curve: the hazard curve used to compute the
            loss ratio curve
        :type hazard_curve: :py:class:`openquake.shapes.Curve`
        """

        # we get the vulnerability function related to the asset

        vuln_function_reference = asset["taxonomy"]
        vuln_function = vuln_curves.get(vuln_function_reference, None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["taxonomy"],
                asset["assetID"]))

            return None

        loss_ratio_curve = cpsha_based.compute_loss_ratio_curve(
            vuln_function, hazard_curve)

        loss_ratio_key = kvs.tokens.loss_ratio_key(
            self.job_id, point.row, point.column, asset['assetID'])

        kvs.set(loss_ratio_key, loss_ratio_curve.to_json())

        return loss_ratio_curve

general.RiskJobMixin.register("Classical", ClassicalPSHABasedMixin)
general.RiskJobMixin.register("Classical BCR", ClassicalPSHABasedMixin)
