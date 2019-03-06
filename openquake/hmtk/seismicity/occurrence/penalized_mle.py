# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2015-2019 GEM Foundation, G. Weatherill, M. Pagani
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

import numpy as np
from openquake.hmtk.seismicity.occurrence.base import (
    SeismicityOccurrence, OCCURRENCE_METHODS)


@OCCURRENCE_METHODS.add(
    'calculate',
    completeness=True,
    reference_magnitude=0.0,
    mmax=None,
    b_prior=1.0,
    b_prior_weight=1.0,
    area=0.0,
    a_prior_weight=1.0)
class PenalizedMLE(SeismicityOccurrence):
    """
    Test Implementation of the Penalized Maximum Likelihood function
    """
    IERR = {1: "No events in catalogue - returning prior",
            2: "Failure of convergence - returning prior"}

    def _null_outcome(self, config, ierr):
        """
        Method to handle failures and return information on their causes
        :param dict config:
            Configuration of method
        :param int ierr:
            Error code
        """
        print(self.IERR[ierr])
        a_4 = 0.05 * config["area"]
        return config["b_prior"], 0.0, (
            10.0 ** (np.log10(a_4) + (4. - config["reference_magnitude"])
                     * config["b_prior"]), 0.0)

    def calculate(self, catalogue, config, completeness):
        """
        Calculates the b-value and rates (and their corresponding standard
        deviations) using the Penalized MLE approach

        :param dict config:
            Configuration parameters
        :param catalogue:
            Earthquake catalogue as instance of :class:
            openquake.hmtk.seismicity.catalogue.Catalogue
        :param completeness:
            Completeness table
        :returns:
            b-value, standard deviation on b, rate (or a-value), standard
            deviation on a
        """
        # Setup
        if config["b_prior"]:
            betap = config["b_prior"] * np.log(10.)
            beta = np.copy(betap)
            has_prior = True
            wbu = config["b_prior_weight"] / np.log(10.)
            wau = config["a_prior_weight"]
            if config["a_prior_weight"]:
                apu = config["a_prior_weight"]
            else:
                apu = 1.0
        else:
            # No prior assumed. Take initial b-value of 1.0 for beta
            betap = 0.0
            beta = np.log(10.)
            wbu = 1.0E-5
            wau = 0.0
            apu = 1.0
            has_prior = False
        # Get the counts of earthquakes in their completeness windows
        delta, kval, tval, lamda, cum_rate, cum_count, nmx, nmt =\
            self._get_rate_counts(catalogue, config, completeness)
        n_val = np.sum(kval)
        if not n_val:
            return self._null_outcome(config, 1)
        assert n_val == cum_count[0]
        # Get the penalized MLE value (also returns correlation coefficient
        # rho - but not used!)
        bval, sigmab, rate, sigma_rate, rho = self._run_penalized_mle(
            config, delta, kval, tval, cum_count, betap, beta, wbu, wau)
        aval = np.log10(rate) + bval * completeness[0, 1]
        if "reference_magnitude" in config.keys() and\
                config["reference_magnitude"]:
            dm = config["reference_magnitude"] - completeness[0, 1]
            rate = 10.0 ** (np.log10(rate) - bval * dm)
            sigma_rate = 10.0 ** (np.log10(rate + sigma_rate) - bval * dm) -\
                rate
        else:
            dm = -completeness[0, 1]
            rate = np.log10(rate) - bval * dm
            sigma_rate = np.log10(rate + sigma_rate) - np.log10(rate)
            rate = np.log10(rate)
        return bval, sigmab, rate, sigma_rate

    def _run_penalized_mle(self, config, delta, kval, tval, cum_count,
                           betap, beta, wbu, wau):
        """
        Implements the core of the penalised maximum likelihood method for
        the b-value
        """
        nrloop = 0
        while nrloop <= 10:
            e_b = np.exp(beta * delta)
            deb = e_b[:-1] - e_b[1:]
            skmeb = np.sum(kval * ((delta[:-1] * e_b[:-1]) -
                                   (delta[1:] * e_b[1:])) / deb)
            skm2eb = np.sum(kval * (
                ((((delta[:-1] ** 2.) * e_b[:-1]) -
                  ((delta[1:] ** 2.) * e_b[1:])) / deb) -
                (((delta[:-1] * e_b[:-1]) - (delta[1:] * e_b[1:])) / deb)
                ** 2.))
            sateb = np.sum(config["area"] * tval * deb)
            satmeb = np.sum(config["area"] * tval *
                            ((delta[:-1] * e_b[:-1]) - (delta[1:] * e_b[1:])))
            satm2eb = np.sum(config["area"] * tval *
                             (((delta[:-1] ** 2.) * e_b[:-1]) -
                              ((delta[1:] ** 2.) * e_b[1:])))
            dldb = skmeb - cum_count[0] * (satmeb / sateb) -\
                (wbu * (beta - betap))
            d2ldb2 = skm2eb - cum_count[0] * (satm2eb / sateb -
                                              (satmeb / sateb) ** 2.) - wbu
            beta0 = np.copy(beta)
            am0 = cum_count[0] * (1.0 - e_b[-1]) / sateb
            if cum_count[1]:
                # More than one interval
                beta -= (dldb / d2ldb2)
                if beta < 0.0:
                    if nrloop > 10:
                        # Total failure of convergence - return prior
                        return self._null_outcome(config, 2)
                    nrloop += 1
                    beta = np.log(10.) / (1.0 + float(nrloop))
                    continue
                if np.abs(beta - beta0) < 1.0E-5:
                    break
            else:
                break
        bval = beta / np.log(10.0)
        v11 = (cum_count[0] / ((am0 * config["area"]) ** 2.)) + (wau / am0)
        v22 = -d2ldb2 * (np.log(10.) ** 2.)
        v12 = np.log(10.) * ((satmeb / (1.0 - e_b[-1])) +
                             delta[-1] * e_b[-1] * sateb / ((1.0 - e_b[-1]) ** 2.)) /\
            config["area"]
        vmat = np.matrix([[v11, v12], [v12, v22]])
        error_mat = np.linalg.inv(vmat)
        sigmab = np.sqrt(error_mat[1, 1])
        sigma_rate = np.sqrt(error_mat[0, 0])
        rho = error_mat[0, 1] / np.sqrt(error_mat[0, 0] * error_mat[1, 1])
        return bval, sigmab, am0 * config["area"], sigma_rate, rho

    def _get_rate_counts(self, catalogue, config, completeness):
        """
        Using the earthquake catalogue and the completeness table determine
        the number of complete earthquakes in each time and magnitude bin

        :returns:
            delta: Mmin - Mi
            kval: Number of earthquakes in magnitude bin
            tval: Effective duration of completeness for magnitude bin
            lamda: Rate of earthquake in bin
            cum_count: Number of earthquakes >= Mi
            nmx: Number of magnitude bins
            nmt: number of time bins
        """
        # If the observed mmax is greater than the specified mmax then replace
        # with observed Mmax
        mmax_inp = np.max([config["mmax"],
                           np.max(catalogue.data["magnitude"])])
        # Stack a maximum magnitude on the completeness magnitudes
        if mmax_inp > np.max(completeness[:, 1]):
            cmag = np.hstack([completeness[:, 1], mmax_inp + 1.0E-10])
            high_event = True
        else:
            cmag = np.hstack([completeness[:, 1],
                              completeness[-1, 1] + 1.0E-10])
            high_event = False
        # Pre-pend the last year of the catalogue as the completeness year
        cyear = np.hstack([catalogue.end_year + 1, completeness[:, 0]])
        count_table = np.zeros([len(cmag) - 1, len(cyear) - 1])
        nmx, nmt = count_table.shape
        count_years = np.zeros_like(count_table)
        for i in range(len(cyear) - 1):
            time_idx = np.logical_and(catalogue.data["dtime"] < cyear[i],
                                      catalogue.data["dtime"] >= cyear[i + 1])
            nyrs = cyear[i] - cyear[i + 1]
            sel_mags = catalogue.data["magnitude"][time_idx]
            for j in range(i, len(cmag) - 1):
                mag_idx = np.logical_and(sel_mags >= cmag[j],
                                         sel_mags < cmag[j + 1])
                count_table[j, i] += float(np.sum(mag_idx))
                count_years[j, i] += float(nyrs)

        delta = cmag[0] - cmag
        if not high_event:
            # Remove last row
            delta = delta[:-1]
            count_table = count_table[:-1, :]
            count_years = count_years[:-1, :]
            nmx -= 1
            nmt -= 1
        kval = np.sum(count_table, axis=1)
        tval = np.sum(count_years, axis=1)
        lamda = kval / tval
        cum_rates = np.zeros_like(count_table)
        cum_count = np.zeros_like(count_table)
        # Get cumulative values
        for i in range(nmt):
            cum_rates[:, i] = np.sum(cum_rates[:, i:], axis=1)
            cum_count[:, i] = np.sum(cum_count[:, i:], axis=1)
        cum_rate = np.array([np.sum(lamda[i:]) for i in range(nmx)])
        cum_count = np.array([np.sum(kval[i:]) for i in range(nmx)])
        return delta, kval, tval, lamda, cum_rate, cum_count, nmx, nmt
