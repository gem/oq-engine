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

import json
from openquake import job
from celery.exceptions import TimeoutError

from openquake.parser import vulnerability
from openquake.shapes import Curve
from openquake.risk import job as risk_job
from openquake.risk import classical_psha_based as cpsha_based
from openquake.risk.common import  compute_loss_curve
from openquake import kvs
from openquake import logs
from openquake.risk.job import preload, output, RiskJobMixin
from math import exp
LOGGER = logs.LOG


class ClassicalPSHABasedMixin:
    """Mixin for Classical PSHA Based Risk Job"""

    @preload
    @output
    def execute(self):
        """ execute -- general mixin entry point """
        celery_tasks = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))
            celery_tasks.append(risk_job.compute_risk.delay(self.id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # kvs).
        for task in celery_tasks:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait(timeout=None)
            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return []
        return True

    def compute_risk(self, block_id, **kwargs):  # pylint: disable=W0613
        """This task computes risk for a block of sites. It requires to have
        pre-initialized in kvs:
         1) list of sites
         2) exposure portfolio (=assets)
         3) vulnerability

        """

        block = job.Block.from_kvs(block_id)

        #pylint: disable=W0201
        self.vuln_curves = \
                vulnerability.load_vuln_model_from_kvs(self.job_id)

        for point in block.grid(self.region):
            curve_token = kvs.tokens.mean_hazard_curve_key(self.job_id,
                                point.site)

            decoded_curve = kvs.get_value_json_decoded(curve_token)

            hazard_curve = Curve([(exp(float(el['x'])), el['y'])
                            for el in decoded_curve['curve']])

            asset_key = kvs.tokens.asset_key(self.id,
                            point.row, point.column)
            assets = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.JSONDecoder().decode(x) for x in assets]:
                LOGGER.debug("processing asset %s" % (asset))
                loss_ratio_curve = self.compute_loss_ratio_curve(
                    point, asset, hazard_curve)

                self.compute_loss_curve(point, loss_ratio_curve, asset)

        return True

    def compute_loss_curve(self, point, loss_ratio_curve, asset):
        """
        Computes the loss ratio and store it in kvs to provide
        data to the @output decorator which does the serialization
        in the RiskJobMixin, more details inside
        openquake.risk.job.RiskJobMixin -- for details see
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

    def compute_loss_ratio_curve(self, point, asset, hazard_curve):
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

        vuln_function_reference = asset["vulnerabilityFunctionReference"]
        vuln_function = self.vuln_curves.get(
            vuln_function_reference, None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["vulnerabilityFunctionReference"],
                asset["assetID"]))

            return None

        loss_ratio_curve = cpsha_based.compute_loss_ratio_curve(
            vuln_function, hazard_curve)

        loss_ratio_key = kvs.tokens.loss_ratio_key(
            self.job_id, point.row, point.column, asset['assetID'])

        kvs.set(loss_ratio_key, loss_ratio_curve.to_json())

        return loss_ratio_curve

RiskJobMixin.register("Classical PSHA", ClassicalPSHABasedMixin)
