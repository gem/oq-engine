# -*- coding: utf-8 -*-

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

"""
Module to compute and plot an aggregate loss curve.
"""

import os

from openquake.logs import LOG
from openquake.output import curve
from openquake.risk.job import general
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


def compute_aggregate_curve(job):
    """Compute and plot an aggreate loss curve.

    This function expects to find in kvs a set of pre computed
    GMFs and assets.

    This function is triggered only if the AGGREGATE_LOSS_CURVE
    parameter is specified in the configuration file.

    :param job: the job the engine is currently processing.
    :type job: openquake.risk.job.probabilistic.ProbabilisticEventMixin
    """
    if not job.has("AGGREGATE_LOSS_CURVE"):
        LOG.debug("AGGREGATE_LOSS_CURVE parameter not specified, " \
                "skipping aggregate loss curve computation...")

        return

    epsilon_provider = general.EpsilonProvider(job.params)
    aggregate_loss_curve = \
        prob.AggregateLossCurve.from_kvs(job.job_id, epsilon_provider)

    path = os.path.join(job.params["BASE_PATH"],
            job.params["OUTPUT_DIR"], _filename(job.job_id))

    plotter = curve.CurvePlot(path)
    plotter.write(_for_plotting(
            aggregate_loss_curve.compute(),
            job.params["INVESTIGATION_TIME"]), autoscale_y=False)

    plotter.close()
    LOG.debug("Aggregate loss curve stored at %s" % path)
