# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani, D. Monelli
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is free software: you can
# redistribute it and/or modify it under the terms of the GNU Affero General
# Public License  as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided
# herein is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the hope that
# it will be useful to the scientific, engineering, disaster risk and software
# design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software developers,
# as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be directed to
# the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# The GEM Foundation, and the authors of the software, assume no liability for
# use of the software.

"""
Module
:mod:`openquake.hmtk.seismicity.max_magnitude.kijko_nonparametric_gaussian`
implements the Non-Parametric Gaussian estimator of maximum magnitude
proposed by Kijko (2004)
"""
import numpy as np
from scipy.stats.mstats import mquantiles
from openquake.hmtk.seismicity.max_magnitude.base import (
    BaseMaximumMagnitude,
    MAX_MAGNITUDE_METHODS,
)


def check_config(config):
    """Check config file inputs and overwrite bad values with the defaults"""
    essential_keys = ["number_earthquakes"]

    for key in essential_keys:
        if key not in config:
            raise ValueError(
                "For Kijko Nonparametric Gaussian the key %s "
                "needs to be set in the configuation" % key
            )

    if config.get("tolerance", 0.0) <= 0.0:
        config["tolerance"] = 0.05

    if config.get("maximum_iterations", 0) < 1:
        config["maximum_iterations"] = 100

    if config.get("number_samples", 0) < 2:
        config["number_samples"] = 51

    return config


def _get_exponential_spaced_values(mmin, mmax, number_samples):
    """
    Function to return a set of exponentially spaced values between mmin and
    mmax

    :param float mmin:
        Minimum value
    :param float mmax:
        Maximum value
    :param float number_samples:
        Number of exponentially spaced samples
    :return np.ndarray:
        Set of 'number_samples' exponentially spaced values
    """
    lhs = np.exp(mmin) + np.arange(0.0, number_samples - 1.0, 1.0) * (
        (np.exp(mmax) - np.exp(mmin)) / (number_samples - 1.0)
    )
    magval = np.hstack([lhs, np.exp(mmax)])

    return np.log(magval)


@MAX_MAGNITUDE_METHODS.add(
    "get_mmax",
    number_earthquakes=float,
    number_samples=51,
    maximum_iterations=100,
    tolerance=0.05,
)
class KijkoNonParametricGaussian(BaseMaximumMagnitude):
    """
    Class to implement non-parametric Gaussian methodology of Kijko (2004)
    """

    def get_mmax(self, catalogue, config):
        """
        Calculates maximum magnitude

        :param catalogue:
            Instance of :class: openquake.hmtk.seismicity.catalogue.Catalogue

        :param dict config:
            Configuration parameters - including:
            * 'number_earthquakes': Number of largest magnitudes to consider
            * 'number_samples' [optional]: Number of samples for integral {default=51}
            * 'maximum_iterations' [optional]: Maximum number of iterations {default=100}
            * 'tolerance' [optional]: Magnitude difference threshold for iterstor stability {default=0.05}

        :returns:
            Maximum magnitude and its uncertainty
        """
        config = check_config(config)

        # Unlike the exponential distributions, if the input mmax is
        # greater than the observed mmax the integral expands rapidly.
        # Therefore, only observed mmax is considered
        max_loc = np.argmax(catalogue.data["magnitude"])
        obsmax = catalogue.data["magnitude"][max_loc]
        if (
            not (isinstance(catalogue.data["sigmaMagnitude"], np.ndarray))
            or (len(catalogue.data["sigmaMagnitude"]) == 0)
            or np.all(np.isnan(catalogue.data["sigmaMagnitude"]))
        ):
            obsmaxsig = 0.0
        else:
            obsmaxsig = catalogue.data["sigmaMagnitude"][max_loc]

        # Find number_eqs largest events
        n_evts = np.shape(catalogue.data["magnitude"])[0]
        if n_evts <= config["number_earthquakes"]:
            # Catalogue smaller than number of required events
            mag = np.copy(catalogue.data["magnitude"])
            neq = float(np.shape(mag)[0])
        else:
            # Select number_eqs largest events
            mag = np.sort(catalogue.data["magnitude"], kind="quicksort")
            mag = mag[-config["number_earthquakes"] :]
            neq = float(config["number_earthquakes"])

        mmin = np.min(mag)
        # Get smoothing factor
        hfact = self.h_smooth(mag)
        mmax = np.copy(obsmax)
        d_t = mmax.item() - 0.0
        iterator = 0
        while d_t > config["tolerance"]:
            # Generate exponentially spaced samples
            magval = _get_exponential_spaced_values(
                mmin, mmax.item(), config["number_samples"]
            )

            # Evaluate integral function using Simpson's method
            delta = self._kijko_npg_intfunc_simps(
                magval, mag, mmax.item(), hfact, neq
            )
            tmmax = obsmax + delta
            d_t = np.abs(tmmax - mmax.item())
            mmax = np.copy(tmmax)
            iterator += 1
            if iterator > config["maximum_iterations"]:
                print(
                    "Kijko-Non-Parametric Gaussian estimator reached"
                    "maximum # of iterations"
                )
                d_t = -np.inf
        return mmax.item(), np.sqrt(
            obsmaxsig**2.0 + (mmax.item() - obsmax) ** 2.0
        )

    def h_smooth(self, mag):
        """
        Function to calculate smoothing coefficient (h) for Gaussian
        Kernel estimation - based on Silverman (1986) formula

        :param numpy.ndarray mag:
            Magnitude vector

        :returns:
            Smoothing coefficient (h) (float)
        """
        neq = float(len(mag))

        # Calculate inter-quartile range
        qtiles = mquantiles(mag, prob=[0.25, 0.75])
        iqr = qtiles[1] - qtiles[0]
        hfact = 0.9 * np.min([np.std(mag), iqr / 1.34]) * (neq ** (-1.0 / 5.0))
        # Round h to 2 dp
        hfact = np.round(100.0 * hfact) / 100.0
        return hfact

    def _gauss_cdf_hastings(self, xval, barx=0.0, sigx=1.0):
        """Function to implement Hasting's approximation of the normalised
        cumulative normal function - this is taken from Kijko's own code
        so I don't really know why this is here!!!!!

        :param np.ndarray xval:
            x variate
        :param float barx:
            Mean of the distribution
        :param float sigx:
            Standard Deviation
        :return float yval:
            Gaussian Cumulative Distribution
        """
        x_norm = (xval - barx) / sigx

        # Fixed distribution co-efficients
        a_1 = 0.196854
        a_2 = -0.115194
        a_3 = 0.000344
        a_4 = 0.019527
        x_a = np.abs(x_norm)
        yval = 1.0 - 0.5 * (
            1.0
            + a_1 * x_a
            + (a_2 * (x_a**2.0))
            + (a_3 * (x_a**3.0))
            + (a_4 * (x_a**4.0))
        ) ** (-4.0)

        # Finally to normalise
        yval[x_norm < 0.0] = 1.0 - yval[x_norm < 0.0]
        # To deal with precision errors for tail ends
        yval[x_norm < -5.0] = 0.0
        yval[x_norm > 5.0] = 1.0
        return yval

    def _kijko_npg_intfunc_simps(self, mval, mag, mmax, hfact, neq):
        """Integral function for non-parametric Gaussuan assuming that
        Simpson's rule has been invoked for exponentially spaced samples

        :param numpy.ndarray mval:
            Target Magnitudes
        :param numpy.ndarray mag:
            Observed Magnitude values
        :param float mmax:
            Maximum magnitude for integral
        :param float hfact:
            Smoothing coefficient (output of h_smooth)
        :param float neq:
            Number of earthquakes (effectively the length of mag)
        :return float intfunc:
            Integral of non-Parametric Gaussian function
        """
        nmval = len(mval)
        # Mmin and Mmax must be arrays to allow for indexing in
        # _gauss_cdf_hastings
        mmin = np.min(mag)

        p_min = self._gauss_cdf_hastings((mmin - mag) / hfact)
        p_max = self._gauss_cdf_hastings((mmax - mag) / hfact)

        cdf_func = np.zeros(nmval)
        for ival, target_mag in enumerate(mval):
            # Calculate normalised magnitudes
            p_mag = self._gauss_cdf_hastings((target_mag - mag) / hfact)
            cdf_func[ival] = (
                (np.sum(p_mag) - np.sum(p_min))
                / (np.sum(p_max) - np.sum(p_min))
            ) ** neq
        # Now to perform integration via mid-point rule
        intfunc = 0.5 * cdf_func[0] * (mval[1] - mval[0])
        for iloc in range(1, nmval - 1):
            intfunc = intfunc + (
                0.5 * cdf_func[iloc] * (mval[iloc + 1] - mval[iloc - 1])
            )

        intfunc = intfunc + (0.5 * cdf_func[-1] * (mval[-1] - mval[-2]))

        return intfunc
