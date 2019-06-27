#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module exports :class:`NBCC2015_AA13_Base`,
               :class:`NBCC2015_AA13_activecrustFRjb_low`,
               :class:`NBCC2015_AA13_activecrustFRjb_central`,
               :class:`NBCC2015_AA13_activecrustFRjb_high`,
               :class:`NBCC2015_AA13_interface_low`,
               :class:`NBCC2015_AA13_interface_central`,
               :class:`NBCC2015_AA13_interface_high`,
               :class:`NBCC2015_AA13_activecrust_low`,
               :class:`NBCC2015_AA13_activecrust_central`,
               :class:`NBCC2015_AA13_activecrust_high`,
               :class:`NBCC2015_AA13_inslab30_low`,
               :class:`NBCC2015_AA13_inslab30_central`,
               :class:`NBCC2015_AA13_inslab30_high`,
               :class:`NBCC2015_AA13_inslab50_low`,
               :class:`NBCC2015_AA13_inslab50_central`,
               :class:`NBCC2015_AA13_inslab50_high`,
               :class:`NBCC2015_AA13_offshore_low`,
               :class:`NBCC2015_AA13_offshore_central`,
               :class:`NBCC2015_AA13_offshore_high`,
               :class:`NBCC2015_AA13_stablecrust_low`,
               :class:`NBCC2015_AA13_stablecrust_central`,
               :class:`NBCC2015_AA13_stablecrust_high`,

"""
import os
import numpy as np
from openquake.baselib import hdf5
from openquake.hazardlib.gsim.gmpe_table import GMPETable
from openquake.hazardlib.gsim.base import CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.gsim.boore_atkinson_2008 import BooreAtkinson2008

dirname = os.path.dirname(__file__)
BASE_PATH_AA13 = os.path.join(dirname, 'nbcc2015_tables')


class NBCC2015_AA13_Base(GMPETable):
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
    AA13_TABLE = ""
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([PGA, PGV, SA])
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,))
    REQUIRES_SITES_PARAMETERS = set(('vs30',))
    REQUIRES_DISTANCES = ""
    REQUIRES_RUPTURE_PARAMETERS = set(('mag',))
    BA08 = BooreAtkinson2008()

    def init(self):
        if not self.AA13_TABLE:
            raise NotImplementedError("AA13 GMPE requires input table")
        with hdf5.File(self.AA13_TABLE, 'r') as fle:
            super().init(fle)

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


class NBCC2015_AA13_stablecrust_low(NBCC2015_AA13_Base):
    """
    AA13 Stable Crust (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Stable Crust"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Stable Crust Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "ENA_low_clC.hdf5")


class NBCC2015_AA13_stablecrust_central(NBCC2015_AA13_Base):
    """
    AA13 Stable Crust (central branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Stable Crust"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Stable Crust Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "ENA_med_clC.hdf5")


class NBCC2015_AA13_stablecrust_high(NBCC2015_AA13_Base):
    """
    AA13 Stable Crust (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Stable Crust"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Stable Crust High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "ENA_high_clC.hdf5")


class NBCC2015_AA13_activecrust_low(NBCC2015_AA13_Base):
    """
    AA13 Active Crust (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Crust"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Active Crust Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "Wcrust_low_clC.hdf5")


class NBCC2015_AA13_activecrust_central(NBCC2015_AA13_Base):
    """
    AA13 Active Crust (central branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Crust"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Active Crust Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "Wcrust_med_clC.hdf5")


class NBCC2015_AA13_activecrust_high(NBCC2015_AA13_Base):
    """
    AA13 Active Crust (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Crust"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Active Crust High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "Wcrust_high_clC.hdf5")


class NBCC2015_AA13_activecrustFRjb_low(NBCC2015_AA13_Base):
    """
    AA13 Active Fault (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Crust Fault"
    REQUIRES_DISTANCES = set(('rjb',))
    gsim = "AA13 Active Crust Fault Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WcrustFRjb_low_clC.hdf5")


class NBCC2015_AA13_activecrustFRjb_central(NBCC2015_AA13_Base):
    """
    AA13 Active Fault (central branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Crust Fault"
    REQUIRES_DISTANCES = set(('rjb',))
    gsim = "AA13 Active Crust Fault Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WcrustFRjb_med_clC.hdf5")


class NBCC2015_AA13_activecrustFRjb_high(NBCC2015_AA13_Base):
    """
    AA13 Active Fault (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Active Crust Fault"
    REQUIRES_DISTANCES = set(('rjb',))
    gsim = "AA13 Active Crust Fault High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WcrustFRjb_high_clC.hdf5")


class NBCC2015_AA13_inslab30_low(NBCC2015_AA13_Base):
    """
    AA13 Inslab 30km depth (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Inslab 30"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Subduction Inslab 30 Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinslabD30_low_clC.hdf5")


class NBCC2015_AA13_inslab30_central(NBCC2015_AA13_Base):
    """
    AA13 Inslab 30km depth (central branch) as used in the 5th generation
    seismic hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Inslab 30"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Subduction Inslab 30 Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinslabD30_med_clC.hdf5")


class NBCC2015_AA13_inslab30_high(NBCC2015_AA13_Base):
    """
    AA13 Inslab 30km depth (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Inslab 30"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Subduction Inslab 30 High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinslabD30_high_clC.hdf5")


class NBCC2015_AA13_inslab50_low(NBCC2015_AA13_Base):
    """
    AA13 Inslab 50km depth (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Inslab 50"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Subduction Inslab 50 Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinslabD50_low_clC.hdf5")


class NBCC2015_AA13_inslab50_central(NBCC2015_AA13_Base):
    """
    AA13 Inslab 50km depth (central branch) as used in the 5th generation
    seismic hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Inslab 50"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Subduction Inslab 50 Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinslabD50_med_clC.hdf5")


class NBCC2015_AA13_inslab50_high(NBCC2015_AA13_Base):
    """
    AA13 Inslab 50km depth (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Inslab 50"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Subduction Inslab 50 High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinslabD50_high_clC.hdf5")


class NBCC2015_AA13_interface_low(NBCC2015_AA13_Base):
    """
    AA13 Interface (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Interface"
    REQUIRES_DISTANCES = set(('rrup',))
    gsim = "AA13 Subduction Interface Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinterfaceCombo_lowclC.hdf5")


class NBCC2015_AA13_interface_central(NBCC2015_AA13_Base):
    """
    AA13 Interface (central branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Interface"
    REQUIRES_DISTANCES = set(('rrup',))
    gsim = "AA13 Subduction Interface Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinterfaceCombo_medclC.hdf5")


class NBCC2015_AA13_interface_high(NBCC2015_AA13_Base):
    """
    AA13 Interface (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Subduction Interface"
    REQUIRES_DISTANCES = set(('rrup',))
    gsim = "AA13 Subduction Interface High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "WinterfaceCombo_highclC.hdf5")


class NBCC2015_AA13_offshore_low(NBCC2015_AA13_Base):
    """
    AA13 Western Offshore (low branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Offshore"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Offshore Low"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "Woffshore_low_clC.hdf5")


class NBCC2015_AA13_offshore_central(NBCC2015_AA13_Base):
    """
    AA13 Western Offshore (central branch) as used in the 5th generation
    seismic hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Offshore"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Offshore Central"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "Woffshore_med_clC.hdf5")


class NBCC2015_AA13_offshore_high(NBCC2015_AA13_Base):
    """
    AA13 Western Offshore (high branch) as used in the 5th generation seismic
    hazard model of Canada.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = "Offshore"
    REQUIRES_DISTANCES = set(('rhypo',))
    gsim = "AA13 Offshore High"
    AA13_TABLE = os.path.join(BASE_PATH_AA13, "Woffshore_high_clC.hdf5")
