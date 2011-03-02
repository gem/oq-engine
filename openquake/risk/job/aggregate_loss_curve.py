# -*- coding: utf-8 -*-
"""
Module to compute and plot an aggregate loss curve.
"""

import os

from celery.decorators import task

from openquake import job as engine
from openquake.logs import LOG
from openquake.output import curve
from openquake.risk import probabilistic_event_based as prob


def _filename(job_id):
    """Return the name of the generated file."""
    return "%s-aggregate-loss-curve.svg" % job_id


def _for_plotting(loss_curve, time_span):
    """Translate a loss curve into a dictionary compatible to
    the interface defined in CurvePlot.write."""
    data = {}

    data["AggregateLossCurve"] = {}
    data["AggregateLossCurve"]["abscissa"] = tuple(loss_curve.abscissae)
    data["AggregateLossCurve"]["ordinate"] = tuple(loss_curve.ordinates)
    data["AggregateLossCurve"]["abscissa_property"] = "Economic Losses"
    data["AggregateLossCurve"]["ordinate_property"] = \
            "PoE in %s years" % (str(time_span))

    data["AggregateLossCurve"]["curve_title"] = "Aggregate Loss Curve"

    return data


@task(is_eager=True)
def compute_aggregate_curve(job_id):
    """Compute and plot an aggreate loss curve.

    This function expects to find in kvs a set of pre computed
    GMFs and assets.

    This function is triggered only if the AGGREGATE_LOSS_CURVE
    parameter has been specified in the configuration file.
    """
    
    job = engine.Job.from_kvs(job_id)

    if not job.has("AGGREGATE_LOSS_CURVE"):
        LOG.debug("AGGREGATE_LOSS_CURVE parameter not specified, " \
                "skipping aggregate loss curve computation...")

        return

    aggregate_loss_curve = prob.AggregateLossCurve.from_kvs(job.id)

    path = os.path.join(job.params["BASE_PATH"],
            job.params["OUTPUT_DIR"], _filename(job.id))

    plotter = curve.CurvePlot(path)
    plotter.write(_for_plotting(
            aggregate_loss_curve.compute(),
            job.params["INVESTIGATION_TIME"]), autoscale_y=False)

    plotter.close()
    LOG.debug("Aggregate loss curve stored at %s" % path)
