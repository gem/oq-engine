# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020-2023, GEM Foundation
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

from typing import Union
import numpy as np

try:
    import onnxruntime
except ImportError:
    onnxruntime = None

# Table mapping the qualitative susceptibility of soils to liquefaction
# to the minimum PGA level necessary to induce liquefaction
HAZUS_LIQUEFACTION_PGA_THRESHOLD_TABLE = {
    b"vh": 0.09,
    b"h": 0.12,
    b"m": 0.15,
    b"l": 0.21,
    b"vl": 0.26,
    b"n": 5.0,
    "vh": 0.09,
    "h": 0.12,
    "m": 0.15,
    "l": 0.21,
    "vl": 0.26,
    "n": 5.0,
}

# Table mapping the qualitative susceptibility of soils to liquefaction
# to coefficients for the range of PGA that can cause liquefaction.
# See `hazus_conditional_liquefaction_probability` for more explanation
# of how these values are used.
HAZUS_LIQUEFACTION_COND_PROB_PGA_TABLE = {
    b"vh": [9.09, 0.82],
    b"h": [7.67, 0.92],
    b"m": [6.67, 1.0],
    b"l": [5.57, 1.18],
    b"vl": [4.16, 1.08],
    b"n": [0.0, 0.0],
    "vh": [9.09, 0.82],
    "h": [7.67, 0.92],
    "m": [6.67, 1.0],
    "l": [5.57, 1.18],
    "vl": [4.16, 1.08],
    "n": [0.0, 0.0],
}


HAZUS_LIQUEFACTION_MAP_AREA_PROPORTION_TABLE = {
    b"vh": 0.25,
    b"h": 0.2,
    b"m": 0.1,
    b"l": 0.05,
    b"vl": 0.02,
    b"n": 0.0,
    "vh": 0.25,
    "h": 0.2,
    "m": 0.1,
    "l": 0.05,
    "vl": 0.02,
    "n": 0.0,
}


FT_PER_M = 3.28084
CM_PER_M = 100
NUM = 10**2.24


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _idriss_magnitude_scaling_factor(mag: float):
    """
    Youd, T. L., & Idriss, I. M. (2001).
    Liquefaction Resistance of Soils: Summary Report from the 1996 NCEER
    and 1998 NCEER/NSF Workshops on Evaluation of Liquefaction Resistance
    of Soils. Journal of Geotechnical
    and Geoenvironmental Engineering, 127(4), 297–313.
    https://doi.org/10.1061/(asce)1090-0241(2001)127:4(297)
    """
    return (NUM) / (mag**2.56)


def _idriss_magnitude_weighting_factor(mag: float):
    """
    Corrects the liquefaction probabilty equations based on the magnitude
    of the causative earthquake. Defined as the inverse of the magnitude
    scaling factor.
    """
    return 1.0 / _idriss_magnitude_scaling_factor(mag)


def _liquefaction_spatial_extent(a: float, b: float, c: float, p: float):
    """
    Calculates the liquefaction spatial extent (LSE) in % as per formulae 2
    from the Reference. LSE after an earthquake is the spatial area covered
    by surface manifestations of liquefaction reported as a percentage of a
    pixel at a specific location on the map.

    Reference: Zhu, J., Baise, L. G., & Thompson, E. M. (2017).
    An updated geospatial liquefaction model for global application.
    Bulletin of the Seismological Society of America, 107(3), 1365–1385.
    https://doi.org/10.1785/0120160198
    """
    LSE = a / (1 + b * np.exp(-c * p)) ** 2
    return LSE


def zhu_etal_2015_general(
    pga: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    cti: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    intercept: float = 24.1,
    pgam_coeff: float = 2.067,
    cti_coeff: float = 0.355,
    vs30_coeff: float = -4.784,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of Zhu et al., 2015. This particular equation is
    the 'general model' with global applicability.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.2 (see Table 6 from the
    Reference).

    Reference: Zhu et al., 2015, 'A Geospatial Liquefaction Model for Rapid
    Response and Loss Estimation', Earthquake Spectra, 31(3), 1813-1837.

    :param pga:
        Peak Ground Acceleration, measured in g
    :param mag:
        Magnitude of causative earthquake (moment or work scale)
    :param cti:
        Compound Topographic Index, a proxy for soil wetness.
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site.

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
    """
    pga_scale = pga * _idriss_magnitude_weighting_factor(mag)
    Xg = (
        pgam_coeff * np.log(pga_scale)
        + cti_coeff * cti
        + vs30_coeff * np.log(vs30)
        + intercept
    )
    prob_liq = sigmoid(Xg)
    out_class = np.where(prob_liq > 0.2, 1, 0)
    return prob_liq, out_class


def zhu_etal_2017_coastal(
    pgv: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    dr: Union[float, np.ndarray],
    dc: Union[float, np.ndarray],
    precip: Union[float, np.ndarray],
    intercept: float = 12.435,
    pgv_coeff: float = 0.301,
    vs30_coeff: float = -2.615,
    dr_coeff: float = 0.0666,
    dc_coeff: float = -0.0287,
    dcdr_coeff: float = -0.0369,
    precip_coeff: float = 0.0005556,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of Zhu et al., 2017. This particular equation is
    the recommended 'coastal model'. A coastal event is defined as one
    where the liquefaction occurrences are, on average, within 20 km of the
    coast; or, for earthquakes with insignificant or no liquefaction,
    epicentral distances less than 50 km.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.4 (see p.13 from the
    Reference).
    Liquefaction spatial extent (LSE) is calculated as per formulae 2 from the
    Reference. Model's coefficients are given in Table 6 (Model 1).

    Reference: Zhu, J., Baise, L. G., & Thompson, E. M. (2017).
    An updated geospatial liquefaction model for global application.
    Bulletin of the Seismological Society of America, 107(3), 1365–1385.
    https://doi.org/10.1785/0120160198

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site, measured in m/s
    :param dr:
        Distance to the nearest river, measured in km
    :param dc:
        Distance to the nearest coast, measured in km
    :param precip:
        Mean annual precipitation, measured in mm

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
        LSE: Liquefaction spatial extent (in %).
    """
    Xg = (
        pgv_coeff * np.log(pgv)
        + vs30_coeff * np.log(vs30)
        + precip_coeff * precip
        + dc_coeff * np.sqrt(dc)
        + dr_coeff * dr
        + dcdr_coeff * np.sqrt(dc) * dr
        + intercept
    )
    prob_liq = sigmoid(Xg)

    # Zhu et al. 2017 heuristically assign zero to the predicted probability
    # for both models when PGV < 3 cm/s. Similarly, they assign zero to the
    # probability when VS30 > 620 m/s.
    prob_liq = np.where((pgv < 3.0) | (vs30 > 620), 0, prob_liq)
    out_class = np.where(prob_liq > 0.4, 1, 0)
    LSE = _liquefaction_spatial_extent(42.08, 62.59, 11.43, prob_liq)
    return prob_liq, out_class, LSE


def zhu_etal_2017_general(
    pgv: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    dw: Union[float, np.ndarray],
    wtd: Union[float, np.ndarray],
    precip: Union[float, np.ndarray],
    intercept: float = 8.801,
    pgv_scaling_factor: float = 1.0,
    pgv_coeff: float = 0.334,
    vs30_coeff: float = -1.918,
    dw_coeff: float = -0.2054,
    wtd_coeff: float = -0.0333,
    precip_coeff: float = 0.0005408,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of the Zhu et al., 2017. This particular equation is
    the recommended noncoastal model, which is the model recommended by the
    authors for global implementation. Noncoastal events are defined as those
    for which the average distance to the nearest coast of the liquefaction
    features is greater than 20 km.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.4
    (see p.13 from the Reference).
    Liquefaction spatial extent (LSE) is calculated as per formulae 2 from the
    Reference. Model's coefficients are given in Table 6 (Model 2).

    Reference: Zhu, J., Baise, L. G., & Thompson, E. M. (2017).
    An updated geospatial liquefaction model for global application.
    Bulletin of the Seismological Society of America, 107(3), 1365–1385.
    https://doi.org/10.1785/0120160198

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site, measured in m/s
    :param dw:
        Distance to the nearest water body, measured in km
    :param wtd:
        Global water table depth, measured in m
    :param precip:
        Mean annual precipitation, measured in mm

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
        LSE: Liquefaction spatial extent (in %).
    """
    Xg = (
        pgv_coeff * np.log(pgv_scaling_factor * pgv)
        + vs30_coeff * np.log(vs30)
        + precip_coeff * precip
        + dw_coeff * dw
        + wtd_coeff * wtd
        + intercept
    )
    prob_liq = sigmoid(Xg)

    # Zhu et al. 2017 heuristically assign zero to the predicted probability
    # for both models when PGV < 3 cm/s. Similarly, they assign zero to the
    # probability when VS30 > 620 m/s.
    prob_liq = np.where((pgv < 3.0) | (vs30 > 620), 0, prob_liq)
    out_class = np.where(prob_liq > 0.4, 1, 0)
    LSE = _liquefaction_spatial_extent(49.15, 42.40, 9.165, prob_liq)
    return prob_liq, out_class, LSE


def rashidian_baise_2020(
    pga: Union[float, np.ndarray],
    pgv: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    dw: Union[float, np.ndarray],
    wtd: Union[float, np.ndarray],
    precip: Union[float, np.ndarray],
    intercept: float = 8.801,
    pgv_scaling_factor: float = 1.0,
    pgv_coeff: float = 0.334,
    vs30_coeff: float = -1.918,
    dw_coeff: float = -0.2054,
    wtd_coeff: float = -0.0333,
    precip_coeff: float = 0.0005408,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of the Zhu et al., 2017 noncoastal model, which is the
    model recommended by the authors for global implementation, as modified
    by Rashidian and Baise (2020) to decrease over-prediction in large areas
    experiencing low PGA (below 0.1 g) with the addition of a PGA threshold
    (no liquefaction when PGA < 0.1 g). An upper bound for the annual
    precipitation of 1700 mm is recommended.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.4
    (see p.13 from Zhu et al., 2017).
    Liquefaction spatial extent (LSE) is calculated as per formulae 3 from the
    Reference. Model's coefficients corresponds to the ones for Model 2 from
    Zhu et al., 2017.

    Reference: Rashidian, V., & Baise, L. G. (2020).
    Regional efficacy of a global geospatial liquefaction model.
    Engineering Geology, 272, 105644.
    https://doi.org/10.1016/j.enggeo.2020.105644

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site, measured in m/s
    :param dw:
        Distance to the nearest water body, measured in km
    :param wtd:
        Global water table depth, measured in m
    :param precip:
        Mean annual precipitation, measured in mm

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
    """

    precip = np.where(precip > 1700, 1700, precip)
    prob_liq, _, _ = zhu_etal_2017_general(
        pgv,
        vs30,
        dw,
        wtd,
        precip,
        intercept=intercept,
        pgv_scaling_factor=pgv_scaling_factor,
        pgv_coeff=pgv_coeff,
        vs30_coeff=vs30_coeff,
        dw_coeff=dw_coeff,
        wtd_coeff=wtd_coeff,
        precip_coeff=precip_coeff,
    )

    # Zhu et al. 2017 heuristically assign zero to the predicted probability
    # for both models when PGV < 3 cm/s. Similarly, they assign zero to the
    # probability when VS30 > 620 m/s. Additionally, Rashidian and Baise (2020)
    # assign zero to the probability when PGA < 0.1 g.
    prob_liq = np.where((pgv < 3.0) | (vs30 > 620), 0, prob_liq)
    prob_liq = np.where(pga < 0.1, 0, prob_liq)
    out_class = np.where(prob_liq > 0.4, 1, 0)
    LSE = _liquefaction_spatial_extent(49.15, 42.40, 9.165, prob_liq)
    return prob_liq, out_class, LSE


def allstadt_etal_2022(
    pga: Union[float, np.ndarray],
    pgv: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    dw: Union[float, np.ndarray],
    wtd: Union[float, np.ndarray],
    precip: Union[float, np.ndarray],
    intercept: float = 8.801,
    pgv_coeff: float = 0.334,
    vs30_coeff: float = -1.918,
    dw_coeff: float = -0.2054,
    wtd_coeff: float = -0.0333,
    precip_coeff: float = 0.0005408,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of the Zhu et al., 2017 noncoastal model, which is the
    model recommended by the authors for global implementation, as modified
    by Rashidian and Baise (2020) to decrease over-prediction in large areas
    experiencing low PGA (below 0.1 g) with the addition of a PGA threshold
    (no liquefaction when PGA < 0.1 g). For use in their the US Geological
    Survey (USGS) ground failure (GF) product, further caps on precipitation
    and PGV of 2500 mm/year and 150 cm/s respectively were imposed to avoid
    unrealistic extrapolations when either factor was much higher than found
    in the training data, as described in Allstadt et al. (2022). Finally, an
    ad-hoc magnitude scaling factor is applied to the PGV values to reduce
    overprediction of liquefaction probabilities for lower magnitude events.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.4
    (see p.13 from Zhu et al., 2017).

    Reference: Allstadt, K. E., Thompson, E. M., Jibson, R. W., Wald, D. J.,
    Hearne, M., Hunter, E. J., Fee, J., Schovanec, H., Slosky, D.,
    & Haynie, K. L. (2022). The US Geological Survey ground failure product:
    Near-real-time estimates of earthquake-triggered landslides and
    liquefaction.
    Earthquake Spectra, 38(1), 5–36. https://doi.org/10.1177/87552930211032685

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site, measured in m/s
    :param dw:
        Distance to the nearest water body, measured in km
    :param wtd:
        Global water table depth, measured in m
    :param precip:
        Mean annual precipitation, measured in mm

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
    """
    pgv = np.where(pgv > 150, 150, pgv)
    precip = np.where(precip > 2500, 2500, precip)
    pgv_scaling_factor = 1.0 / (1.0 + np.exp(-2.0 * (mag - 6.0)))
    prob_liq, _, _ = rashidian_baise_2020(
        pga,
        pgv,
        vs30,
        dw,
        wtd,
        precip,
        intercept=intercept,
        pgv_scaling_factor=pgv_scaling_factor,
        pgv_coeff=pgv_coeff,
        vs30_coeff=vs30_coeff,
        dw_coeff=dw_coeff,
        wtd_coeff=wtd_coeff,
        precip_coeff=precip_coeff,
    )
    prob_liq = np.where((pgv < 3.0) | (vs30 > 620), 0, prob_liq)
    prob_liq = np.where(pga < 0.1, 0, prob_liq)
    out_class = np.where(prob_liq > 0.4, 1, 0)
    LSE = _liquefaction_spatial_extent(49.15, 42.40, 9.165, prob_liq)
    return prob_liq, out_class, LSE


def akhlagi_etal_2021_model_a(
    pgv: Union[float, np.ndarray],
    tri: Union[float, np.ndarray],
    dc: Union[float, np.ndarray],
    dr: Union[float, np.ndarray],
    zwb: Union[float, np.ndarray],
    intercept: float = 4.925,
    pgv_coeff: float = 0.694,
    tri_coeff: float = -0.459,
    dc_coeff: float = -0.403,
    dr_coeff: float = -0.309,
    zwb_coeff: float = -0.164,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of the Akhlagi et al., 2021 model A.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.4
    (see p.13 from Zhu et al., 2017).

    Reference: Akhlaghi, A., Baise, L. G., Moaveni, B., Chansky, A. A.,
    & Meyer, M. (2021). An Update to the Global Geospatial Liquefaction
    Model With Uncertainty Propagation. SSA Annual Meeting Abstracts (p. 162).
    Seismological Society of America.
    Model parameters described in: Baise, L. G., Akhlaghi, A., Chansky, A.,
    Meyer, M., & Moeveni, B. (2021). USGS Award #G20AP00029. Updating the
    Geospatial Liquefaction Database and Model.
    Tufts University. Medford, Massachusetts, United States.

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param tri:
        Topographic roughness index, unitless
    :param dc:
        Distance to the nearest coast, measured in km
    :param dr:
        Distance to the nearest river, measured in km
    :param zwb:
        Elevation above the nearest water body, measured in m

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
    """

    Xg = (
        pgv_coeff * np.log(pgv)
        + tri_coeff * np.sqrt(tri)
        + dc_coeff * np.log(dc + 1)
        + dr_coeff * np.log(dr + 1)
        + zwb_coeff * np.sqrt(zwb)
        + intercept
    )
    prob_liq = sigmoid(Xg)
    out_class = np.where(prob_liq > 0.4, 1, 0)
    return prob_liq, out_class


def akhlagi_etal_2021_model_b(
    pgv: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    dc: Union[float, np.ndarray],
    dr: Union[float, np.ndarray],
    zwb: Union[float, np.ndarray],
    intercept: float = 9.504,
    pgv_coeff: float = 0.706,
    vs30_coeff: float = -0.994,
    dc_coeff: float = -0.389,
    dr_coeff: float = -0.291,
    zwb_coeff: float = -0.205,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of the Akhlagi et al., 2021 model B.
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.4
    (see p.13 from Zhu et al., 2017).

    Reference: Akhlaghi, A., Baise, L. G., Moaveni, B., Chansky, A. A.,
    & Meyer, M. (2021). An Update to the Global Geospatial Liquefaction
    Model With Uncertainty Propagation. SSA Annual Meeting Abstracts (p. 162).
    Seismological Society of America.
    Model parameters described in: Baise, L. G., Akhlaghi, A., Chansky, A.,
    Meyer, M., & Moeveni, B. (2021). USGS Award #G20AP00029. Updating the
    Geospatial Liquefaction Database and Model.
    Tufts University. Medford, Massachusetts, United States.

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site, measured in m/s
    :param dc:
        Distance to the nearest coast, measured in m
    :param dr:
        Distance to the nearest river, measured in m
    :param zwb:
        Elevation above the nearest water body, measured in m

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
    """

    Xg = (
        pgv_coeff * np.log(pgv)
        + vs30_coeff * np.log(vs30)
        + dc_coeff * np.log(dc + 1)
        + dr_coeff * np.log(dr + 1)
        + zwb_coeff * np.sqrt(zwb)
        + intercept
    )
    prob_liq = sigmoid(Xg)
    out_class = np.where(prob_liq > 0.4, 1, 0)
    return prob_liq, out_class


def bozzoni_etal_2021_europe(
    pga: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    cti: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    intercept: float = -11.489,
    pgam_coeff: float = 3.864,
    cti_coeff: float = 2.328,
    vs30_coeff: float = -0.091,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of a site undergoing liquefaction using the
    logistic regression of Bozzoni et al., 2021. Optimal regression
    coefficients are associated with ADASYN sampling algorithm (AUC = 0.95).
    The optimal threshold probability value to convert the predicted
    probability into binary classification is 0.57 (see Table 4 from the
    Reference).

    Reference: Bozzoni, F., Bonì, R., Conca, D., Lai, C. G., Zuccolo,
    E., & Meisina, C. (2021).
    Megazonation of earthquake-induced soil liquefaction hazard in
    continental Europe.
    Bulletin of Earthquake Engineering, 19(10), 4059–4082.
    https://doi.org/10.1007/s10518-020-01008-6

    :param pga:
        Peak Ground Acceleration, measured in g
    :param mag:
        Magnitude of causative earthquake (moment or work scale)
    :param cti:
        Compound Topographic Index, a proxy for soil wetness.
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site.

    :returns:
        prob_liq: Probability of liquefaction at the site.
        out_class: Binary output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
    """
    pga_scale = pga * _idriss_magnitude_weighting_factor(mag)
    Xg = (
        pgam_coeff * np.log(pga_scale)
        + cti_coeff * cti
        + vs30_coeff * np.log(vs30)
        + intercept
    )
    prob_liq = sigmoid(Xg)
    out_class = np.where(prob_liq > 0.57, 1, 0)
    return prob_liq, out_class


def todorovic_silva_2022_nonparametric_general(
    pgv: Union[float, np.ndarray],
    vs30: Union[float, np.ndarray],
    dw: Union[float, np.ndarray],
    wtd: Union[float, np.ndarray],
    precip: Union[float, np.ndarray],
    session,
) -> Union[float, np.ndarray]:
    """
    Returns the binary class output (i.e, 0 or 1) which indicates liquefaction
    nonoccurrence or liquefaction occurrence as per Todorovic and Silva
    (2022). In addition, it returns the probability of belonging to a class 1,
    or liquefaction occurrence. The implemented model includes modifications
    from the version published in Todorovic and Silva (2022).

    Reference: Todorovic, L., Silva, V. (2022).
    A liquefaction occurrence model for regional analysis.
    Soil Dynamics and Earthquake Engineering, 161, 1–12.
    https://doi.org/10.1016/j.soildyn.2022.107430

    :param pgv:
        Peak Ground Velocity, measured in cm/s
    :param vs30:
        Shear-wave velocity averaged over the upper 30 m of the earth at the
        site, measured in m/s
    :param dw:
        Distance to the nearest water body, measured in km
    :param wtd:
        Global water table depth, measured in m
    :param precip:
        Mean annual precipitation, measured in mm
    :param session:
        A Pickable ONNX Runtime Inference Session with the trained model loaded

    :returns:
        out_class: output 0 or 1, i.e., liquefaction nonoccurrence
                   or liquefaction occurrence occurrence.
        out_prob: probability of belonging to class 1.
    """
    strain_proxy = pgv / (CM_PER_M * vs30)
    matrix = np.array([strain_proxy, dw, wtd, precip]).T
    results = session.run(None, {"X": matrix})
    out_class = results[0]
    out_prob = [p[1] for p in results[1]]
    return out_class, out_prob


def _hazus_magnitude_correction_factor(
    mag,
    m3_coeff: float = 0.0027,
    m2_coeff: float = -0.0267,
    m1_coeff: float = -0.2055,
    intercept=2.9188,
):
    """
    Corrects the liquefaction probabilty equations based on the magnitude
    of the causative earthquake.
    """
    return (m3_coeff * (mag**3) + m2_coeff * (mag**2) +
            m1_coeff * mag + intercept)


def _hazus_groundwater_correction_factor(
    groundwater_depth,
    gd_coeff: float = 0.022,
    intercept: float = 0.93,
    unit: str = "feet",
):
    """
    Correction for groundwater depth in FEET
    """
    if unit in ["meters", "m"]:
        groundwater_depth = groundwater_depth * FT_PER_M

    return gd_coeff * groundwater_depth + intercept


def _hazus_conditional_liquefaction_probability(
    pga,
    susceptibility_category,
    coeff_table=HAZUS_LIQUEFACTION_COND_PROB_PGA_TABLE,
):
    """
    Calculates the probility of liquefaction of a soil susceptibility category
    conditional on the value of PGA observed.
    """
    if isinstance(susceptibility_category, str):
        coeffs = coeff_table[susceptibility_category]
        liq_prob = coeffs[0] * pga - coeffs[1]
    else:
        coeffs = [coeff_table[susc_cat] for susc_cat in susceptibility_category]
        coeff_0 = np.array([c[0] for c in coeffs])
        coeff_1 = np.array([c[1] for c in coeffs])
        liq_prob = coeff_0 * pga - coeff_1

    # TODO: Refactor below using np.clip
    if np.isscalar(liq_prob):
        if liq_prob <= 0:
            liq_prob = 0.0
        elif liq_prob >= 1:
            liq_prob = 1.0
        else:
            liq_prob = liq_prob
    else:
        liq_prob = liq_prob
        liq_prob[liq_prob < 0.0] = 0.0
        liq_prob[liq_prob > 1.0] = 1.0

    return liq_prob


def hazus_liquefaction_probability(
    pga: Union[float, np.ndarray],
    mag: Union[float, np.ndarray],
    liq_susc_cat: str,
    groundwater_depth: float = 1.524,
    do_map_proportion_correction: bool = True,
) -> Union[float, np.ndarray]:
    """
    Calculates the probability of liquefaction at a site based on the
    HAZUS methodology, which involves both earthquake and ground motion
    characteristics as well as a site characterization.

    For more information, see the HAZUS-MH MR5 Earthquake Model Technical
    Manual (https://www.hsdl.org/?view&did=12760), section 4-21.

    :param pga:
        Peak Ground Acceleration, measured in g
    :param mag:
        Magnitude of causative earthquake (moment or work scale)
    :param liq_susc_cat:
        Liquefaction susceptibility category (LSC). This is a category denoting
        the susceptibility of a site to liquefaction, independent of the
        ground motions or earthquake magnitude. Acceptable values are:
            `vh`: Very high
            `h` : High
            `m` : Medium
            `l` : Low
            `vl`: Very low
            `n` : No suceptibility.
    :param groundwater_depth:
        Depth to the groundwater from the earth surface in meters (note
        that the HAZUS methods call for this depth in feet; a conversion
        is automatically applied).
    :param do_map_proportion_correction:
        Flag to apply an additional LSC-based probability or coefficent to
        the conditional probability. This is part of the HAZUS methodology
        but it is unclear whether this is applicable for point-based site
        analysis, or how to compare this to other liquefaction models.
        Defaults to `True` following the HAZUS methods.
    """
    groundwater_corr = _hazus_groundwater_correction_factor(
        groundwater_depth, unit="m")
    mag_corr = _hazus_magnitude_correction_factor(mag)

    if isinstance(liq_susc_cat, str):
        liq_susc_prob = _hazus_conditional_liquefaction_probability(
            pga, liq_susc_cat)
        if do_map_proportion_correction:
            map_unit_proportion = HAZUS_LIQUEFACTION_MAP_AREA_PROPORTION_TABLE[
                liq_susc_cat
            ]
        else:
            map_unit_proportion = 1.0
    else:
        liq_susc_prob = _hazus_conditional_liquefaction_probability(
            pga, liq_susc_cat)

        if do_map_proportion_correction:
            map_unit_proportion = np.array(
                [
                    HAZUS_LIQUEFACTION_MAP_AREA_PROPORTION_TABLE[lsc]
                    for lsc in liq_susc_cat
                ]
            )
        else:
            map_unit_proportion = 1.0

    return liq_susc_prob * map_unit_proportion / (groundwater_corr * mag_corr)
