# pylint: disable=W0232
""" Mixin for Classical PSHA Risk Calculation """

import json
from openquake import job
from celery.exceptions import TimeoutError

from openquake.parser import vulnerability
from openquake.shapes import Curve
from openquake.risk import job as risk_job
from openquake.risk import classical_psha_based as cpsha_based
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

        tasks = []
        results = []
        for block_id in self.blocks_keys:
            LOGGER.debug("starting task block, block_id = %s of %s"
                        % (block_id, len(self.blocks_keys)))
            tasks.append(risk_job.compute_risk.delay(self.id, block_id))

        # task compute_risk has return value 'True' (writes its results to
        # kvs).
        for task in tasks:
            try:
                # TODO(chris): Figure out where to put that timeout.
                task.wait(timeout=None)
            except TimeoutError:
                # TODO(jmc): Cancel and respawn this task
                return []
        return results

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

            asset_key = kvs.tokens.asset_key(self.id, point.row, point.column)
            asset_list = kvs.get_client().lrange(asset_key, 0, -1)
            for asset in [json.JSONDecoder().decode(x) for x in asset_list]:
                LOGGER.debug("processing asset %s" % (asset))
                self.compute_loss_ratio_curve(
                    point, asset, hazard_curve)
        return True

    def compute_loss_ratio_curve(self, point, asset, hazard_curve):
        """ Computes the loss ratio curve and stores in kvs
            the curve itself """

        # we get the vulnerability function related to the asset
        vuln_function = self.vuln_curves.get(
            asset["vulnerabilityFunctionReference"], None)

        if not vuln_function:
            LOGGER.error(
                "Unknown vulnerability function %s for asset %s"
                % (asset["vulnerabilityFunctionReference"],
                asset["assetID"]))

            return None

        loss_ratio_curve = cpsha_based.compute_loss_ratio_curve(
            vuln_function, hazard_curve)

        loss_key = kvs.tokens.loss_ratio_key(
            self.job_id, point.row, point.column, asset['assetID'])

        kvs.set(loss_key, loss_ratio_curve.to_json())

        return loss_ratio_curve

RiskJobMixin.register("Classical PSHA", ClassicalPSHABasedMixin)
