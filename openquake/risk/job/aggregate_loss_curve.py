# -*- coding: utf-8 -*-
"""
A mixin that is able to compute and plot an aggregate loss curve.
"""

import os

from openquake import risk
from openquake import shapes
from openquake.output import curve
from openquake.risk import probabilistic_event_based as prob


def filename(job_id):
    """Return the name of the generated file."""
    return "%s-aggregate-loss-curve.svg" % job_id

def for_plotting(curve):
    """Translate a loss curve into a dictionary compatible to
    the interface defined in CurvePlot.write."""
    data = {}

    data["AggregatedLossCurve"] = {}
    data["AggregatedLossCurve"]["abscissa"] = tuple(curve.abscissae)
    data["AggregatedLossCurve"]["ordinate"] = tuple(curve.ordinates)
    data["AggregatedLossCurve"]["abscissa_property"] = "Losses"
    data["AggregatedLossCurve"]["ordinate_property"] = "PoEs"
    data["AggregatedLossCurve"]["curve_title"] = "Aggregated Loss Curve"
    
    return data

class AggregateLossCurveMixin:
    """This class computes and plots an aggregate loss curve given a set
    of pre computed curves stored in the underlying kvs system."""
    
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
        
        # could be optimized by adding this flag in the probablistic mixin
        if not self.has("AGGREGATE_LOSS_CURVE"):
            return

        key = risk.loss_curves_key(self.id)
        curves = shapes.CurveSet.from_kvs(key)
        aggregate_loss_curve = prob.AggregateLossCurve.from_curve_set(curves)
        
        path = os.path.join(self.base_path,
                self.params["OUTPUT_DIR"], filename(self.id))

        plotter = curve.CurvePlot(path)
        plotter.write(for_plotting(aggregate_loss_curve.compute(
                self.tses(), self.time_span())), autoscale_y=False)

        plotter.close()
