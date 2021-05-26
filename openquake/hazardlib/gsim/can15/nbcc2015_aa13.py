#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module exports :class:`NBCC2015_AA13`
"""
import io
import os
import numpy as np
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.base import gsim_aliases
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008

dirname = os.path.dirname(__file__)
BASE_PATH_AA13 = os.path.join(dirname, 'nbcc2015_tables')

# populating `gsim_aliases` so that the engine can associate a string
# to a specific gsim; for instance the string "NBCC2015_AA13_offshore_high"
# is associated to the gsim (in TOML representation)
# [NBCC2015_AA13]
# REQUIRES_DISTANCES = ["rhypo"]
# DEFINED_FOR_TECTONIC_REGION_TYPE = "Offshore"
# gmpe_table = "Woffshore_high_clC.hdf5"
arguments = [
    ['stablecrust', 'rhypo', 'Stable Crust', 'ENA_%s_clC'],
    ['activecrust', 'rhypo', 'Active Crust', 'Wcrust_%s_clC'],
    ['activecrustFRjb', 'rjb', 'Active Crust Fault', 'WcrustFRjb_%s_clC'],
    ['inslab30', 'rhypo', 'Subduction Inslab 30', 'WinslabD30_%s_clC'],
    ['inslab50', 'rhypo', 'Subduction Inslab 50', 'WinslabD50_%s_clC'],
    ['interface', 'rrup', 'Subduction Interface', 'WinterfaceCombo_%sclC'],
    ['offshore', 'rhypo', 'Offshore', 'Woffshore_%s_clC']]
for key, dist, trt, hdf5 in arguments:
    for kind in ('low', 'med', 'high'):
        name = f"NBCC2015_AA13_{key}_" + ("central" if kind == "med" else kind)
        gsim_aliases[name] = f'''[NBCC2015_AA13]
REQUIRES_DISTANCES = ["{dist}"]
DEFINED_FOR_TECTONIC_REGION_TYPE = "{trt}"
gmpe_table = "{hdf5}.hdf5"
''' % kind


class NBCC2015_AA13(GMPETable):
    """
    Implements the GMMs of the 5th Generation seismic hazard model of Canada
    as used in the 2015 National Building Code of Canada (NBCC2015).

    The  GMMs are described in Atkinson and Adams (2013):
    Atkinson, GM, Adams, J (2013): Ground motion prediction equations for
    application to the 2015 Canadian national seismic hazard maps,
    Can. J. Civ. Eng., 40, 988–998, doi: 10.1139/cjce-2012-0544. Note that
    however some additional modifications were made for NBCC2015.

    For NBCC2015, hazard was calculated only at site class C (Vs30 = 450 m/s).
    To allow calculation of the GMM at other Vs30s, a site term has been added.
    The terms derivation is equivalent to the site coefficient term (F(T))
    (but as a continous function of Vs30) as used in NBCC2015 to scale Site
    Class C hazard to other site classes.

    Openquake implementation is based off of the Openquake nga_east seed model:
    https://docs.openquake.org/oq-engine/3.0/_modules/openquake/hazardlib/
    gsim/nga_east.html
    """
    experimental = True
    gmpe_table = ""
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {const.StdDev.TOTAL}
    REQUIRES_SITES_PARAMETERS = {'vs30'}
    REQUIRES_DISTANCES = ""
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}
    BA08 = BooreAtkinson2008()

    def __init__(self, **kwargs):
        # kwargs must contain the keys REQUIRES_DISTANCES,
        # DEFINED_FOR_TECTONIC_REGION_TYPE, gmpe_table
        fname = kwargs['gmpe_table']
        if isinstance(fname, io.BytesIO):
            # magic happening in the engine when reading the gsim from HDF5
            pass
        else:
            # fname is really a filename (absolute in the engine)
            kwargs['gmpe_table'] = os.path.join(
                BASE_PATH_AA13, os.path.basename(fname))
        super().__init__(**kwargs)
        self.REQUIRES_DISTANCES = frozenset(kwargs['REQUIRES_DISTANCES'])
        self.DEFINED_FOR_TECTONIC_REGION_TYPE = kwargs[
            'DEFINED_FOR_TECTONIC_REGION_TYPE']

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        # Return Distance Tables
        imls = self._return_tables(rctx.mag, imt, "IMLs")
        # Get distance vector for the given magnitude
        idx = np.searchsorted(self.m_w, rctx.mag)
        dists = self.distances[:, 0, idx - 1]
        # Get mean and standard deviations
        mean = np.log(self._get_mean(imls, dctx, dists))
        stddevs = self._get_stddevs(dists, rctx.mag, dctx, imt, stddev_types)
        amplification = self.site_term(sctx, rctx, dctx, dists, imt,
                                       stddev_types)
        mean += amplification
        return mean, stddevs

    def site_term(self, sctx, rctx, dctx, dists, imt, stddev_types):
        """
        Site term as used to calculate site coefficients for NBCC2015:

        For Vs30 > 760 m/s use log-log interpolation of the 760-to-2000
        factor of AA13.

        For Vs30 < 760 m/s use the site term of Boore and Atkinson 2008.

        Original site term is relative to Vs30 = 760m/s so needs to be made
        relative to Vs30 = 450 m/s by dividing by the site term at Vs30 = 450.
        Assume PGA_760 = 0.1g for Vs30 > 450 m/s. Also need to correct PGA at
        site class C to 760 m/s. Cap PGA_450 at 0.1 - 0.5g.

        """

        imls_pga = self._return_tables(rctx.mag, PGA(), "IMLs")
        PGA450 = self._get_mean(imls_pga, dctx, dists)
        imls_SA02 = self._return_tables(rctx.mag, SA(0.2), "IMLs")
        SA02 = self._get_mean(imls_SA02, dctx, dists)

        PGA450[SA02 / PGA450 < 2.0] = PGA450[SA02 / PGA450 < 2.0] * 0.8

        pgas = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        pga_cors = np.array([0.083, 0.165, 0.248, 0.331, 0.414])
        PGA760 = np.interp(PGA450, pgas, pga_cors)
        PGA760_ref = np.copy(PGA760)
        PGA760_ref[sctx.vs30 > 450.] = 0.1

        vs30ref = np.zeros_like(sctx.vs30)
        vs30ref += 450.0

        site_term = (self.AB06_BA08(sctx.vs30, imt, PGA760_ref) /
                     self.AB06_BA08(vs30ref, imt, PGA760_ref))

        return np.log(site_term)

    def AB06_BA08(self, vs30, imt, PGA760):

        C = self.COEFFS_2000_to_BC[imt]

        F = np.zeros_like(vs30)

        F[vs30 >= 760.] = 10**(np.interp(np.log10(vs30[vs30 >= 760.]),
                                         np.log10([760.0, 2000.0]),
                                         np.log10([1.0, C['c']])))
        F[vs30 >= 760.] = 1./F[vs30 >= 760.]

        C2 = self.BA08.COEFFS_SOIL_RESPONSE[imt]
        nl = self.BA08._get_site_amplification_non_linear(vs30[vs30 < 760.],
                                                          PGA760[vs30 < 760.],
                                                          C2)
        lin = self.BA08._get_site_amplification_linear(vs30[vs30 < 760.], C2)
        F[vs30 < 760.] = np.exp(nl+lin)

        return F

    COEFFS_2000_to_BC = CoeffsTable(sa_damping=5, table="""\
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
