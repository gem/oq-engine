# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani, D. Monelli
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is free software: you can
# redistribute
# it and/or modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein is
# released as a prototype implementation on behalf of scientists and engineers
# working within the GEM Foundation (Global Earthquake Model).
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
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# The GEM Foundation, and the authors of the software, assume no liability for
# use of the software.

"""
Module :mod:`openquake.hmtk.seismicity.max_magnitude.kijko_sellevol` defines
the Kijko & Sellevol algorithm for maximum magnitude
"""

import warnings
import numpy as np
from math import fabs
from scipy.integrate import quad
from openquake.hmtk.seismicity.max_magnitude.base import (
    BaseMaximumMagnitude,
    MAX_MAGNITUDE_METHODS,
    _get_observed_mmax,
    _get_magnitude_vector_properties,
)


def check_config(config, data):
    """Checks that the config file contains all required parameters

    :param dict config:
        Configuration file

    :returns:
        Configuration file with all correct parameters
    """
    if "tolerance" not in config.keys() or not config["tolerance"]:
        config["tolerance"] = 1e-5

    if not config.get("maximum_iterations", None):
        config["maximum_iterations"] = 1000

    mmin_obs = np.min(data["magnitude"])
    if config.get("input_mmin", 0) < mmin_obs:
        config["input_mmin"] = mmin_obs

    if fabs(config["b-value"]) < 1e-7:
        config["b-value"] = 1e-7

    return config


@MAX_MAGNITUDE_METHODS.add(
    "get_mmax",
    **{
        "input_mmin": lambda cat: np.min(cat.data["magnitude"]),
        "input_mmax": lambda cat: cat.data["magnitude"][
            np.argmax(cat.data["magnitude"])
        ],
        "input_mmax_uncertainty": lambda cat: cat.get_observed_mmax_sigma(0.2),
        "b-value": 1e-7,
        "maximum_iterations": 1000,
        "tolerance": 1e-5,
    },
)
class KijkoSellevolFixedb(BaseMaximumMagnitude):
    """
    Implements Kijko and Sellevol estimator for maximim magnitude assuming
    a fixed b-value. Coded from description in Kijko (2004):

    Kijko, A. (2004), ..., Pure & Applied Geophysics,
    """

    def get_mmax(self, catalogue, config):
        """
        Calculates Maximum magnitude

        :param catalogue:
            Earthquake catalogue as instance of :class:
            openquake.hmtk.seismicity.catalogue.Catalogue

        :param dict config:
            Configuration file for algorithm, contains the attributes:
            * 'b-value': b-value (positive float)
            * 'input_mmin': Minimum magnitude for integral (if less than
            minimum observed magnitude, will be overwritten by
            minimum observed magnitude)
            * 'tolerance': Tolerance of stabilising of iterator
            * 'maximum_interations': Maximum number of iterations

        :returns: **mmax** Maximum magnitude and **mmax_sig** corresponding
                    uncertainty
        """
        config = check_config(config, catalogue.data)

        obsmax, obsmaxsig = _get_observed_mmax(catalogue.data, config)

        mmin = config["input_mmin"]
        beta = config["b-value"] * np.log(10.0)

        neq, mmin = _get_magnitude_vector_properties(catalogue.data, config)

        mmax = np.copy(obsmax)
        d_t = np.inf
        iterator = 0
        print(mmin, mmax, neq, beta)
        while d_t > config["tolerance"]:
            delta = quad(
                self._ks_intfunc, mmin, mmax, args=(neq, mmax, mmin, beta)
            )[0]
            tmmax = obsmax + delta
            d_t = np.abs(tmmax - mmax)
            mmax = np.copy(tmmax)
            iterator += 1
            if iterator > config["maximum_iterations"]:
                print(
                    "Kijko-Sellevol estimator reached "
                    "maximum # of iterations"
                )
                d_t = -np.inf
        return mmax.item(), np.sqrt(obsmaxsig**2.0 + delta**2.0)

    def _ks_intfunc(self, mval, neq, mmax, mmin, beta):
        """Integral function inside Kijko-Sellevol estimator
        (Eq. 6 in Kijko, 2004)

        :param float mval:
            Magnitude value
        :param float neq:
            Number of earthquakes
        :param float mmax:
            Maximum Magnitude
        :param float mmin:
            Minimum Magnitude
        :param float beta:
            Beta-value of the distribution
        :returns:
            Integrand of Kijko-Sellevol estimator
        """
        if mmin >= mmax:
            raise ValueError(
                "Maximum magnitude smaller than minimum magnitude"
                " in Kijko & Sellevol (Fixed-b) integral"
            )

        func1 = 1.0 - np.exp(-beta * (mval - mmin))
        if np.fabs(beta) > 1e-3:
            func1 = (func1 / (1.0 - np.exp(-beta * (mmax - mmin)))) ** neq
        else:
            warnings.warn("beta is lower or equal to 0", RuntimeWarning)
        return func1
