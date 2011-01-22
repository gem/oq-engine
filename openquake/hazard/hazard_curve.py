# -*- coding: utf-8 -*-
"""
Collection of mixins that compute stuff using hazard curves as input.
"""

from numpy import array # pylint: disable=E1101, E0611
from scipy.stats.mstats import mquantiles

from openquake import kvs
from openquake import shapes


def compute_mean_curve(curves):
    """Compute a mean hazard curve.
    
    The input parameter is a list of arrays where each array
    contains just the Y values of the corresponding hazard curve.
    """
    return array(curves).mean(axis=0)


def compute_quantile_curve(curves, quantile):
    result = []
    
    if curves:
        result = mquantiles(curves, quantile, axis=0)[0]
    
    return result


def _extract_y_values_from(curve):
    """Extract from a serialized hazard curve (in json format)
    the Y values used to compute the mean hazard curve.
    
    The serialized hazard curve has this format:
    {"site_lon": 1.0, "site_lat": 1.0, "curve": [{"x": 0.1, "y": 0.2}, ...]}
    """
    y_values = []

    for point in curve:
        y_values.append(point["y"])
        
    return y_values


def _acceptable(quantile):
    try:
        quantile = float(quantile)
        return quantile >= 0.0 and quantile <= 1.0

    except ValueError:
        return False


def curves_at(job_id, site):
    pattern = "%s*%s*%s*%s" % (kvs.tokens.HAZARD_CURVE_KEY_TOKEN,
            job_id, site.longitude, site.latitude)
    
    return kvs.mget_decoded(pattern)


class MeanHazardCurveCalculator:
    """This class computes a mean hazard for each site in the region
    using as input all the pre computed curves for different realizations."""
    
    def __init__(self):
        pass
    
    def execute(self):
        """Execute the logic of this mixin."""
        for sites in self.site_list_generator(): # pylint: disable=E1101
            for site in sites:
                curves = []

                for raw_curve in curves_at(self.job_id, site):
                    curves.append(_extract_y_values_from(raw_curve["curve"]))

                self._serialize_mean_curve_for(site, curves)

    def _serialize_mean_curve_for(self, site, curves):
        """Serialize a mean hazard curve in the underlying kvs system."""

        mean_curve = {"site_lon": site.longitude, "site_lat": site.latitude,
                "curve": list(compute_mean_curve(curves))}

        kvs.set_value_json_encoded(kvs.tokens.mean_hazard_curve_key(
                # pylint: disable=E1101
                self.job_id, site), mean_curve)


class QuantileHazardCurveCalculator:

    def __init__(self):
        pass
    
    def execute(self):
        """Execute the logic of this mixin."""
        quantiles = self._extract_quantiles_from_config()

        for quantile in quantiles:
            for sites in self.site_list_generator():
                for site in sites:
                    curves = []

                    for raw_curve in curves_at(self.job_id, site):
                        curves.append(_extract_y_values_from(
                                raw_curve["curve"]))

                    self._serialize_quantile_curve_for(site, curves, quantile)

    def _serialize_quantile_curve_for(self, site, curves, quantile):
        """Serialize a quantile hazard curve in the underlying kvs system."""

        quantile_curve = {"site_lon": site.longitude, "site_lat": site.latitude,
                "curve": list(compute_quantile_curve(curves, quantile))}

        kvs.set_value_json_encoded(kvs.tokens.quantile_hazard_curve_key(
                # pylint: disable=E1101
                self.job_id, site, quantile), quantile_curve)

    def _extract_quantiles_from_config(self):
        """Extract the set of valid quantiles from the configuration file."""
        quantiles = []

        if self.has("QUANTILE_LEVELS"):
            raw_quantiles = self.params["QUANTILE_LEVELS"].split()
            quantiles = [float(x) for x in raw_quantiles if _acceptable(x)]

        return quantiles
