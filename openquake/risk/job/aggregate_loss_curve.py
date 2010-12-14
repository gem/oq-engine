# -*- coding: utf-8 -*-
"""
A mixin that is able to compute and plot an aggregate loss curve.
"""

import os

from openquake.logs import LOG
from openquake.output import curve
from openquake.risk import probabilistic_event_based as prob


def filename(job_id):
    """Return the name of the generated file."""
    return "%s-aggregate-loss-curve.svg" % job_id

def for_plotting(loss_curve):
    """Translate a loss curve into a dictionary compatible to
    the interface defined in CurvePlot.write."""
    data = {}

    data["AggregateLossCurve"] = {}
    data["AggregateLossCurve"]["abscissa"] = tuple(loss_curve.abscissae)
    data["AggregateLossCurve"]["ordinate"] = tuple(loss_curve.ordinates)
    data["AggregateLossCurve"]["abscissa_property"] = "Loss"
    data["AggregateLossCurve"]["ordinate_property"] = "PoE"
    data["AggregateLossCurve"]["curve_title"] = "Aggregate Loss Curve"
    
    return data

class AggregateLossCurveMixin:
    """This class computes and plots an aggregate loss curve given a set
    of pre computed curves stored in the underlying kvs system."""
    
    def __init__(self):
        pass
    
    def tses(self):
        """Return the tses parameter, using the mixed config file."""
        histories = int(self.params["NUMBER_OF_SEISMICITY_HISTORIES"])
        realizations = int(self.params["NUMBER_OF_HAZARD_CURVE_CALCULATIONS"])
        
        num_ses = histories * realizations
        return num_ses * self.time_span()

    def time_span(self):
        """Return the time span parameter, using the mixed config file."""
        return float(self.params["INVESTIGATION_TIME"])

    def execute(self):
        """Execute the logic of this mixin."""

        if not self.has("AGGREGATE_LOSS_CURVE"):
            LOG.debug("AGGREGATE_LOSS_CURVE parameter not specified, " \
                    "skipping aggregate loss curve computation...")

            return []

        aggregate_loss_curve = prob.AggregateLossCurve.from_kvs(self.id)
        
        path = os.path.join(self.base_path,
                self.params["OUTPUT_DIR"], filename(self.id))

        plotter = curve.CurvePlot(path)
        plotter.write(for_plotting(aggregate_loss_curve.compute(
                self.tses(), self.time_span())), autoscale_y=False)

        plotter.close()
        LOG.debug("Aggregate loss curve stored at %s" % path)

        return [path] # why?
