# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2021, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import logging
from copy import deepcopy
from scipy.interpolate import RectBivariateSpline
from abc import abstractmethod
from typing import Dict, List, Optional

from openquake.hazardlib.imt import IMT
from openquake.hazardlib.site import SiteCollection
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.correlation.spatial_correlation import \
        BaseCorrelationModel


class BaseSpatialCrossCorrelationModel(BaseCorrelationModel):
    """
    Base class for cross-IM spatial correlation models for
    spatially-distributed ground-shaking intensities.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.cache = {"corma": None}

    @abstractmethod
    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :param from_imt:
            An intensity measure type
        :param to_imt:
            An intensity measure type
        :return: a scalar
        """

    def _get_correlation_matrix(self, sites: SiteCollection, imts: List):
        """
        Setup the correlation matrix given the sites and IMTs
        """
        distances = sites.mesh.get_distance_matrix()
        return self.get_correlation_model(distances, imts)

    @abstractmethod
    def get_correlation_model(self, distances: np.ndarray, imts: List):
        """
        Builds the correlation model - specific to the actual model itself
        """

    def get_lower_triangle_correlation_matrix(
            self, sites: SiteCollection, imts: List):
        # Apply Cholesky factorisation and retreive the
        # lower triangular correlation matrix
        self.cache["corma"] = np.linalg.cholesky(
            self._get_correlation_matrix(sites, imts))

    def apply_correlation(
            self, sites: SiteCollection, imts: List, residuals: np.ndarray):
        """
        Applies the correlation model to the sites
        """
        if not self.cache["corma"]:
            # For first implementation then get the lower
            # matrix
            logging.info("--- Building lower triangle correlation matrix")
            self.get_lower_triangle_correlation_matrix(sites.complete, imts)
            logging.info("--- --- done!")
        nsites = len(sites)
        logging.info("--- Generating spatially cross-correlated residuals")
        if len(sites.complete) == nsites:
            # No filtering of sites
            corr_residuals = np.matmul(self.cache["corma"], residuals)
        else:
            # Need to locate indices of correlation matrix corresponding
            # to the selected sites
            idx = np.tile(sites.indices, len(imts))
            lb = 0
            ub = len(sites)
            norig_sites = len(sites.complete)
            for i in range(len(imts)):
                idx[lb:ub] += i * norig_sites
                lb += nsites
                ub += nsites
            corr_residuals = np.matmul(
                self.cache["corma"][np.ix_(idx, idx)], residuals)

        # corr_residuals is 2-D array [Nimts * Nsites, Nevents]
        # need to re-arrange back to 3-D shape
        residuals = np.empty([len(imts), nsites, corr_residuals.shape[1]])
        idx = np.arange(nsites)
        for i in range(len(imts)):
            residuals[i] = corr_residuals[idx, :]
            idx += nsites
        logging.info("--- --- done!")
        return residuals

    def sample(self,
               num_realizations: int,
               sites: SiteCollection,
               imts: List,
               rng: Optional[np.random.Generator] = None,
               ) -> np.ndarray:
        """Generate random fields from the distribution

        :param num_realizations:
            Number of ground motion fields to generate
        :param sites:
            Site model as instance of
            `class`::shakyground2.site_model.SiteModel
        :param imts:
            List of intensity measure types (as string)
        :param rng:
            Seeded numpy random number generator (or None - uses random seed)

        :Returns: Sample fields of dimension
            [No. Intensiy Measures, No. Sites, No. Realizations]
        """
        if not rng:
            rng = np.random.default_rng()
        uncorrelated_residuals = rng.normal(
            0.0, 1.0, [len(sites) * len(imts), num_realizations]
        )

        return self.apply_correlation(sites, imts, uncorrelated_residuals)


class LothBaker2013CorrelationModel(BaseSpatialCrossCorrelationModel):
    """Implements the spatial cross-correlation model of Loth & Baker (2013)

    Loth, C., and Baker, J. W. (2013) A spatial cross-correlation model of
    spectral accelerations at multiple periods. Earthquake Engineering &
    Structural Dynamics, 42: 397 - 417

    Valid for periods 0.01 to 10.0 s
    """

    T = np.array([0.01, 0.1, 0.2, 0.5, 1.00, 2.00, 5.00, 7.5, 10.00])

    # Table II. Short range coregionalization matrix, B1
    B1 = np.array(
        [
            [0.29, 0.25, 0.23, 0.23, 0.18, 0.10, 0.06, 0.06, 0.06],
            [0.25, 0.30, 0.20, 0.16, 0.10, 0.04, 0.03, 0.04, 0.05],
            [0.23, 0.20, 0.27, 0.18, 0.10, 0.03, 0.00, 0.01, 0.02],
            [0.23, 0.16, 0.18, 0.31, 0.22, 0.14, 0.08, 0.07, 0.07],
            [0.18, 0.10, 0.10, 0.22, 0.33, 0.24, 0.16, 0.13, 0.12],
            [0.10, 0.04, 0.03, 0.14, 0.24, 0.33, 0.26, 0.21, 0.19],
            [0.06, 0.03, 0.00, 0.08, 0.16, 0.26, 0.37, 0.30, 0.26],
            [0.06, 0.04, 0.01, 0.07, 0.13, 0.21, 0.30, 0.28, 0.24],
            [0.06, 0.05, 0.02, 0.07, 0.12, 0.19, 0.26, 0.24, 0.23]
        ]
    )

    # Table III. Long range coregionalization matrix, B2
    B2 = np.array(
        [
            [0.47, 0.40, 0.43, 0.35, 0.27, 0.15, 0.13, 0.09, 0.12],
            [0.40, 0.42, 0.37, 0.25, 0.15, 0.03, 0.04, 0.00, 0.03],
            [0.43, 0.37, 0.45, 0.36, 0.26, 0.15, 0.09, 0.05, 0.08],
            [0.35, 0.25, 0.36, 0.42, 0.37, 0.29, 0.20, 0.16, 0.16],
            [0.27, 0.15, 0.26, 0.37, 0.48, 0.41, 0.26, 0.21, 0.21],
            [0.15, 0.03, 0.15, 0.29, 0.41, 0.55, 0.37, 0.33, 0.32],
            [0.13, 0.04, 0.09, 0.20, 0.26, 0.37, 0.51, 0.49, 0.49],
            [0.09, 0.00, 0.05, 0.16, 0.21, 0.33, 0.49, 0.62, 0.60],
            [0.12, 0.03, 0.08, 0.16, 0.21, 0.32, 0.49, 0.60, 0.68]
        ]
    )

    # Table IV. Nugget effect coregionalization matrix, B3
    B3 = np.array(
        [
            [0.24, 0.22, 0.21, 0.09, -0.02, 0.01, 0.03, 0.02, 0.01],
            [0.22, 0.28, 0.20, 0.04, -0.05, 0.00, 0.01, 0.01, -0.01],
            [0.21, 0.20, 0.28, 0.05, -0.06, 0.00, 0.04, 0.03, 0.01],
            [0.09, 0.04, 0.05, 0.26, 0.14, 0.05, 0.05, 0.05, 0.04],
            [-0.02, -0.05, -0.06, 0.14, 0.20, 0.07, 0.05, 0.05, 0.05],
            [0.01, 0.00, 0.00, 0.05, 0.07, 0.12, 0.08, 0.07, 0.06],
            [0.03, 0.01, 0.04, 0.05, 0.05, 0.08, 0.12, 0.10, 0.08],
            [0.02, 0.01, 0.03, 0.05, 0.05, 0.07, 0.10, 0.10, 0.09],
            [0.01, -0.01, 0.01, 0.04, 0.05, 0.06, 0.08, 0.09, 0.09]
        ]
    )

    def __repr__(self):
        return "LothBaker2013"

    def get_correlation_model(self, distances: np.ndarray, imts: List):
        """
        Build the correlation model for the particular
        configuration
        """
        periods = []
        for imt in imts:
            if str(imt) == "PGA":
                periods.append(0.01)
            elif "SA" in str(imt):
                if (imt.period > 10.0) or (imt.period < 0.01):
                    raise ValueError(
                        "Period %s out of range for Loth & Baker LMCR" % str(
                            imt.period)
                    )
                periods.append(imt.period)
            else:
                raise ValueError(
                    "Loth & Baker LMCR not supported for %s" % str(imt))

        periods = np.array(periods)
        b1mat = self.interp_matrix(periods, self.T, self.B1)
        b2mat = self.interp_matrix(periods, self.T, self.B2)
        b3mat = self.interp_matrix(periods, self.T, self.B3)
        dh = np.array(-3.0 * distances)
        if isinstance(dh, float):
            rho = b1mat * np.exp(dh / 20.0) + b2mat * np.exp(dh / 70.0)
            if dh < 1.0e-7:
                rho += b3mat
            return rho
        else:
            # dh is a matrix
            x, y = distances.shape
            mask = np.array(distances < 1.0e-7)
            nimts = len(periods)
            rho = np.zeros([nimts * x, nimts * y])
            idx_x = np.arange(0, x)
            for i in range(nimts):
                idx_y = np.arange(0, y)
                for j in range(nimts):
                    dummy = b1mat[i, j] * \
                        np.exp(dh / 20.0) + b2mat[i, j] * np.exp(dh / 70.0)
                    dummy[mask] += b3mat[i, j]
                    rho[np.ix_(idx_x, idx_y)] += dummy
                    idx_y += y
                idx_x += x
        return rho

    @staticmethod
    def interp_matrix(targets, periods, matrix):
        """Apply 2D interpolation to retrieve the values of the coefficient
        matrices at the required periods
        """
        f = RectBivariateSpline(periods, periods, matrix.T, kx=1, ky=1)
        return f(targets, targets).T


def get_isotropic_nested_cov(var_model: Dict, dist: np.ndarray) -> np.ndarray:
    """Returns the covariance matrix for the isotropic, nested, exponential
    semivariogram

    Args:
        var_model: Coefficients of the semivariogram model
        dist: distance matrix

    Returns:
        cov: Covariance matrix
    """
    var = var_model["Cn"] + var_model["C1"] + var_model["C2"]
    cov = var - (
        var_model["Cn"]
        + var_model["C1"] * (1.0 - np.exp(-3.0 * dist / var_model["A1"]))
        + var_model["C2"] * (1.0 - np.exp(-3.0 * dist / var_model["A2"]))
    )
    cov[dist == 0.0] = var
    return cov


def get_nugget_cov(var_model: Dict, dist: np.ndarray) -> np.ndarray:
    """Returns the covarance matrix for the nugget semivariogram

    Args:
        var_model: Coefficients of the semivariogram model
        dist: distance matrix

    Returns:
        cov: Covariance matrix
    """
    return np.eye(len(dist)) * var_model["Cn"]


class MarkhvidaEtAl2018CorrelationModel(BaseSpatialCrossCorrelationModel):
    """
    Implements the spatial cross-correlation model of Markhvida et al. (2018)
    based on principal component analysis and geostatistics.

    Markhvida, M., Ceferino, L., & Baker, J. W. (2018).
    Modeling spatially correlated spectral accelerations at multiple periods
    using principal component analysis and geostatistics. Earthquake
    Engineering & Structural Dynamics, 47(5), 1107-1123.
    https://doi.org/10.1002/eqe.3007
    """

    T = np.array(
        [
            0.01,
            0.02,
            0.03,
            0.05,
            0.075,
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
            0.40,
            0.50,
            0.75,
            1.00,
            1.50,
            2.00,
            3.00,
            4.00,
            5.00,
        ]
    )

    PCA_COEFFS = CoeffsTable(
        sa_damping=5,
        table="""\
        imt                    1               2               3               4               5               6               7               8               9              10              11              12              13              14              15              16              17              18              19
        pga       2.70963956e-01 -1.39418157e-01  6.90420061e-02 -1.06094866e-01 -9.22880748e-02 -1.13489976e-01 -1.88935371e-01  1.53956802e-01 -1.60082932e-01 -4.85878662e-02  1.06169114e-01  5.45367125e-02 -8.42347289e-02  2.06507178e-03  2.33666516e-01 -4.44106081e-02 -2.98766213e-01 -5.27588860e-01 -5.80349073e-01
        0.010     2.70963956e-01 -1.39418157e-01  6.90420061e-02 -1.06094866e-01 -9.22880748e-02 -1.13489976e-01 -1.88935371e-01  1.53956802e-01 -1.60082932e-01 -4.85878662e-02  1.06169114e-01  5.45367125e-02 -8.42347289e-02  2.06507178e-03  2.33666516e-01 -4.44106081e-02 -2.98766213e-01 -5.27588860e-01 -5.80349073e-01
        0.020     2.70185457e-01 -1.41734439e-01  7.70156687e-02 -1.16393534e-01 -1.03464378e-01 -1.24082463e-01 -1.99840301e-01  1.55452551e-01 -1.57024101e-01 -5.11781532e-02  1.02685985e-01  5.34091782e-02 -7.85807733e-02  5.38047461e-03  2.20317829e-01 -3.94525931e-02 -2.57172669e-01 -1.50994889e-01  7.81868928e-01
        0.030     2.66716484e-01 -1.50918021e-01  1.01241750e-01 -1.44620230e-01 -1.28327845e-01 -1.50413273e-01 -2.17519115e-01  1.54533128e-01 -1.44555133e-01 -4.93784913e-02  8.65380809e-02  3.69034473e-02 -5.51975904e-02  7.87249482e-03  1.49651510e-01 -2.32087970e-02 -2.84597880e-02  8.08901724e-01 -2.26437335e-01
        0.050     2.51688240e-01 -1.84642999e-01  1.78879968e-01 -2.21328311e-01 -1.75557526e-01 -1.76668887e-01 -1.88651351e-01  4.24749059e-02 -4.55090102e-02 -2.91885727e-02 -3.15764521e-02 -6.05411455e-02  9.35508236e-02  2.24423933e-02 -2.99181352e-01  5.99168859e-02  7.54350403e-01 -2.06472973e-01  2.31093445e-02
        0.075     2.36434541e-01 -2.18922079e-01  2.37254184e-01 -2.34559034e-01 -1.33267088e-01 -4.31828094e-02  1.19447151e-01 -2.72310555e-01  2.38192698e-01  1.00676333e-01 -2.63315034e-01 -1.21207177e-01  2.02769694e-01  6.61936094e-03 -4.93306767e-01  1.16246173e-01 -4.75923823e-01  3.67733765e-02 -6.43955732e-03
        0.100     2.32994643e-01 -2.28087987e-01  2.30554573e-01 -1.60443024e-01  4.00564219e-02  1.81657485e-01  4.27112684e-01 -3.24579280e-01  2.63780433e-01  1.42634796e-01 -8.13780348e-02  4.65305509e-02 -1.51801547e-01 -8.33183140e-02  5.34198178e-01 -1.84596750e-01  2.10357917e-01 -2.84225564e-03  3.31108667e-03
        0.150     2.38919759e-01 -2.11905954e-01  1.32646222e-01  8.20453503e-02  3.27946973e-01  3.93273105e-01  3.25836316e-01  1.62029625e-01 -1.82164846e-01 -1.38319895e-01  4.70111475e-01  1.77876088e-01 -1.11256500e-01  8.83177907e-02 -2.91143253e-01  2.62494245e-01 -1.52291509e-03  1.54770016e-02  1.50080927e-03
        0.200     2.47247201e-01 -1.74053610e-01 -8.25743328e-03  2.77382297e-01  4.03271334e-01  2.20437620e-01 -8.37312940e-02  2.24796020e-01 -1.71941473e-01 -2.92747130e-02 -3.81524121e-01 -2.37244496e-01  3.56271009e-01 -8.50494997e-02 -1.25434811e-02 -4.42559355e-01  1.51125188e-02  1.10964548e-02  1.94187520e-03
        0.250     2.53677097e-01 -1.22375885e-01 -1.48595586e-01  3.65271223e-01  2.53186444e-01 -6.12442511e-02 -2.83389735e-01 -8.11437932e-02  2.12210668e-01  1.43362427e-01 -2.75727619e-01 -4.11307165e-02 -2.02014525e-01  2.28459039e-02  1.55257214e-01  6.32145332e-01  4.55130188e-02  6.90596762e-04  4.69634929e-04
        0.300     2.54921192e-01 -7.13194464e-02 -2.37030888e-01  3.59073100e-01  4.01080107e-02 -2.48766602e-01 -1.41859038e-01 -2.86692239e-01  3.00971238e-01  5.79993716e-02  3.28411992e-01  2.08361703e-01 -1.94768508e-01  3.24295009e-02 -2.58822161e-01 -4.77244327e-01  1.91094744e-03  6.62185259e-03  1.88266913e-04
        0.400     2.52458254e-01  1.25091294e-02 -3.27121081e-01  2.26053197e-01 -2.61297620e-01 -2.16236975e-01  3.44080560e-01 -1.21230621e-01 -6.02714323e-02 -2.19189671e-01  2.11470671e-01 -1.28634841e-01  5.76234521e-01 -5.50760430e-02  1.97333044e-01  2.05766455e-01  2.36621450e-02  3.70370109e-03  1.85197343e-04
        0.500     2.45944241e-01  7.99604140e-02 -3.58449873e-01  6.40998105e-02 -3.41792254e-01  2.24967546e-02  3.88717982e-01  1.77122204e-01 -2.55990758e-01 -6.44303562e-03 -3.75390123e-01 -7.62061467e-02 -5.02002036e-01  1.83662355e-02 -1.76351452e-01 -6.86345487e-02  1.54233464e-02  5.41822808e-03  1.27868850e-03
        0.750     2.25758567e-01  1.91381035e-01 -3.35176303e-01 -2.16152634e-01 -1.65178955e-01  4.23011572e-01 -1.44255462e-01  1.87567292e-01  1.49360082e-01  5.30105301e-01  4.17962321e-02  3.26784764e-01  2.74609836e-01  5.58724755e-02  4.42737636e-03  1.11352503e-02  2.44045339e-02  6.82889258e-04  1.98665379e-04
        1.000     2.11097169e-01  2.59405650e-01 -2.43643585e-01 -3.25745719e-01  7.63484286e-02  3.30279571e-01 -2.20001696e-01 -1.17395307e-01  2.71296591e-01 -4.38774328e-01  1.48165306e-01 -4.84545679e-01 -1.43691434e-01 -3.89147467e-02  8.93381613e-03 -2.05549231e-02 -6.11584426e-03  3.80246485e-03 -3.89229001e-04
        1.500     1.88387437e-01  3.29799741e-01 -9.46692612e-02 -2.73646379e-01  3.56651426e-01 -1.53161130e-01 -6.82050970e-04 -3.29897663e-01 -2.67361750e-01 -2.79382156e-01 -2.63740501e-01  5.28987613e-01  7.03281456e-02 -8.35258439e-02 -2.54953444e-02  2.71139319e-02  1.26194670e-02  3.85357399e-03 -8.09502038e-04
        2.000     1.76395533e-01  3.57332294e-01  5.54387509e-02 -1.55161958e-01  3.54513035e-01 -3.43041979e-01  1.61895880e-01 -2.75355961e-02 -2.07859409e-01  5.06833313e-01  2.05450556e-01 -4.13916086e-01 -4.07497251e-02  1.68472841e-01 -2.35465742e-03 -5.88317617e-03 -3.34222371e-03  1.97868686e-03  1.70392027e-03
        3.000     1.65469018e-01  3.60040620e-01  2.60392170e-01  6.69803672e-02  5.72701976e-02 -2.20913199e-01  1.81062550e-01  5.19913777e-01  4.62086625e-01 -1.04489885e-01 -2.19632037e-02  1.19011799e-01 -4.29988165e-03 -4.17545575e-01 -4.01081046e-02  2.00607204e-02 -5.26025220e-03 -5.80167364e-03  4.58230034e-04
        4.000     1.59580892e-01  3.47927160e-01  3.48346295e-01  2.39394141e-01 -1.57211928e-01  9.28779109e-02 -5.01602104e-03  1.69759688e-02  1.09978222e-01 -1.82603154e-01 -1.21233490e-01  7.11306931e-02  6.20582734e-02  7.50450107e-01  7.85420661e-02 -5.21102089e-02  7.51936647e-03 -1.88268150e-03 -1.85190445e-03
        5.000     1.48832921e-01  3.32847695e-01  3.65098052e-01  3.31227695e-01 -2.81334582e-01  2.83334016e-01 -1.82848345e-01 -3.25817997e-01 -3.10946154e-01  1.28556114e-01  8.37173663e-02 -7.03828761e-02 -4.61924126e-02 -4.41499964e-01 -4.05906261e-02  3.37161618e-02  1.16291918e-03  4.01605033e-03  5.05570345e-04
    """,
    )

    VARIANCE_SCALE_FACTOR = np.array(
        [
            0.63984174,
            0.84627714,
            0.90453306,
            0.93340282,
            0.95015459,
            0.96046156,
            0.96797214,
            0.97387821,
            0.97929703,
            0.98334580,
            0.98663949,
            0.98968140,
            0.99236758,
            0.99479044,
            0.99692908,
            0.99875974,
            0.99976488,
            0.99996981,
            1.0,
        ]
    )

    MODEL_VARIO = {
        1: {"Cn": 2.5, "C1": 4.52, "A1": 15.0, "C2": 6.78, "A2": 250.0, "type": "iso nest"},
        2: {"Cn": 0.5, "C1": 1.40, "A1": 10.0, "C2": 2.60, "A2": 160.0, "type": "iso nest"},
        3: {"Cn": 0.15, "C1": 0.42, "A1": 15.0, "C2": 0.63, "A2": 160.0, "type": "iso nest"},
        4: {"Cn": 0.15, "C1": 0.225, "A1": 10.0, "C2": 0.225, "A2": 120.0, "type": "iso nest"},
        5: {"Cn": 0.31432187, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        6: {"Cn": 0.19074954, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        7: {"Cn": 0.13784676, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        8: {"Cn": 0.11128384, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        9: {"Cn": 0.09649928, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        10: {"Cn": 0.0717368, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        11: {"Cn": 0.06481622, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        12: {"Cn": 0.05407664, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        13: {"Cn": 0.05118875, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        14: {"Cn": 0.04331642, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        15: {"Cn": 0.04139805, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        16: {"Cn": 0.03466367, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        17: {"Cn": 0.01879699, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        18: {"Cn": 0.00285694, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
        19: {"Cn": 0.00036065, "C1": 0.0, "A1": 0.0, "C2": 0.0, "A2": 0.0, "type": "nug"},
    }

    def __init__(self, **kwargs):
        """
        :param npcs: Number of principal components to be used
            (must be between 5 and 19)
        """

        super().__init__(**kwargs)
        self.npcs = int(kwargs.get("num_pcs", 5))
        assert (self.npcs >= 5) and (self.npcs <= 19), (
           "Number of principal components must be between 5 and 19 "
           f"({self.npcs} given)"
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.npcs} Principal Components)"

    def get_correlation_model(self, distances: np.ndarray, imts: List):
        """Correlation model is not relevant in this context"""
        pass

    def get_lower_triangle_correlation_matrix(
            self, sites: SiteCollection, imts: List):
        """In this case the lower triangle correlation matrix has a different
        interpretation as here it has the dimension
        [num_sites, num_sites, num principal components]
        """
        # Get the distance matrix for the sites
        distance_matrix = sites.mesh.get_distance_matrix()
        model_vario = deepcopy(self.MODEL_VARIO)
        if self.npcs < 19:
            # If less than 19 principal components are used then scale down
            # the variance
            scale_factor = self.VARIANCE_SCALE_FACTOR[self.npcs - 1]
            for i in range(1, 20):
                model_vario[i]["Cn"] /= scale_factor
                if model_vario[i]["type"] != "nug":
                    model_vario[i]["C1"] /= scale_factor
                    model_vario[i]["C2"] /= scale_factor
        # Build the covariance matrices
        n_y, n_x = distance_matrix.shape
        self.cache["corma"] = np.empty([n_y, n_x, self.npcs])
        for i in range(self.npcs):
            var_model = model_vario[i + 1]
            if var_model["type"] == "nug":
                cov = get_nugget_cov(var_model, distance_matrix)
            else:
                cov = get_isotropic_nested_cov(var_model, distance_matrix)
            self.cache["corma"][:, :, i] = np.linalg.cholesky(cov)
        return

    def apply_correlation(
            self, sites: SiteCollection, imts: List, residuals: np.ndarray):
        """Apply the correlation models to the arrays on simulated residuals"""
        # Get the required PCA coefficients for the corresponding period
        pca_coeffs = {}
        for imt in imts:
            if str(imt) == "PGV":
                raise ValueError(
                    f"Correlation model {str(self)} not supported for PGV")
            pca_coeff = self.PCA_COEFFS[imt]
            pca_coeffs[imt] = np.array(
                [[pca_coeff["{:g}".format(i + 1)] for i in range(self.npcs)]]
            ).T
        nimts = len(imts)
        if not self.cache["corma"]:
            # Get the lower covariance matrices
            logging.info("Building lower triangle correlation matrices")
            self.get_lower_triangle_correlation_matrix(sites, imts)
            logging.info("Lower triangle correlation matrices built.")
        nlocs, nsims, _ = residuals.shape
        # Get simulated PCA matrices for each realisation of residuals
        logging.info("Generating spatially cross-correlated residuals")
        sim_pcas = np.empty([nlocs, nsims, self.npcs])
        for i in range(self.npcs):
            logging.info(
                "Processing principal component %g of %g" % (i + 1, self.npcs))
            for j in range(nsims):
                res = residuals[:, [j], [i]]
                sim_pcas[:, j, i] = (self.cache["corma"][:, :, i] @ res)[:, 0]

        sim_results = np.zeros([nimts, nlocs, nsims])
        for i, imt in enumerate(imts):
            for j in range(nsims):
                sim_results[i, :, j] = (
                    sim_pcas[:, j, :] @ pca_coeffs[imt])[:, 0]
        logging.info("Principal component processing completed.")
        return sim_results

    def sample(
        self,
        num_realizations: int,
        sites: SiteCollection,
        imts: List,
        rng: Optional[np.random.Generator] = None,
    ) -> np.ndarray:
        if not rng:
            rng = np.random.default_rng()
        uncorrelated_residuals = rng.normal(
            0.0, 1.0, [len(sites), num_realizations, self.npcs])
        return self.apply_correlation(sites, imts, uncorrelated_residuals)
