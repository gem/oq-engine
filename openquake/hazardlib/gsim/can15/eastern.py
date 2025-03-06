"""
:module:`openquake.hazardlib.gsim.nrcan15` implements
:class:`EasternCan15Mid`, :class:`EasterCnan15Low`,
:class:`EasternCan15Upp`
"""
import numpy as np

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.can15 import utils
from openquake.hazardlib.gsim.can15.western import get_sigma
from openquake.hazardlib import contexts
from openquake.hazardlib.imt import PGA, SA
from openquake.hazardlib.const import StdDev, IMC, TRT
from openquake.hazardlib.gsim.pezeshk_2011 import PezeshkEtAl2011
from openquake.hazardlib.gsim.boore_atkinson_2011 import Atkinson2008prime
from openquake.hazardlib.gsim.atkinson_boore_2006 import \
    AtkinsonBoore2006Modified2011
from openquake.hazardlib.gsim.silva_2002 import (
    SilvaEtAl2002SingleCornerSaturation, SilvaEtAl2002DoubleCornerSaturation)


def _get_delta(stds, repi):
    """
    Computes the additional delta to be used for the computation of the
    upp and low models
    """
    return np.fmax(0.1 - 0.001 * repi, 0.)


def apply_correction_to_BC(cff, mean, imt, repi):
    if imt.period:
        tmp = cff['mf']
    elif imt in [PGA()]:
        tmp = -0.3 + 0.15 * np.log10(repi)
    else:
        raise ValueError('Unsupported IMT', imt.string)
    return mean + np.log(10**tmp)


class EasternCan15Mid(GMPE):
    """
    Implements the hybrid GMPE used to compute hazard in the Eastern part of
    Canada.

    The GMPEs used are:

    - Pezeshk et al. (2011) - For this GMPE we scale the ground motion from
    hard rock to B/C using the correction proposed in Atkinson and Adams (2013)
    Table 2 page 994. As the distance metric used is Rrup we compute an
    equivalent Rrup distance from Repi using the equations in Appendix A (page
    31) of Atkinson (2012).

    - Atkinson (2008) as revised in Atkinson and Boore (2011). As the distance
    metric used is Rjb we compute an equivalent Rjb distance from Repi
    using the equations in Appendix A (page 31) of Atkinson (2012).

    - Atkinson and Boore (2006) as revised in Atkinson and Boore (2011). As
    the distance metric used is Rjb we compute an equivalent Rjb distance
    from Repi using the equations in Appendix A (page 31) of Atkinson (2012).

    - Silva et al. (2002) single corner and saturation.

    - Silva et al. (2002) double corner and saturation.
    """

    #: GMPE not tested against independent implementation so raise
    #: not verified warning
    non_verified = True

    #: Supported tectonic region type is 'stable continental region'
    #: equation has been derived from data from Eastern North America (ENA)
    # 'Instroduction', page 1859.
    DEFINED_FOR_TECTONIC_REGION_TYPE = TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration. See Table 2 in page 1865
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}

    #: Geometric mean determined from the fiftieth percentile values of the
    #: geometric means computed for all nonredundant rotation angles and all
    #: periods less than the maximum useable period, independent of
    #: sensor orientation. See page 1864.
    #: :attr:'~openquake.hazardlib.const.IMC.GMRotI50'.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = IMC.GMRotI50

    #: Required rupture parameters are magnitude (eq. 4, page 1866).
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is RRup, explained in page 1864 (eq. 2 page
    #: 1861, eq. 5 page 1866).
    REQUIRES_DISTANCES = {'rrup'}

    #: Required site parameters
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: Required distance is only repi since rrup and rjb are obtained from repi
    REQUIRES_DISTANCES = {'repi'}

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag'}

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    #: Standard deviation types supported
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {StdDev.TOTAL}

    gsims = [PezeshkEtAl2011(), Atkinson2008prime(),
             SilvaEtAl2002SingleCornerSaturation(),
             SilvaEtAl2002DoubleCornerSaturation(),
             AtkinsonBoore2006Modified2011()]
    sgn = 0

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See documentation for method `GroundShakingIntensityModel` in
        :class:~`openquake.hazardlib.gsim.base.GSIM`
        """
        mean_stds = []  # 5 arrays of shape (4, M, N)
        for gsim in self.gsims:
            # add equivalent distances
            if isinstance(gsim, AtkinsonBoore2006Modified2011):
                c = utils.add_distances_east(ctx, ab06=True)
            else:
                c = utils.add_distances_east(ctx)
            mean_stds.append(contexts.get_mean_stds(gsim, c, imts))

        for m, imt in enumerate(imts):
            cff = None if imt.period == 0 else self.COEFFS_SITE[imt]

            # Pezeshk et al. 2011 - Rrup
            mean1, stds1 = mean_stds[0][:2, m]
            mean1 = apply_correction_to_BC(cff, mean1, imt, ctx.repi)

            # Atkinson 2008 - Rjb
            mean2, stds2 = mean_stds[1][:2, m]

            # Silva single corner
            mean4, stds4 = mean_stds[2][:2, m]
            mean4 = apply_correction_to_BC(cff, mean4, imt, ctx.repi)

            # Silva double corner
            mean5, stds5 = mean_stds[3][:2, m]
            mean5 = apply_correction_to_BC(cff, mean5, imt, ctx.repi)

            # Atkinson and Boore 2006 - Rrup
            mean3, stds3 = mean_stds[4][:2, m]

            # Computing adjusted mean and stds
            mean[m] = mean1*0.2 + mean2*0.2 + mean3*0.2 + mean4*0.2 + mean5*0.2

            # Note that in this case we do not apply a triangular smoothing on
            # distance as explained at page 996 of Atkinson and Adams (2013)
            # for the calculation of the standard deviation
            stds = np.log(np.exp(stds1) * 0.2 + np.exp(stds2) * 0.2 +
                          np.exp(stds3) * 0.2 + np.exp(stds4) * 0.2 +
                          np.exp(stds5) * 0.2)
            sig[m] = get_sigma(imt)
            if self.sgn:
                mean[m] += self.sgn * (stds + _get_delta(stds, ctx.repi))

    COEFFS_SITE = CoeffsTable(sa_damping=5, table="""\
    IMT        mf
    0.05    -0.10
    0.10     0.03
    0.20     0.12
    0.33     0.14
    0.50     0.14
    1.00     0.11
    2.00     0.09
    5.00     0.06
    """)


class EasternCan15Low(EasternCan15Mid):
    sgn = -1


class EasternCan15Upp(EasternCan15Mid):
    sgn = +1
