# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

import warnings
import numpy as np
from openquake.hmtk.seismicity.occurrence.base import (
    SeismicityOccurrence,
    OCCURRENCE_METHODS,
)
from openquake.hmtk.seismicity.occurrence.utils import (
    input_checks,
    get_completeness_counts,
)


@OCCURRENCE_METHODS.add(
    "calculate",
    completeness=True,
    reference_magnitude=0.0,
    magnitude_interval=0.1,
    bvalue=1.0,
    itstab=1e-5,
    maxiter=1000,
)
class Weichert(SeismicityOccurrence):
    """Class to Implement Weichert Algorithm"""

    def calculate(self, catalogue, config, completeness=None):
        """Calculates b value and rate for mag ref"""
        bval, sigma_b, rate, sigma_rate, _aval, _sigma_a = self._calculate(
            catalogue, config, completeness
        )
        return bval, sigma_b, rate, sigma_rate

    def calc(self, catalogue, config, completeness=None):
        """Calculates GR params"""
        bval, sigma_b, _rate, _sigma_rate, aval, sigma_a = self._calculate(
            catalogue, config, completeness
        )
        return bval, sigma_b, aval, sigma_a

    def _calculate(self, catalogue, config, completeness=None):
        """Calculates a, b values + rate for mag ref"""

        # Input checks
        cmag, ctime, ref_mag, _, config = input_checks(
            catalogue, config, completeness
        )
        if "dtime" not in catalogue.data.keys() or not len(
            catalogue.data["dtime"]
        ):
            catalogue.data["dtime"] = catalogue.get_decimal_time()
        if not catalogue.end_year:
            catalogue.update_end_year()
        if completeness is None:
            # start_year = float(np.min(catalogue.data["year"]))
            completeness = np.column_stack([ctime, cmag])
        # Apply Weichert preparation
        cent_mag, t_per, n_obs = get_completeness_counts(
            catalogue, completeness, config["magnitude_interval"]
        )

        # A few more Weichert checks
        key_list = config.keys()
        if ("bvalue" not in key_list) or (not config["bvalue"]):
            config["bvalue"] = 1.0
        if ("itstab" not in key_list) or (not config["itstab"]):
            config["itstab"] = 1e-5
        if ("maxiter" not in key_list) or (not config["maxiter"]):
            config["maxiter"] = 1000

        bval, sigma_b, rate, sigma_rate, fn0, stdfn0 = self.weichert_algorithm(
            t_per,
            cent_mag,
            n_obs,
            ref_mag,
            config["bvalue"],
            config["itstab"],
            config["maxiter"],
        )

        # if not config['reference_magnitude']:
        agr = np.log10(fn0)
        agr_sigma = np.log10(fn0 + stdfn0) - np.log10(fn0)

        return bval, sigma_b, rate, sigma_rate, agr, agr_sigma

    def weichert_algorithm(
        self, tper, fmag, nobs, mrate=0.0, bval=1.0, itstab=1e-5, maxiter=1000
    ):
        """
        Weichert algorithm

        :param tper: length of observation period corresponding to magnitude
        :type tper: numpy.ndarray (float)
        :param fmag: central magnitude
        :type fmag: numpy.ndarray (float)
        :param nobs: number of events in magnitude increment
        :type nobs: numpy.ndarray (int)
        :keyword mrate: reference magnitude
        :type mrate: float
        :keyword bval: initial value for b-value
        :type beta: float
        :keyword itstab: stabilisation tolerance
        :type itstab: float
        :keyword maxiter: Maximum number of iterations
        :type maxiter: Int
        :returns: b-value, sigma_b, a-value, sigma_a
        :rtype: float
        """
        beta = bval * np.log(10.0)
        d_m = fmag[1] - fmag[0]
        itbreak = 0
        snm = np.sum(nobs * fmag)
        nkount = np.sum(nobs)
        iteration = 1
        while itbreak != 1:
            beta_exp = np.exp(-beta * fmag)
            tjexp = tper * beta_exp
            tmexp = tjexp * fmag
            sumexp = np.sum(beta_exp)
            stmex = np.sum(tmexp)
            sumtex = np.sum(tjexp)
            stm2x = np.sum(fmag * tmexp)
            dldb = stmex / sumtex
            if np.isnan(stmex) or np.isnan(sumtex):
                warnings.warn("NaN occurs in Weichert iteration")
                return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan
                # raise ValueError('NaN occers in Weichert iteration')

            d2ldb2 = nkount * ((dldb**2.0) - (stm2x / sumtex))
            dldb = (dldb * nkount) - snm
            betl = np.copy(beta)
            beta = beta - (dldb / d2ldb2)
            sigbeta = np.sqrt(-1.0 / d2ldb2)

            if np.abs(beta - betl) <= itstab:
                # Iteration has reached convergence
                bval = beta / np.log(10.0)
                sigb = sigbeta / np.log(10.0)
                fngtm0 = nkount * (sumexp / sumtex)
                fn0 = fngtm0 * np.exp((beta) * (fmag[0] - (d_m / 2.0)))
                stdfn0 = fn0 / np.sqrt(nkount)
                a_m = fngtm0 * np.exp(
                    (-beta) * (mrate - (fmag[0] - (d_m / 2.0)))
                )
                siga_m = a_m / np.sqrt(nkount)
                itbreak = 1
            else:
                iteration += 1
                if iteration > maxiter:
                    warnings.warn("Maximum Number of Iterations reached")
                    return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan
        return bval, sigb, a_m, siga_m, fn0, stdfn0
