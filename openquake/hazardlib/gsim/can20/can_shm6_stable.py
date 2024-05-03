#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6th Generation Seismic Hazard Model of Canada (CanadaSHM6) Stable Crust GMMs.
The final documentation for the GMMs is being prepared. The GMMs are subject
to change up until the release of the documentation.
Preliminary documentation is available in:
Kolaj, M., Halchuk, S., Adams, J., Allen, T.I. (2020): Sixth Generation Seismic
Hazard Model of Canada: input files to produce values proposed for the 2020
National Building Code of Canada; Geological Survey of Canada, Open File 8630,
2020, 15 pages, https://doi.org/10.4095/327322
Kolaj, M., Adams, J., Halchuk, S (2020): The 6th Generation seismic hazard
model of Canada. 17th World Conference on Earthquake Engineering, Sendai,
Japan. Paper 1c-0028.
Kolaj, M., Allen, T., Mayfield, R., Adams, J., Halchuk, S (2019): Ground-motion
models for the 6th Generation Seismic Hazard Model of Canada. 12th Canadian
Conference on Earthquake Engineering, Quebec City, Canada.
"""
import os
import numpy as np
import pandas as pd
import openquake.hazardlib.gsim.atkinson_boore_2006 as AB06
from scipy import interpolate
from openquake.hazardlib import const
from openquake.hazardlib.const import StdDev
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib.gsim.can20.can_shm6_active_crust import _check_imts
from openquake.hazardlib.gsim.gmpe_table import _get_mean, _get_stddev
from openquake.hazardlib.gsim.boore_atkinson_2008 import \
    BooreAtkinson2008 as BA08

dirname = os.path.abspath(os.path.dirname(__file__))
BASE_PATH_AA13 = os.path.join(dirname, 'AA13')
BASE_PATH_NGAE = os.path.join(dirname, 'NGA-East-13')

# from Atkinson and Adams, 2013 with NBC 2015 modifications
COEFFS_2000_to_BC_AA13 = CoeffsTable(sa_damping=5, table="""\
IMT     c
pgv 1.23
pga  0.891
0.05 0.794
0.1 1.072
0.2 1.318
0.3 1.38
0.5 1.38
1.0 1.288
2.0 1.230
5.0 1.148
10.0 1.072
""")


def _defined_imts_aa13():
    imts = [SA(10.0), SA(5.0), SA(2.0), SA(1.0), SA(0.5), SA(0.3), SA(0.2),
            SA(0.1), SA(0.05), PGA(), PGV()]
    return imts


def site_term_aa13(self, mag, ctx, dists, imt):
    """
    Site amplification relative to Vs30 = 450 m/s following the approach
    adopted to derive the NBC 2015 foundation factors:
    """
    # Get the distance type
    dst = getattr(ctx, self.distance_type)

    # imls_pga = self._return_tables(rctx.mag, PGA(), "IMLs")
    imls_pga = self.mean_table['%.2f' % mag, 'PGA']
    PGA450 = _get_mean(self.kind, imls_pga, dst, dists)  # in units of g
    imls_SA02 = self.mean_table['%.2f' % mag, 'SA(0.2)']
    SA02 = _get_mean(self.kind, imls_SA02, dst, dists)

    # Correction to reduce non-linear term for eastern Canada
    PGA450[SA02 / PGA450 < 2.0] = PGA450[SA02 / PGA450 < 2.0] * 0.8

    # PGA at 450 corrected to 760 following approach used in NBC 2015
    pgas = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    pga_cors = np.array([0.083, 0.165, 0.248, 0.331, 0.414])
    PGA760 = np.interp(PGA450, pgas, pga_cors)
    PGA760_ref = np.copy(PGA760)
    PGA760_ref[ctx.vs30 > 450.] = 0.1  # fixed PGA of 0.1g used for > 450

    # normalize site term by prediction at 450 m/s
    vs30ref = np.zeros_like(ctx.vs30)
    vs30ref += 450.0
    site_term = (AB06_BA08_aa13(ctx.vs30, imt, PGA760_ref) /
                 AB06_BA08_aa13(vs30ref, imt, PGA760_ref))

    return np.log(site_term)


def AB06_BA08_aa13(vs30, imt, PGA760):
    """
    Site amplification relative to 760 m/s where the term is derived from:
    Vs30 < 760: Boore and Atkison 2008 (relative to 450 m/s)
    Vs30 >= 760: log-log interpolatation of the 760-2000 AA13 / AB06 factor
    """

    AB06_BA08 = np.zeros_like(vs30)

    # log interpolation of 760-2000 factor of AA13 for Vs30 >= 760
    C = COEFFS_2000_to_BC_AA13[imt]
    AB06_BA08[vs30 >= 760.] = 10**(np.interp(np.log10(vs30[vs30 >= 760.]),
                                   np.log10([760.0, 2000.0]),
                                   np.log10([1.0, C['c']])))
    AB06_BA08[vs30 >= 760.] = 1./AB06_BA08[vs30 >= 760.]

    # BA08 for Vs30 < 760
    C2 = BA08.COEFFS_SOIL_RESPONSE[imt]
    nl = AB06._get_site_amplification_non_linear(
        vs30[vs30 < 760.], PGA760[vs30 < 760.], C2)
    lin = AB06._get_site_amplification_linear(vs30[vs30 < 760.], C2)
    AB06_BA08[vs30 < 760.] = np.exp(nl + lin)

    return AB06_BA08


class CanadaSHM6_StableCrust_AA13(GMPETable):
    """
    Implementation of the Atkinson and Adams, 2013 representative suite of
    GMMs for CanadaSHM6 (low, central and high branch).
    Site amplification follows that of what was used to derive the NBC 2015
    foundation factors (but as a continous function wrt. to Vs30 rather than
                        discretized step-wise by Site Class.
    References:
        See header in can_shm6_stable.py
        Atkinson, GM, Adams, J (2013): Ground motion prediction equations
        for application to the 2015 Canadian national seismic hazard maps,
        Can. J. Civ. Eng., 40, 988–998, doi: 10.1139/cjce-2012-0544.
    """
    AA13_TABLE = ""
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Stable Shallow Crust"
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    REQUIRES_DISTANCES = {'rhypo'}
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    def __init__(self, submodel):
        """
        submodel is one of: "low", "central" or "high"
        """
        fname = os.path.join(BASE_PATH_AA13, f'ENA_{submodel}_cl450.hdf5')
        super().__init__(fname)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations
        """
        # Check input imts
        _check_imts(imts)
        # Magnitudes
        [mag] = np.unique(np.round(ctx.mag, 2))

        # Get distance vector for the given magnitude
        idx = np.searchsorted(self.m_w, mag)
        dists = self.distances[:, 0, idx - 1]
        dst = getattr(ctx, self.distance_type)

        # Compute mean and stddevs
        for m, imt in enumerate(imts):
            key = ('%.2f' % mag, imt.string)
            imls = self.mean_table[key]
            # Compute mean on reference conditions
            mean[m] = np.log(_get_mean(self.kind, imls, dst, dists))

            # Correct PGV to units of cm/s (tables for PGV are scaled
            # by a factor of g in cm/s)

            if imt == PGV():
                mean[m] = mean[m] - np.log(9.81)

            # Add site-term
            mean[m] += site_term_aa13(self, mag, ctx, dists, imt)

            # Get standard deviations
            sig[m] = _get_stddev(self.sig_table[key], dst, dists, imt)

# =============================================================================
# =============================================================================


def site_term_NGAE(self, ctx, mag, dists, imt, stddev_types):
    """
    Site amplification relative to Vs30 = 3000 m/s following the approach
    adopted for eastern Canada in CanadaSHM6:
    Model H. Harmon et al., (2019) L1 (linear) model with the USGS CEUS
                2019 non-linear term.
    Model B. 3000 > Vs30 > 2000: Boore and Campbell (2017)
                2000 > Vs30 > 760: 2000-760 Atkinson and Adams (2013) factor
                760 > Vs30: Boore and Atkinson (2008)
    For Sa(T) site amplification model is the larger of Model H and B.
    For PGA and PGV it follows Model B.
    """
    dst = getattr(ctx, self.distance_type)
    imls_pga = self.mean_table['%.2f' % mag, 'PGA']
    PGArock = _get_mean(self.kind, imls_pga, dst, dists)

    # site term from Model B.

    B = BA08_BC17(self, imt, PGArock, ctx)

    # site term from Model H.
    if imt != PGA() and imt != PGV():
        lin = _Hea19_L1_linear(self,imt, ctx.vs30)
        nl = _Fnl_USGS(self, imt, ctx.vs30, PGArock)
        H = lin + nl
    else:
        H = [-999.]*len(B)

    # return the larger of Models H and B
    return np.max([H, B], axis=0)


def _Hea19_L1_linear(self, imt, vs30):
    """
    L1 (linear) model of Harmon et al., 2019:
    Harmon, J., Hashash, Y. M. A., Stewart, J. P., Rathje, E. M., Campbell,
    K. W., Silva, W. J., and Ilhan, O.,2019b. Site Amplification Functions
    for Central and Eastern North America - Part II: Model Development and
    Evaluation, Earthquake Spectra.
    """

    C = self.COEFFS_HarmonL1[imt]

    F = np.zeros_like(vs30)

    F[C['Vc'] <= vs30] = 0.0

    F[(C['VL'] < vs30) & (vs30 < C['Vc'])] = (
        C['c1'] * np.log(vs30[(C['VL'] < vs30) & (vs30 < C['Vc'])]/C['Vc']))

    F[vs30 <= C['VL']] = (
            (C['c1'] * np.log(vs30[vs30 <= C['VL']] / C['Vc']))
            + (C['c2'] * np.log(vs30[vs30 <= C['VL']] / C['VL']))
            + (C['c3'] * (np.log(vs30[vs30 <= C['VL']] / C['VL']))**2.))

    return F


def _Fnl_USGS(self, imt, vs30, PGArock):
    """
    Non-linear amplification term used by the USGS for the CEUS 2019 NSHM
    as documented in:
        Petersen, MD, Shumway AM, Powers, PM, Mueller, CS, Moschetti, MP,
        Frankel, AD, Rezaeian, S, McNamara, DE, Hoover, SM, Luco, N, Boyd,
        OS, Rukstales, KS, Jaiswal, KS, Thompson, EM, Clayton, B, Field,
        EH, Zeng, Y (2018): Preliminary 2018 Update of the U.S. National
        Seismic Hazard Model: Overview of Model, Changes, and Implications,
        USGS report for public comment, 1-47.
        Hashash, Y. M. A., Ilhan, O., Harmon, J. A., Parker, G. A.,
        Stewart, J. P. Rathje, E. M., Campbell, K. W., and Silva, W. J.
        (2019) "Nonlinear site amplification model for ergodic seismic
        hazard analysis in Central and Eastern North America", Earthquake
        Spectra.
    """
    Fnl = np.zeros_like(vs30)
    C = self.COEFFS_NGA_USGS[imt]
    idx_ltVc = tuple([vs30 < C['Vc']])
    vs_ltVc = np.copy(vs30[idx_ltVc])

    if imt.period >= 0.4:
        vRefNl = 3000.0
    else:
        vRefNl = 760.0

    vs_ltVc[vs_ltVc > vRefNl] = vRefNl
    f2 = C['f4'] * (np.exp(C['f5']*(vs_ltVc - 360.0))
                    - np.exp(C['f5'] * (vRefNl - 360.0)))
    Fnl[idx_ltVc] = f2 * np.log((PGArock[idx_ltVc] + C['f3']) / C['f3'])

    return Fnl


def BA08_BC17(self, imt, PGArock, ctx):
    """
    Site amplification relative to Vs30 = 3000 m/s following:
    3000 > Vs30 > 2000: Boore and Campbell (2017)
    2000 > Vs30 > 760: 2000-760 Atkinson and Adams (2013) factor
    760 > Vs30: Boore and Atkinson (2008)
    References:
        See header in CanadaSHM6_StableCrust.py
        Atkinson, GM, Adams, J (2013): Ground motion prediction equations
        for application to the 2015 Canadian national seismic hazard maps,
        Can. J. Civ. Eng., 40, 988–998, doi: 10.1139/cjce-2012-0544.
        Boore, DM, Atkinson, GM (2008): Ground-motion prediction equations
        for the average horizontal component of PGA, PGV, and 5%-damped
        PSA at spectral periods between 0.01 s and 10.0 s, Earthq.
        Spectra, 24(1), 99–138,
        Boore, DM, Campbell, KW (2017): Adjusting central and eastern
        North America ground-motion intensity measures between sites with
        different reference-rock site conditions, Bull.Seism. Soc. Am.,
        107(1), 132–148
    """
    vs30 = ctx.vs30
    log_vs30 = np.log(vs30)
    F = np.zeros_like(vs30)
    
    # Get indices for various Vs30 ranges
    lte760 = vs30 <= 760.
    lt3000 = vs30 < 3000.
    lt3000gt2000 = (vs30 < 3000.) & (vs30 > 2000.)
    lt2000gt760 = (vs30 < 2000.) & (vs30 > 760.)
    vs = vs30[lt3000]
    vs_lte760 = vs <= 760
    vs_lt2000gt760 = (vs < 2000.) & (vs > 760.)
    vs_gt2000 = vs > 2000.

    # Repi for AA13 factor
    Repi_from_Rrup(ctx, ctx.mag, 10.0)  # fixed depth of 10km

    # log amplification factors for various IMTs at 2000 and 760 m/s
    i = np.zeros(8, dtype=object)
    if imt.period == 0:  # PGA, SA(0) or PGV
        F_2000 = np.log(BC17_amp(self, imt, ctx.mag, ctx.rrup[lt3000]))
        i[[0, 1, 2, 4, 5, 6]] = [vs_gt2000, vs_gt2000, vs == 2000,
                                    vs_lt2000gt760, vs_lt2000gt760, vs_lte760]
    else:
        F_2000 = np.array([np.log(self.COEFFS_BC17[imt]['c'])])

    if imt != PGV() and imt.period < 0.025:
        F_760 = -0.690775 + 0.15*np.log(ctx.repi[lt3000])
        i[[3, 7]] = [vs_lt2000gt760, vs_lte760]
    else:
        F_760 = np.array([np.log(self.COEFFS_AB06[imt]['c'])])

    # add amplification for 3000 > Vs30 > 2000:
    F[lt3000gt2000] += interp(self, log_vs30[lt3000gt2000], np.log(2000.),
                                    np.log(3000.), F_2000[i[0]],
                                    np.zeros_like(F_2000[i[1]]))

    # add amplification for Vs30 = 2000:
    F[vs30 == 2000] = F_2000[i[2]]

    # add amplification for 2000 > Vs30 > 760:
    F[lt2000gt760] += interp(self, log_vs30[lt2000gt760], np.log(760.),
                                    np.log(2000.), F_760[i[3]]+F_2000[i[4]],
                                    F_2000[i[5]])

    # Add (partial) amplification for Vs30 < 760:
    F[lte760] += F_2000[i[6]] + F_760[i[7]]

    # remaining amplification for vs30 < 760:
    # calculate PGA at 760 by repeating above process just for PGA
    C_pga1 = BC17_amp(self, PGA(), ctx.mag, ctx.rrup[lte760])
    PGA2000 = PGArock[lte760] * C_pga1  # BC17

    # Apply distance dependent AA13 factor
    C_pga = 10**(-0.3 + 0.15*np.log10(ctx.repi[lte760]))
    PGA760 = PGA2000 * C_pga

    # BA08 using the corrected PGA
    AB06_gmpe = AB06.AtkinsonBoore2006()
    C = AB06_gmpe.COEFFS_SOIL_RESPONSE[imt]
    nl = AB06._get_site_amplification_non_linear(vs30[lte760], PGA760, C)
    lin = AB06._get_site_amplification_linear(vs30[lte760], C)
    F[lte760] += nl + lin

    return F


def interp(self, x, x0, x1, y0, y1):
    """
    Helper function for fast and simple 1D interpolation
    """

    return y0 + (x-x0)*((y1-y0)/(x1-x0))


def Repi_from_Rrup(ctx, mag, h):
    """
    Epicental distance (Repi) converted from the closest rupture distance
    (Rrup) following:
        Atkinson, G (2012): White paper on Proposed Ground-motion
        Prediction Equations (GMPEs) for 2015 National Seismic Hazard Maps.
        https://www.seismotoolbox.ca/GMPEtables2012/r12_GMPEs9b.pdf
    """
    W = 10**(-1.01 + 0.32*mag)
    W = 0.6*W
    Dtop = h - 0.5*W
    Ztor = np.where(Dtop > 0.0, Dtop, 0.0).max()

    L = 10**(-2.44 + 0.59*mag)
    L = 0.6*L
    fac = 0.3*L
    rrup_temp = np.copy(ctx.rrup)
    rrup_temp[rrup_temp < Ztor] = Ztor + 0.001

    ctx.repi = ((rrup_temp**2 - Ztor**2)**0.5) + fac


def BC17_amp(self, imt, ctx, dist):
    """
    Distance and magnitude dependent amplification factors to convert from
    3000 m/s to 2000 m/s for PGA and PGV following Boore and Campbell 2017.
    Boore, DM, Campbell, KW (2017): Adjusting central and eastern
    North America ground-motion intensity measures between sites with
    different reference-rock site conditions, Bull.Seism. Soc. Am.,
    107(1), 132–148
    """
    if imt == PGV():
        interpolant_mag = f_pgv
    elif imt.period == 0:
        interpolant_mag = f_pga

    # clip values outside of BC17 range
    rrup = dist.copy()
    rrup[rrup < 2.] = 2.
    rrup[rrup > 1200.] = 1200.
    # clip any values less than 3 to 3, 
    # and any values greater than 8 to 8
    mag = np.clip(ctx, 3., 8.)

    rrups = np.array([2., 2.49, 3.11, 3.88, 4.83, 6.03, 7.51, 9.37, 11.68,
                        14.56, 18.16, 22.64, 28.22, 35.19, 43.87, 54.7, 68.2,
                        85.04, 106.02, 132.19, 164.81, 205.49, 256.21,
                        319.44, 398.28, 496.58, 619.14, 771.94, 962.46,
                        1200.])
    BC17 = np.interp(rrup, rrups, pd.DataFrame(interpolant_mag(mag)).iloc[:,0])

    return np.array(BC17)


class CanadaSHM6_StableCrust_NGAEast(GMPETable):
    """
    6th Generation Seismic Hazard Model of Canada (CanadaSHM6) implementation
    of the 13 NGA-East Ground-Motion Models as described in PEER Report No.
    2017/03 with the following modifications:
            Added site-amplification term
            Sigma model from CanadaSHM6 / Atkinson and Adams, 2013
    Submodel is one of: "01", "02", "03", "04", "05", "06", "07", "08", "09",
                        "10", "11", "12", "13"
    Reference:
        See header in CanadaSHM6_StableCrust.py
        Goulet, CA, Bozorgnia, Y, Kuehn, N, Al Atik, L, Youngs, RR, Graves,
        RW, Atkinson, GM (2017): PEER 2017/03 -NGA-East ground-motion models
        for the U.S. Geological Survey National Seismic Hazard Maps, in PEER
        Report No. 2017/03.
    """
    
    NGA_EAST_TABLE = ""
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Stable Shallow Crust"
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    REQUIRES_DISTANCES = {'rhypo'}
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    def __init__(self, submodel):
        """
        Submodel is one of: "01", "02", "03", "04", "05", "06", "07", "08",
                            "09", "10", "11", "12", "13"
        """
        fname = f'SHM6-trial_NGA-East_Model_{submodel}_AA13_sigma.vs3000.hdf5'
        gmpe_table = os.path.join(BASE_PATH_NGAE, fname)
        super().__init__(gmpe_table)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Returns the mean and standard deviations
        """
        # Check input imts
        _check_imts(imts)

        # Magnitudes
        [mag] = np.unique(np.round(ctx.mag, 2))

        # Get distance vector for the given magnitude
        idx = np.searchsorted(self.m_w, mag)
        dists = self.distances[:, 0, idx - 1]
        dst = getattr(ctx, self.distance_type)

        # Compute mean and stddevs
        for m, imt in enumerate(imts):

            key = (f'{mag:.2f}', imt.string)
            imls = self.mean_table[key]

            # Compute mean on reference conditions
            mean[m] = np.log(_get_mean(self.kind, imls, ctx.rrup, dists))

            # Correct PGV to units of cm/s (tables for PGV are scaled
            # by a factor of g in cm/s)
            if imt == PGV():
                mean[m] = mean[m] - np.log(980.665)

            # Add amplification
            mean[m] += site_term_NGAE(self, ctx, mag, dists, imt,[StdDev.TOTAL])

            # Get standard deviations
            sig[m] = _get_stddev(self.sig_table[key], dst, dists, imt)


    COEFFS_NGA_USGS = CoeffsTable(sa_damping=5, table="""\
    imt  f760i  f760g  f760is  f760gs  c  V1  V2  Vf  sig_vc  sig_l  sig_u  f3  f4  f5  Vc  sig_c
    PGV  0.375  0.297  0.313  0.117  -0.449  331  760  314  0.251  0.306  0.334  0.06089  -0.08344  -0.00667  2257  0.12
    PGA  0.185  0.121  0.434  0.248  -0.29  319  760  345  0.3  0.345  0.48  0.0752  -0.43755  -0.00131  2990  0.12
    0.01  0.185  0.121  0.434  0.248  -0.29  319  760  345  0.3  0.345  0.48  0.0752  -0.43755  -0.00131  2990  0.12
    0.02  0.185  0.031  0.434  0.27  -0.303  319  760  343  0.29  0.336  0.479  0.0566  -0.41511  -0.00098  2990  0.12
    0.03  0.224  0  0.404  0.229  -0.315  319  810  342  0.282  0.327  0.478  0.1036  -0.49871  -0.00127  2990  0.12
    0.04  0.283  0.012  0.39  0.139  -0.331  319  900  340  0.275  0.317  0.477  0.11836  -0.48734  -0.00169  2990  0.12
    0.05  0.337  0.062  0.363  0.093  -0.344  319  1010  338  0.271  0.308  0.476  0.16781  -0.58073  -0.00187  2990  0.12
    0.075  0.475  0.211  0.322  0.102  -0.348  319  1380  334  0.269  0.285  0.473  0.17386  -0.53646  -0.00259  2990  0.12
    0.1  0.674  0.338  0.366  0.088  -0.372  317  1900  319  0.27  0.263  0.47  0.15083  -0.44661  -0.00335  2990  0.12
    0.15  0.586  0.47  0.253  0.066  -0.385  302  1500  317  0.261  0.284  0.402  0.14272  -0.38264  -0.0041  2335  0.12
    0.2  0.419  0.509  0.214  0.053  -0.403  279  1073  314  0.251  0.306  0.334  0.12815  -0.30481  -0.00488  1533  0.12
    0.25  0.332  0.509  0.177  0.052  -0.417  250  945  282  0.238  0.291  0.357  0.13286  -0.27506  -0.00564  1318  0.135
    0.3  0.27  0.498  0.131  0.055  -0.426  225  867  250  0.225  0.276  0.381  0.1307  -0.22825  -0.00655  1152  0.15
    0.4  0.209  0.473  0.112  0.06  -0.452  217  843  250  0.225  0.275  0.381  0.09414  -0.11591  -0.00872  1018  0.15
    0.5  0.175  0.447  0.105  0.067  -0.48  217  822  280  0.225  0.311  0.323  0.09888  -0.07793  -0.01028  939  0.15
    0.75  0.127  0.386  0.138  0.077  -0.51  227  814  280  0.225  0.33  0.31  0.06101  -0.0178  -0.01456  835  0.125
    1  0.095  0.344  0.124  0.078  -0.557  255  790  300  0.225  0.377  0.361  0.04367  -0.00478  -0.01823  951  0.06
    1.5  0.083  0.289  0.112  0.081  -0.574  276  805  300  0.242  0.405  0.375  0.0048  -0.00086  -0.02  882  0.05
    2  0.079  0.258  0.118  0.088  -0.584  296  810  300  0.259  0.413  0.388  0.00164  -0.00236  -0.01296  879  0.04
    3  0.073  0.233  0.111  0.1  -0.588  312  820  313  0.306  0.41  0.551  0.00746  -0.00626  -0.01043  894  0.04
    4  0.066  0.224  0.12  0.109  -0.579  321  821  322  0.34  0.405  0.585  0.00269  -0.00331  -0.01215  875  0.03
    5  0.064  0.22  0.108  0.115  -0.558  324  825  325  0.34  0.409  0.587  0.00242  -0.00256  -0.01325  856  0.02
    7.5  0.056  0.216  0.082  0.13  -0.544  325  820  328  0.345  0.42  0.594  0.04219  -0.00536  -0.01418  832  0.02
    10  0.053  0.218  0.069  0.137  -0.507  325  820  330  0.35  0.44  0.6  0.05329  -0.00631  -0.01403  837  0.02
            """)

    COEFFS_AB06 = CoeffsTable(sa_damping=5, table="""\
    IMT     c
    pgv 1.23
    pga  0.891
    0.05 0.791
    0.1 1.072
    0.2 1.318
    0.3 1.38
    0.5 1.38
    1.0 1.288
    2.0 1.230
    5.0 1.148
    10.0 1.072
    """)

    # Interpolated from Table 2 of Boore and Campbell, 2017
    COEFFS_BC17 = CoeffsTable(sa_damping=5, table="""\
    IMT     c
    0.01 1.28
    0.05 1.28
    0.1 1.27
    0.2 1.25
    0.3 1.21
    0.5 1.14
    1.0 1.06
    2.0 1.035
    5.0 1.015
    10.0 1.01
    """)

    COEFFS_HarmonL1 = CoeffsTable(sa_damping=5, table="""\
            imt 	c1	c2	c3	Vc	VL
            0.001	-0.73744	0	-0.32484	2990	1886.562
            0.006667	-0.7242	0	-0.32453	2990	1886.562
            0.008	-0.70976	0	-0.32336	2990	1886.562
            0.01	-0.66284	0	-0.32055	2990	1886.562
            0.010526	-0.64972	0	-0.32074	2990	1886.562
            0.011111	-0.64276	0	-0.32255	2990	1886.562
            0.011749	-0.63702	0	-0.32471	2990	1886.562
            0.0125	-0.63315	0	-0.32842	2990	1886.562
            0.014125	-0.62518	0	-0.34138	2990	1886.562
            0.016218	-0.61778	0	-0.35909	2990	1886.562
            0.018182	-0.62314	0	-0.37378	2990	1886.562
            0.02	-0.63091	0	-0.3888	2990	1886.562
            0.022	-0.64877	0	-0.40473	2990	1886.562
            0.025	-0.67716	0	-0.41949	2990	1886.562
            0.029	-0.70516	0	-0.42762	2990	1886.562
            0.03	-0.71514	0	-0.42861	2990	1886.562
            0.032	-0.73163	0	-0.43225	2990	1886.562
            0.035	-0.75478	0	-0.43681	2990	1886.562
            0.036	-0.76054	0	-0.43782	2990	1886.562
            0.04	-0.79496	0	-0.4417	2990	1886.562
            0.042	-0.80516	0	-0.44221	2990	1886.562
            0.044	-0.81765	0	-0.44491	2990	1886.562
            0.045	-0.82077	0	-0.4453	2990	1886.562
            0.046	-0.82745	0	-0.44618	2990	1886.562
            0.048	-0.8345	0	-0.445	2990	1886.562
            0.05	-0.84463	0	-0.44534	2990	1886.562
            0.055	-0.85863	0	-0.44359	2990	1886.562
            0.06	-0.8732	0	-0.44107	2990	1886.562
            0.065	-0.88504	0	-0.43629	2990	1886.562
            0.066667	-0.88873	0	-0.43489	2990	1886.562
            0.07	-0.89376	0	-0.43128	2990	1886.562
            0.075	-0.89876	0	-0.42455	2990	1886.562
            0.08	-0.89754	0	-0.41585	2990	1886.562
            0.085	-0.89761	0	-0.40874	2990	1886.562
            0.09	-0.89484	0	-0.40158	2990	1886.562
            0.095	-0.89393	0	-0.39442	2990	1886.562
            0.1	-0.89247	0	-0.3864	2990	1886.562
            0.11	-0.87647	0	-0.369	2990	1886.562
            0.12	-0.87333	0	-0.35647	2990	1886.562
            0.13	-0.86613	0	-0.34411	2990	1886.562
            0.133333	-0.86667	0	-0.34378	2946.224	1858.942
            0.14	-0.89255	0	-0.36886	2652.236	1673.448
            0.15	-0.92505	0	-0.40242	2335.376	1473.522
            0.16	-0.9646	0	-0.43721	2101.823	1326.16
            0.17	-1.00086	0	-0.47535	1902.382	1200.322
            0.18	-1.03212	0	-0.51107	1743.072	1099.804
            0.19	-1.05843	0	-0.54019	1632.377	1029.961
            0.2	-1.08972	0	-0.57208	1532.801	967.132
            0.22	-0.88714	-0.39561	-0.6372	1499.43	946.0764
            0.24	-1.18266	0	-0.66617	1245.266	785.71
            0.25	-0.91202	-0.44526	-0.69383	1317.97	831.583
            0.26	-0.90268	-0.48269	-0.713	1269.224	800.8264
            0.28	-0.88502	-0.56085	-0.74552	1201.712	758.2291
            0.29	-0.87666	-0.58807	-0.75476	1173.706	740.5582
            0.3	-0.86859	-0.60497	-0.7546	1151.791	726.731
            0.32	-0.85041	-0.60231	-0.77891	1130.924	655.6985
            0.34	-0.83333	-0.61199	-0.82509	1103.976	587.707
            0.35	-0.83681	-0.59111	-0.84488	1094.306	555.6097
            0.36	-0.81778	-0.62125	-0.84309	1089.194	546.2976
            0.38	-0.87585	-0.46472	-0.91823	1037.395	461.4881
            0.4	-0.85601	-0.51025	-0.98006	1018.069	428.9142
            0.42	-0.86948	-0.4592	-1.10747	989.6682	375.2397
            0.44	-0.85594	-0.50743	-1.20947	978.7148	349.8498
            0.45	-0.84909	-0.53993	-1.2592	969.7465	339.9384
            0.46	-0.83977	-0.58028	-1.28994	962.6836	334.6427
            0.48	-0.82134	-0.66129	-1.34916	952.583	324.3198
            0.5	-0.80884	-0.74172	-1.42513	938.516	313.912
            0.55	-0.77469	-0.89078	-1.58235	917.1113	289.5563
            0.6	-0.77838	-0.95332	-1.9226	882.9021	252.4941
            0.65	-0.76334	-0.95717	-1.85593	861.9838	242.9401
            0.666667	-0.75146	-0.9573	-1.78077	858.5831	241.9816
            0.7	-0.74494	-0.89501	-1.60135	848.844	239.2367
            0.75	-0.71858	-0.858	-1.40401	834.7709	235.2704
            0.8	-0.69679	-0.75896	-1.11873	832.4085	234.6046
            0.85	-0.56168	-0.54468	-0.54806	905.2938	304.7872
            0.9	-0.43429	-0.34266	-0.01002	974.0116	387.761
            0.95	-0.43429	-0.31383	0.010229	963.2368	478.7989
            1	-0.43429	-0.2853	0.026783	950.9678	465.5261
            1.1	-0.43429	-0.21209	0.074789	947.3805	443.8768
            1.2	-0.43429	-0.10124	0.155349	930.852	427.9618
            1.3	-0.43429	-0.01064	0.188612	913.1782	434.8641
            1.4	-0.43429	0	0.164929	886.7144	436.2375
            1.5	-0.43429	0	0.117398	882.2115	447.3806
            1.6	-0.43429	0	0.07195	878.6152	458.3723
            1.7	-0.43429	0	0.040183	876.271	469.4901
            1.8	-0.43429	0	0.014342	871.4213	478.7658
            1.9	-0.43429	0	-0.01067	872.7749	550.6837
            2	-0.43429	0	-0.02203	878.8883	554.5411
            2.2	-0.43429	0	-0.04813	889.3877	561.1657
            2.4	-0.43429	0	-0.06473	892.8143	563.3278
            2.5	-0.43429	0	-0.06824	891.8014	562.6886
            2.6	-0.43429	0	-0.07173	890.7799	562.0441
            2.8	-0.43429	0	-0.07621	891.8191	562.6998
            3	-0.43429	0	-0.07609	894.3879	564.3206
            3.2	-0.43429	0	-0.07931	890.849	562.0877
            3.4	-0.43429	0	-0.08228	888.8291	560.8133
            3.5	-0.43429	0	-0.08309	884.7668	558.2501
            3.6	-0.43429	0	-0.08327	883.0574	557.1716
            3.8	-0.43429	0	-0.08504	878.9371	554.5718
            4	-0.43429	0	-0.085	874.8681	552.0045
            4.2	-0.43429	0	-0.08434	869.9218	548.8836
            4.4	-0.43429	0	-0.08217	866.5324	546.745
            4.6	-0.43429	0	-0.08165	863.7773	545.0066
            4.8	-0.43429	0	-0.0808	861.8108	543.7659
            5	-0.43429	0	-0.08093	856.1077	540.1674
            5.5	-0.43429	0	-0.08107	847.146	534.513
            6	-0.43429	0	-0.08166	840.2302	530.1494
            6.5	-0.43429	0	-0.08095	836.9147	528.0575
            7	-0.43429	0	-0.08001	835.4604	527.1399
            7.5	-0.43429	0	-0.08091	831.6034	524.7063
            8	-0.43429	0	-0.08247	830.0349	523.7166
            8.5	-0.43429	0	-0.08301	831.4132	524.5863
            9	-0.43429	0	-0.08179	832.5597	525.3096
            9.5	-0.43429	0	-0.08053	833.8127	526.1003
            10	-0.43429	0	-0.07831	837.0494	528.1425
            """)

BC17_PGA = np.array([[1.2776, 1.275, 1.2685, 1.2608, 1.2548, 1.2495],
                    [1.2776, 1.275, 1.2684, 1.2609, 1.2548, 1.2495],
                    [1.2776, 1.275, 1.2684, 1.2608, 1.2548, 1.2493],
                    [1.2776, 1.275, 1.2683, 1.2607, 1.2546, 1.2493],
                    [1.2776, 1.275, 1.2682, 1.2606, 1.2545, 1.2493],
                    [1.2776, 1.2749, 1.268, 1.2604, 1.2544, 1.2492],
                    [1.2776, 1.2748, 1.2679, 1.2601, 1.2542, 1.2491],
                    [1.2776, 1.2747, 1.2676, 1.2598, 1.2539, 1.2488],
                    [1.2776, 1.2746, 1.2674, 1.2592, 1.2535, 1.2485],
                    [1.2775, 1.2745, 1.2669, 1.2586, 1.2528, 1.248],
                    [1.2775, 1.2744, 1.2664, 1.2577, 1.2519, 1.2473],
                    [1.2775, 1.2741, 1.2657, 1.2566, 1.2508, 1.2462],
                    [1.2775, 1.2738, 1.2649, 1.2553, 1.2492, 1.2448],
                    [1.2775, 1.2735, 1.2639, 1.2535, 1.2467, 1.2428],
                    [1.2774, 1.2731, 1.2626, 1.2513, 1.2442, 1.2399],
                    [1.2772, 1.2725, 1.261, 1.2483, 1.2405, 1.2362],
                    [1.2771, 1.2718, 1.2588, 1.2445, 1.2359, 1.2312],
                    [1.2769, 1.2708, 1.256, 1.2396, 1.2298, 1.2249],
                    [1.2765, 1.2695, 1.2523, 1.2334, 1.222, 1.2163],
                    [1.2762, 1.2677, 1.2476, 1.2254, 1.212, 1.2058],
                    [1.2755, 1.2653, 1.2417, 1.2157, 1.1998, 1.1925],
                    [1.2746, 1.2621, 1.2342, 1.2038, 1.185, 1.1762],
                    [1.273, 1.2577, 1.2249, 1.1897, 1.168, 1.1574],
                    [1.2707, 1.252, 1.2136, 1.1734, 1.1488, 1.1369],
                    [1.267, 1.2444, 1.2002, 1.1553, 1.1283, 1.1153],
                    [1.261, 1.2344, 1.1846, 1.1362, 1.1076, 1.0939],
                    [1.2518, 1.2214, 1.1671, 1.1168, 1.0879, 1.074],
                    [1.2372, 1.2046, 1.148, 1.0981, 1.0699, 1.0565],
                    [1.2158, 1.1834, 1.1278, 1.0807, 1.0544, 1.0421],
                    [1.186, 1.1577, 1.1074, 1.0652, 1.0417, 1.0307]])

# same as above but for PGV
BC17_PGV = np.array([[1.2722, 1.2482, 1.188, 1.1161, 1.0664, 1.0395],
                    [1.2721, 1.2481, 1.1878, 1.116, 1.0664, 1.0395],
                    [1.2721, 1.2479, 1.1874, 1.1159, 1.0664, 1.0395],
                    [1.272, 1.2477, 1.1871, 1.1157, 1.0663, 1.0395],
                    [1.272, 1.2475, 1.1868, 1.1155, 1.0663, 1.0395],
                    [1.272, 1.2472, 1.1863, 1.1152, 1.0662, 1.0394],
                    [1.2719, 1.2469, 1.1857, 1.1147, 1.0661, 1.0394],
                    [1.2717, 1.2465, 1.185, 1.1142, 1.0657, 1.0393],
                    [1.2716, 1.2461, 1.1842, 1.1134, 1.065, 1.0391],
                    [1.2714, 1.2456, 1.1832, 1.1124, 1.0643, 1.039],
                    [1.2712, 1.2447, 1.1813, 1.1104, 1.0634, 1.0387],
                    [1.2709, 1.2439, 1.1796, 1.1084, 1.0622, 1.0383],
                    [1.2705, 1.2429, 1.1778, 1.1065, 1.061, 1.0378],
                    [1.2701, 1.2417, 1.1758, 1.1045, 1.0597, 1.0373],
                    [1.2696, 1.2404, 1.1737, 1.1025, 1.0583, 1.0366],
                    [1.2689, 1.2387, 1.1712, 1.1003, 1.057, 1.0361],
                    [1.2679, 1.2366, 1.1683, 1.098, 1.0557, 1.0355],
                    [1.2667, 1.2341, 1.1649, 1.0953, 1.0541, 1.0347],
                    [1.2651, 1.2308, 1.1608, 1.0922, 1.0523, 1.0337],
                    [1.2628, 1.2269, 1.156, 1.0884, 1.05, 1.0324],
                    [1.2597, 1.2217, 1.1502, 1.0841, 1.0473, 1.0307],
                    [1.2554, 1.2155, 1.1433, 1.0791, 1.0442, 1.0287],
                    [1.2495, 1.2076, 1.1353, 1.0735, 1.0406, 1.0262],
                    [1.2411, 1.1977, 1.1264, 1.0674, 1.0366, 1.0233],
                    [1.2293, 1.1856, 1.1164, 1.0609, 1.0325, 1.0202],
                    [1.2131, 1.1709, 1.1051, 1.0543, 1.0283, 1.017],
                    [1.1916, 1.153, 1.0934, 1.0476, 1.0242, 1.0141],
                    [1.1645, 1.1325, 1.081, 1.0412, 1.0205, 1.0114],
                    [1.1333, 1.1097, 1.0685, 1.035, 1.0173, 1.0092],
                    [1.1011, 1.0862, 1.0561, 1.0293, 1.0144, 1.0074]])

# helper functions to interpolate BC17 factors accross magnitude
f_pga = interpolate.interp1d(np.array([3., 4., 5., 6., 7., 8.]),
                                BC17_PGA, axis=1)
f_pgv = interpolate.interp1d(np.array([3., 4., 5., 6., 7., 8.]),
                                BC17_PGV, axis=1)
