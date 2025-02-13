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
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
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
    recurrence_table,
    input_checks,
)


@OCCURRENCE_METHODS.add("calculate", completeness=True)
class AkiMaxLikelihood(SeismicityOccurrence):
    def calculate(self, catalogue, config=None, completeness=None):
        """
        Calculation of b-value and its uncertainty for a given
        catalogue, using the maximum likelihood method of Aki (1965),
        with a correction for discrete bin width (Bender, 1983).

        :param catalogue:
            See :class:`openquake.hmtk.seismicity.occurrence.base.py`
            for further explanation
        :param config:
            The configuration in this case do not contains specific
            information
        :keyword float completeness:
            Completeness magnitude

        :return float bval:
            b-value of the Gutenberg-Richter relationship
        :return float sigma_b:
            Standard deviation of the GR b-value
        """
        # Input checks
        _cmag, _ctime, _ref_mag, dmag, config = input_checks(
            catalogue, config, completeness
        )
        rt = recurrence_table(
            catalogue.data["magnitude"], dmag, catalogue.data["year"]
        )
        bval, sigma_b = self._aki_ml(rt[:, 0], rt[:, 1])
        return bval, sigma_b

    def _aki_ml(self, mval, number_obs, dmag=0.1, m_c=0.0):
        """
        :param numpy.ndarray mval:
            array of reference magnitudes (column 0 from recurrence
            table)
        :param numpy.ndarray number_obs:
            number of observations in magnitude bin (column 1 from
            recurrence table)
        :keyword float dmag:
            magnitude interval
        :keyword float m_c:
            completeness magnitude

        :return float bval:
            b-value of the Gutenberg-Richter relationship
        :return float sigma_b:
            Standard deviation of the GR b-value
        """
        # Exclude data below Mc
        id0 = mval >= m_c
        mval = mval[id0]
        number_obs = number_obs[id0]
        # Get Number of events, minimum magnitude and mean magnitude
        neq = np.sum(number_obs)
        if neq <= 1:
            # Cannot determine b-value (too few event) return NaNs
            warnings.warn("Too few events (<= 1) to calculate b-value")
            return np.nan, np.nan

        m_min = np.min(mval)
        m_ave = np.sum(mval * number_obs) / neq
        # Calculate b-value
        bval = np.log10(np.exp(1.0)) / (m_ave - m_min + (dmag / 2.0))
        # Calculate sigma b from Bender estimator
        sigma_b = np.sum(number_obs * ((mval - m_ave) ** 2.0)) / (
            neq * (neq - 1)
        )
        sigma_b = np.log(10.0) * (bval**2.0) * np.sqrt(sigma_b)
        return bval, sigma_b
