# -*- coding: utf-8 -*-
"""
Bayless and Somerville (2024) Ground Motion Model for Australia (BS24)

OpenQuake hazardlib implementation
by T Costa de Lima, April 2026, Geoscience Australia
(thuany.costadelima@ga.gov.au)

Reference:
    Bayless J. and P. Somerville (2024). An Updated Ground Motion Model for
    Australia Developed Using Broadband Ground Motion Simulations.
    Proc. AEES 2024 National Conference, Adelaide, South Australia.

    Coefficients and Fortran code with the model were kindly provided by Jeff Bayless
    (jeff.bayless@aecom.com).
    
    Full coefficient tables from:
    Appendix D - Bayless J. and P. Somerville (2024, updated May 2026). 
    AECOM internal report.

===========================================================================
Model description  (Equations from the 2024 AEES paper):

    ln(RotD50) = fM + fP + fS + fZ1.0 + fZtor + fHW             Median model [Eq. 2]

    fM    = magnitude scaling               [Eq. 3, ASK14 polynomial formulation]
    fP    = distance scaling                [Eq. 4, ASK14 path scaling formulation, geometric spreading + anelastic Q]
    fZtor = earthquake depth scaling        [Eq. 5, new cubic polynomial in Ztor]

    fS    = Vs30 site amplification         [adopted, Boore et al. 2014]
    fZ1.0 = basin depth scaling             [adopted, Boore et al. 2014]
    fHW   = hanging wall effects            [adopted, Donahue & Abrahamson 2014 as implemented in ASK14]

Aleatory variability [Eq. 6]: Al Atik (2015) global model.
    sigma = sqrt(tau^2 + phi^2)

Output: ln(RotD50) in units of g (OpenQuake standard).
Note: Bayless Fortran outputs cm/s/s (+6.89). Here we return ln(g).

Applicability: M 4.0-8.0, Rrup 0-300 km, T 0.01-10 sec,
                  Vs30 150-1500 m/s.

The Cratonic and NonCratonic versions share all coefficients except:
    a1  (high-freq source level / source spectrum mean level)
    a17 (anelastic attenuation / crustal Q)

===========================================================================
Module exports:
    BaylessSomerville2024Cratonic
    BaylessSomerville2024NonCratonic
"""
import numpy as np
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


def _get_fM(C, mag):
    """
    Magnitude scaling fM [Equation 3 in Bayless J. and P. Somerville (2024)].

    ASK14 polynomial formulation:
        M >= M1:        a1 + a5*(M-M1) + a8*(8.5-M)^2
        M2 <= M < M1:   a1 + a4*(M-M1) + a8*(8.5-M)^2
        M < M2:         fM(M=M2) + a6*(M-M2) + a7*(M-M2)^2

    M is the moment magnitude;
    M1 is period-dependent (6.75-7.25); this is already taken into account in the COEFFS
    M2 = 5.0 fixed.
    """

    M1 = C['M1']
    M2 = 5.0 # Lower magnitude break, fixed at 5.0 (same as ASK14)
    fM = np.zeros_like(mag, dtype=float)
    fM_M2 = C['a1'] + C['a4'] * (M2 - M1) + C['a8'] * (8.5 - M2) ** 2

    idx = mag >= M1
    fM[idx] = C['a1'] + C['a5']*(mag[idx]-M1) + C['a8']*(8.5-mag[idx])**2

    idx = (mag >= M2) & (mag < M1)
    fM[idx] = C['a1'] + C['a4']*(mag[idx]-M1) + C['a8']*(8.5-mag[idx])**2

    idx = mag < M2
    fM[idx] = fM_M2 + C['a6']*(mag[idx]-M2) + C['a7']*(mag[idx]-M2)**2

    return fM



def _get_fP(C, mag, rrup):
    """
    Path scaling fP [Equation 4 in Bayless J. and P. Somerville (2024)].
        fP = [a2 + a3*(M-M1)] * ln(R) + a17*Rrup

    R = sqrt(Rrup^2 + c4M^2), where c4M is the additive distance term to represent the
    near-source amplitude saturation effects of the finite-fault rupture dimension as 
    described in Equation 4 in Abrahamson et al. (ASK14, 2014). 

    The ln(R) term models the magnitude-dependent geometric spreading;
    
    a17Rrup models anelastic attenuation and scattering effects.

    Notes:
        - a17 differs between Cratonic (slower) and NonCratonic (faster) versions.
        
        - c4M tapers with magnitude (ASK14), Equation 4.4 in Abrahamson et al. (2014).
            M >= 5.0 : c4M = c4
            4 <= M < 5 : c4M = c4 - (c4 - 1.0) * (5.0 - M)   [ASK14, lower anchor = 1.0]
            M < 4.0  : c4M = 1.0

            Here however we set c4M lower anchor = 2.0 (intentional deviation from ASK14 which uses 1.0)
            Jeff Bayless confirmed this was set based on scaling for very small
            magnitudes at short distances (personal communication, May 2026).

        - For M < M2=5.0, geometric spreading is frozen at M2 (ASK14, pg.1032)
            M2 = 5.0  # Fixed lower magnitude break, ASK14 PEER Report 2013/04, p.23:
               # "the breaks in the magnitude scaling in Equation (4.2) are
               #  set at M1=6.75 and M2=5.0"
            
    """
    c4 = C['c4']
    M1 = C['M1']
    M2 = 5.0

    c4m = np.where(mag >= 5.0, c4,
                np.where(mag >= 4.0, c4 - (c4 - 2.0) * (5.0 - mag),
                   2.0))

    R = np.sqrt(rrup**2 + c4m**2) # in km

    mag_for_geom = np.where(mag < M2, M2, mag)
    return (C['a2'] + C['a3'] * (mag_for_geom - M1)) * np.log(R) + C['a17'] * rrup



def _get_fZtor(C, ztor):
    """
    Depth scaling fZtor [Originally from Equation 5 in Bayless and Somerville (2024)]:
        fZtor = d1*Z^3 + d2*Z^2 + d3*Z + d4
    
    However, instead of using Z = min(Ztor, 20 km), we now have Z = min(Ztor - 10, 5) after personal communication
    with Jeff Bayless [BS24 Appendix Rev2, May 2026].

    -Ztor is the depth to the top of the rupture plane in km.
    -d1 through d4 are period-dependent coefficients

    -The model is centred at Ztor = 10 km (no scaling at reference depth).
    -d4 is fixed to zero at all periods, so fZtor = 0 when Z = 0 (Ztor = 10 km).
    -Z is capped at 5 km (equivalent to Ztor >= 15 km) based on log-likelihood analysis of the simulation data.
    -For Ztor < 10 km, Z is negative, giving amplification at long periods and de-amplification at short periods (Rg wave effects).
    """
    Z = np.minimum(ztor - 10.0, 5.0)
    return C['d1'] * Z**3 + C['d2'] * Z**2 + C['d3'] * Z + C['d4']


def _get_stddevs(C, mag):
    """
    Aleatory variability  (Al Atik 2015, Table 5.1 / Eq. 5.6 & 5.14)
        sigma = sqrt(tau^2 + phi^2)

    tau: between-event standard deviation
    phi: within-event standard deviation  
    """
    # tau equation from Eq. 5.6 in Al Atik 2015, global model
    tau1, tau2, tau3, tau4 = 0.4518, 0.4270, 0.3863, 0.3508 # from Table 5.1 in Al Atik 2015
    tau = np.where(mag > 6.5, tau4, 
                np.where(mag > 5.5, tau3 + (tau4-tau3)*(mag-5.5)/1.0,
                    np.where(mag > 5.0, tau2 + (tau3-tau2)*(mag-5.0)/0.5,
                        np.where(mag > 4.5, tau1 + (tau2-tau1)*(mag-4.5)/0.5,
                            tau1
                        )
                    )
                )
            )
    # phi equation from Eq. 5.14 in Al Atik 2015
    PhiA, PhiB = C['PhiA'], C['PhiB']
    phi = np.where(mag <= 5.0, PhiA, 
                np.where(mag > 6.5, PhiB, 
                    PhiA + (mag - 5.0) * (PhiB - PhiA) / 1.5
                    )
            )
    return np.sqrt(tau**2 + phi**2), tau, phi



def _get_fZ10(C, z1pt0, vs30, imt_period):
    """
    fZ1.0: Basin depth scaling (Boore et al. 2014)

    Z1.0 is the depth to the 1.0 km/s shear-wave velocity horizon, basically 
    how deep we have to go underground before the rock becomes 
    "fast" (Vs = 1000 m/s). It is a proxy for basin depth. 
    
    A site sitting on top of a deep sedimentary basin has a 
    large Z1.0 (say 0.5–2 km). A site on hard rock has a very small 
    Z1.0 (maybe 0.001 km).
    """
    if imt_period < 0.65:   #  this means no basin term for short periods T < 0.65 sec, BSSA14 (Boore et al. 2014, Eq. 9)
        return np.zeros_like(vs30) # equivalent to F_dz1=0.0 in the fortran code

    # California model z1_ref (km) from BSSA14,  Boore et al., 2014 / Jeff's Fortran code, expected (reference) Z1.0 for a given Vs30
    # Eq 11 in Boore et al., 2014
    z1_ref = (np.exp(-7.15 / 4.0 *
               np.log((vs30**4 + 570.94**4) / (1360.0**4 + 570.94**4)))
              / 1000.0)

    z1 = np.where(z1pt0 < 0, z1_ref, z1pt0) #  until proper Z1.0 measurements are collected here, don't apply \
                                            # a basin correction! \
                                            # If z1pt0 is -999 (not measured), we use the Vs30-derived reference. \
                                            # Otherwise we use the actual measured value.

    dz1 = z1 - z1_ref                   #[Eq. 10 Boore et al., 2014], This is the deviation of the site's actual basin depth
                                        # from what you'd expect given its Vs30. 
                                        # A positive dz1 means the basin is deeper than average for 
                                        # that Vs30 -> extra amplification. A negative dz1 means shallower 
                                        # than average -> de-amplification. When z1pt0 = -999, dz1 = 0 and the term vanishes.

    b6, b7 = C['b6'], C['b7']
    ratio = np.where(np.abs(b6) > 1e-9, b7 / b6, 1e9)   # b6 is the slope (how much amplification per km of 
                                                        # extra basin depth) and b7 is the maximum cap. The 
                                                        # ratio line just avoids dividing by zero in the
                                                        # case b6 is zero

    return np.where(dz1 <= ratio, b6 * dz1, b7)


#  Taper 5: along-strike Ry0  [ASK14 Eq. 4.13, Ry0 version] where:
    #ry0 = getattr(ctx, 'ry0', np.zeros_like(rx))
    #ry1 = rx * np.tan(np.radians(20.0))
def _get_fHW(C, ctx):
    """
    Geometric hanging wall effects fHW (Donahue & Abrahamson 2014 with ASK14 implementation).

        The total hanging wall term is:
        fHW = a13 * T1 * T2 * T3 * T4 * T5

    It uses coefficient a13 stored in BS24 COEFFS, (Table D-8).

    Requires ctx: rx, ry0, rrup, rjb, ztor, dip, mag, width.
    Returns zero for footwall sites (rx <= 0) and vertical faults (dip=90).

    The functional form with five tapers is described in:
        Abrahamson et al. (2013) PEER Report 2013/04, Section 4.4,
        Equations 4.11 to 4.15a.

    T1-T5 are five distance/geometry tapers, each ranging 0 to 1
    (or slightly above 1 for T1 when dip < 30°).

    -----------------------------------------------------------------------
    TAPER 1 — T1: Dip taper
    -----------------------------------------------------------------------
    ASK14 PEER Report Eq. 4.11
        T1 = (90 - dip) / 45      for dip > 30°
        T1 = 60 / 45              for dip <= 30°

    -----------------------------------------------------------------------
    TAPER 2 — T2: Magnitude taper
    -----------------------------------------------------------------------
    ASK14 PEER Report Eq. 4.12
        T2 = 1 + a2HW * (M - 6.5)              for M >= 6.5
        T2 = 1 + a2HW * (M - 6.5) - (1-a2HW)*(M-6.5)^2   for 5.5 < M < 6.5
        T2 = 0                                  for M <= 5.5

    -----------------------------------------------------------------------
    TAPER 3 — T3: Rx distance taper
    -----------------------------------------------------------------------
    ASK14 PEER Report Eq. 4.13
        R1 = W * cos(dip)     [horizontal projection of fault width]
        R2 = 3 * R1

        T3 = h1 + h2*(Rx/R1) + h3*(Rx/R1)^2     for Rx < R1
        T3 = 1 - (Rx - R1) / (R2 - R1)          for R1 <= Rx <= R2
        T3 = 0                                  for Rx > R2
        T3 = 0                                  for Rx < 0  (footwall)

    Note: the quadratic h1 + h2*(Rx/R1) + h3*(Rx/R1)^2 with the
    specific h values of h1=0.25, h2=1.5, h3=-0.75
    gives T3=0.25 at Rx=0, T3=1.0 at Rx=R1.

    -----------------------------------------------------------------------
    TAPER 4 — T4: Depth to top of rupture (Ztor) taper
    -----------------------------------------------------------------------
    ASK14 PEER Report Eq. 4.14
        T4 = 1 - (Ztor^2) / 100    for Ztor < 10 km
        T4 = 0                      for Ztor >= 10 km

    -----------------------------------------------------------------------
    TAPER 5 — T5: Along-strike (Ry0) taper
    -----------------------------------------------------------------------
    ASK14 PEER Report Eq. 4.15a
        T5 = 1                          for Ry0 < Ry1
        T5 = 1 - (Ry0 - Ry1) / 5        for Ry0 - Ry1 <  5
        T5 = 0                          for Ry0 - Ry1 >= 5

    """

    mag, rx, ztor, dip, width = ctx.mag, ctx.rx, ctx.ztor, ctx.dip, ctx.width

    # Taper 1: dip  [ASK14 Eq. 4.11]
    hw_t1 = np.where(dip <= 30.0, 60.0 / 45.0, (90.0 - dip) / 45.0)

    # Taper 2: magnitude  [ASK14 Eq. 4.12]
    hw_a2 = 0.2 # also in ASK14, listed just before Eq15.b
    hw_t2 = np.where(
        mag >= 6.5,
        1.0 + hw_a2 * (mag - 6.5),
        np.where(
            mag > 5.5,
            1.0 + hw_a2*(mag-6.5) - (1.0-hw_a2)*(mag-6.5)**2,
            0.0))

    # Taper 3: Rx distance  [ASK14 Eq. 4.13]
    ## h1, h2, h3 values, and R1 and R2 are also in ASK14, listed just before Eq15.b
    h1 = 0.25
    h2 = 1.5
    h3 = -0.75 
    R1 = width * np.cos(np.radians(dip))  # horizontal fault width projection
    R2 = 3.0 * R1
    ##
    
    hw_t3 = np.where(
        rx > R2, 0.0,
        np.where(
            rx < R1,
            h1 + h2*(rx/R1) + h3*(rx/R1)**2,
            np.where((rx >= R1) & (rx <= R2), 
                     1.0 - (rx - R1) / (R2 - R1),
                     0.0)))
            

    # Taper 4: Ztor depth  [ASK14 Eq. 4.14]
    hw_t4 = np.where(ztor < 10.0, 1.0 - ztor**2 / 100.0, 0.0)

    # Taper 5: along-strike Ry0  [ASK14 Eq. 4.13, Ry0 version]
    # Ry0 = 0 if not available (sites along the rupture, no along-strike offset)
    ry0 = getattr(ctx, 'ry0', np.zeros_like(rx))
    ry1 = rx * np.tan(np.radians(20.0))
    
    hw_t5 = np.where(
        ry0 < ry1, 1.0,
        np.where(ry0 - ry1 < 5.0,
                 1.0 - (ry0 - ry1) / 5.0,
                 0.0))

    return C['a13'] * hw_t1 * hw_t2 * hw_t3 * hw_t4 * hw_t5



def _get_fS(C, vs30, pga_rock):
    """
    fS: Vs30 site amplification from Seyhan and Stewart (2014) as used in Boore et al. (2014; BSSA14).

    -----------------------------------------------------------------------
    TERM 1 — flin: Linear site amplification
    Eq. 6  in Boore et al. (2014; BSSA14)
    ----------------------------------------------------------------------- 
        
        flin = c_site * ln( min(Vs30, vc) / 760 ), [v_ref = 760; if Vs30 > vcT, use vcT instead of Vs30] 

    Coefficients (from Table D-8, BSSA14 columns):
        c_site : slope of the linear amplification in log-velocity space.
                 Negative values mean amplification increases as Vs30
                 decreases below 760 m/s (softer sites amplify more).
                 In Table D-8 this column is labelled 'c'.
        vc     : velocity cap (m/s). For Vs30 above vc the linear term
                 saturates — very hard rock does not keep amplifying
                 beyond this threshold. Values range ~770–1503 m/s
                 depending on period (Table D-8 column 'vc').

    Behaviour:
        Vs30 = 760 m/s (reference): ln(760/760) = 0  -> flin = 0  
        Vs30 < 760 m/s (soft site): ln < 0, c_site < 0 -> flin > 0 (amplification)
        Vs30 > vc    (very hard rock): capped, no further change

    -----------------------------------------------------------------------
    TERM 2 — fnl: Nonlinear site amplification
    Eq.s 7 and 8  in Boore et al. (2014; BSSA14)
    -----------------------------------------------------------------------
    
        fnl = b1 + b2 * log((pgar + b3) / b3)
        b2 = b4T * (exp(b5T*(min(vs30,760)-360)) - exp(b5T*(760-360))) 

    The nonlinear term captures soil softening: at high input shaking
    levels (large pga_rock), soft soils amplify less than they would
    linearly because they yield (strain softening). The term is zero
    at the reference rock condition and grows with softer Vs30 and
    stronger input motion.

    """
    #Reference Vs30 = 760 m/s. At reference: fS ~ 0.

    # --- Term 1: Linear ---
    flin = C['c_site'] * np.log(np.minimum(vs30, C['vc']) / 760.0)

    # --- Term 2: Nonlinear ---
    # Fortran b1=0.0, b3=0.1 are hardcoded constants
    # b2 is zero at Vs30=760 (reference) by construction of the formula.
    b1 = 0.0   # from the fortran code
    b3 = 0.1   # from the fortran code
    b2 = C['b4'] * (np.exp(C['b5'] * (np.minimum(vs30, 760.0) - 360.0))
                    - np.exp(C['b5'] * (760.0 - 360.0)))
    fnl = b1 + b2 * np.log((pga_rock + b3) / b3)

    return flin + fnl

 
# ---------------------------------------------------------------------------
# Base GSIM class
# ---------------------------------------------------------------------------
class BaylessSomerville2024Base(GMPE):
    """
    Base class for BS24. Use Cratonic or NonCratonic subclasses directly.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.RotD50
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT,
    }
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z1pt0'}
    REQUIRES_RUPTURE_PARAMETERS = {'mag', 'rake', 'ztor', 'dip', 'width'}
    REQUIRES_DISTANCES = {'rrup', 'rx', 'rjb'}

    def __init__(self, hwflag=1, **kwargs):
        """
        hwflag : int, optional
            1 (default) — compute hanging wall term (from Fortran version HWFlag=1)
            0           — suppress hanging wall term (from Fortran version HWFlag=0).
                          Use this for point sources where Rx is not defined.
        """
        super().__init__(**kwargs)
        self.hwflag = hwflag


    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        # Pass 1: rock PGA at Vs30=760 for nonlinear site term
        #C_PGA = self.COEFFS[PGA()]
        C_PGA = self.COEFFS[SA(0.01)]  # Fortran uses pgat=0.01, not T=0
        pga_rock = np.exp(
            _get_fM(C_PGA, ctx.mag)
            + _get_fP(C_PGA, ctx.mag, ctx.rrup)
            + _get_fZtor(C_PGA, ctx.ztor)
        )
        # Pass 2: each IMT
        for m, imt in enumerate(imts):
            C = self.COEFFS[imt]
            imt_period = 0.0 if imt == PGA() else imt.period
            mean[m] = (
                _get_fM(C, ctx.mag)
                + _get_fP(C, ctx.mag, ctx.rrup)
                + _get_fZtor(C, ctx.ztor)
                + _get_fS(C, ctx.vs30, pga_rock)
                + _get_fZ10(C, ctx.z1pt0, ctx.vs30, imt_period)
                #+ _get_fHW(C, ctx)
                + (_get_fHW(C, ctx) if self.hwflag == 1 else np.zeros_like(ctx.mag))
            )
            sig[m], tau[m], phi[m] = _get_stddevs(C, ctx.mag)


# ---------------------------------------------------------------------------
# Cratonic subclass — full coefficient table
# ---------------------------------------------------------------------------
class BaylessSomerville2024Cratonic(BaylessSomerville2024Base):
    """
    Bayless and Somerville (2024) GMM — Cratonic Australia.

    Applicable to Yilgarn, Gawler, Pilbara, Kimberley, and Northern
    Australian Cratons (NSHA23 classification).

    Higher short-period ground motions and slower attenuation than NonCratonic.

    Coefficients from Table D-7 (a1_Crat, a17_Crat) and Table D-8.
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT      a1        a17        M1      c4     a2       a3      a4       a5       a6      a7       a8        d1          d2          d3          d4        a13    c_site    vc      b4        b5       b6        b7      PhiA    PhiB
pga         1.4840  -0.005124  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1541  0.0000  -0.0017     1.680e-04   -3.109e-03    1.730e-02    0.0000  0.6000 -0.6037  1500  -0.1483  -0.0070  -9.9000  -9.9000  0.7131  0.5770
0.010       1.5042  -0.005124  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1541  0.0000  -0.0017     1.680e-04   -3.109e-03    1.730e-02    0.0000  0.6000 -0.6037  1500  -0.1483  -0.0070  -9.9000  -9.9000  0.7131  0.5770
0.011       1.5171  -0.005224  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1530  0.0000  -0.0017     1.680e-04   -3.109e-03    1.731e-02    0.0000  0.6000 -0.5996  1500  -0.1481  -0.0070  -9.9000  -9.9000  0.7130  0.5771
0.012       1.5310  -0.005322  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1520  0.0000  -0.0017     1.681e-04   -3.109e-03    1.731e-02    0.0000  0.6000 -0.5959  1500  -0.1480  -0.0071  -9.9000  -9.9000  0.7130  0.5772
0.013       1.5463  -0.005418  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1511  0.0000  -0.0017     1.681e-04   -3.110e-03    1.731e-02    0.0000  0.6000 -0.5924  1500  -0.1478  -0.0071  -9.9000  -9.9000  0.7129  0.5773
0.015       1.5828  -0.005601  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1494  0.0000  -0.0017     1.682e-04   -3.110e-03    1.732e-02    0.0000  0.6000 -0.5863  1500  -0.1476  -0.0072  -9.9000  -9.9000  0.7128  0.5774
0.017       1.6334  -0.005770  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1480  0.0000  -0.0017     1.683e-04   -3.111e-03    1.733e-02    0.0000  0.6000 -0.5809  1500  -0.1474  -0.0072  -9.9000  -9.9000  0.7127  0.5775
0.020       1.8230  -0.006087  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1461  0.0000  -0.0017     1.685e-04   -3.113e-03    1.736e-02    0.0000  0.6000 -0.5739  1500  -0.1471  -0.0073  -9.9000  -9.9000  0.7126  0.5777
0.022       1.9594  -0.006259  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1486  0.0000  -0.0017     1.685e-04   -3.115e-03    1.738e-02    0.0000  0.6000 -0.5645  1501  -0.1489  -0.0073  -9.9000  -9.9000  0.7137  0.5793
0.025       2.0755  -0.006479  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1519  0.0000  -0.0017     1.686e-04   -3.118e-03    1.745e-02    0.0000  0.6000 -0.5520  1502  -0.1514  -0.0073  -9.9000  -9.9000  0.7151  0.5814
0.029       2.1949  -0.006646  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1557  0.0000  -0.0017     1.690e-04   -3.123e-03    1.754e-02    0.0000  0.6000 -0.5374  1503  -0.1542  -0.0073  -9.9000  -9.9000  0.7167  0.5838
0.032       2.2621  -0.006667  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1475  0.0000  -0.0017     1.695e-04   -3.127e-03    1.761e-02    0.0000  0.6000 -0.5245  1503  -0.1596  -0.0072  -9.9000  -9.9000  0.7194  0.5875
0.035       2.3158  -0.006638  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1348  0.0000  -0.0017     1.700e-04   -3.135e-03    1.771e-02    0.0000  0.6000 -0.5111  1502  -0.1661  -0.0071  -9.9000  -9.9000  0.7226  0.5918
0.040       2.3795  -0.006528  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1160  0.0000  -0.0017     1.709e-04   -3.153e-03    1.788e-02    0.0000  0.6000 -0.4912  1502  -0.1758  -0.0069  -9.9000  -9.9000  0.7274  0.5982
0.045       2.4217  -0.006364  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0994  0.0000  -0.0017     1.718e-04   -3.174e-03    1.807e-02    0.0000  0.6000 -0.4737  1502  -0.1843  -0.0067  -9.9000  -9.9000  0.7407  0.6147
0.050       2.4465  -0.006199  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0845  0.0000  -0.0017     1.729e-04   -3.188e-03    1.823e-02    0.0000  0.6000 -0.4580  1501  -0.1920  -0.0065  -9.9000  -9.9000  0.7526  0.6295
0.055       2.4543  -0.006032  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0713  0.0000  -0.0017     1.736e-04   -3.194e-03    1.838e-02    0.0000  0.6000 -0.4547  1500  -0.2021  -0.0063  -9.9000  -9.9000  0.7614  0.6405
0.060       2.4539  -0.005870  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0593  0.0000  -0.0017     1.728e-04   -3.204e-03    1.865e-02    0.0000  0.6000 -0.4517  1498  -0.2113  -0.0061  -9.9000  -9.9000  0.7694  0.6505
0.065       2.4504  -0.005716  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0483  0.0000  -0.0017     1.726e-04   -3.213e-03    1.887e-02    0.0000  0.6000 -0.4490  1497  -0.2198  -0.0060  -9.9000  -9.9000  0.7767  0.6597
0.075       2.4282  -0.005441  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0285  0.0000  -0.0017     1.729e-04   -3.229e-03    1.913e-02    0.0000  0.6000 -0.4441  1494  -0.2350  -0.0057  -9.9000  -9.9000  0.7899  0.6761
0.085       2.4000  -0.005206  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0339  0.0000  -0.0017     1.744e-04   -3.237e-03    1.917e-02    0.0000  0.6000 -0.4629  1488  -0.2412  -0.0057  -9.9000  -9.9000  0.7932  0.6809
0.100       2.3424  -0.004904  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0408  0.0000  -0.0017     1.759e-04   -3.245e-03    1.911e-02    0.0000  0.6000 -0.4872  1479  -0.2492  -0.0056  -9.9000  -9.9000  0.7974  0.6872
0.110       2.2980  -0.004734  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0596  0.0000  -0.0017     1.761e-04   -3.248e-03    1.915e-02    0.0000  0.6000 -0.5089  1471  -0.2511  -0.0057  -9.9000  -9.9000  0.7927  0.6833
0.120       2.2527  -0.004582  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0768  0.0000  -0.0017     1.753e-04   -3.251e-03    1.926e-02    0.0000  0.6000 -0.5287  1463  -0.2528  -0.0057  -9.9000  -9.9000  0.7884  0.6797
0.130       2.2023  -0.004444  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0926  0.0000  -0.0017     1.760e-04   -3.253e-03    1.912e-02    0.0000  0.6000 -0.5470  1456  -0.2543  -0.0058  -9.9000  -9.9000  0.7844  0.6765
0.150       2.1100  -0.004214  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1208  0.0000  -0.0017     1.761e-04   -3.247e-03    1.889e-02    0.0000  0.6000 -0.5796  1443  -0.2571  -0.0059  -9.9000  -9.9000  0.7773  0.6706
0.170       2.0198  -0.004018  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1657  0.0000  -0.0031     1.746e-04   -3.236e-03    1.877e-02    0.0000  0.6000 -0.6266  1421  -0.2525  -0.0060  -9.9000  -9.9000  0.7646  0.6607
0.200       1.9102  -0.003783  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.2241  0.0000  -0.0080     1.710e-04   -3.195e-03    1.876e-02    0.0000  0.6000 -0.6876  1393  -0.2466  -0.0061  -9.9000  -9.9000  0.7481  0.6478
0.220       1.8458  -0.003654  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.2618  0.0000  -0.0120     1.699e-04   -3.173e-03    1.864e-02    0.0000  0.6000 -0.7236  1377  -0.2419  -0.0063  -9.9000  -9.9000  0.7370  0.6396
0.240       1.7891  -0.003539  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.2962  0.0000  -0.0159     1.692e-04   -3.157e-03    1.841e-02    0.0000  0.6000 -0.7564  1363  -0.2377  -0.0064  -9.9000  -9.9000  0.7268  0.6321
0.260       1.7351  -0.003438  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.3180  0.0000  -0.0198     1.679e-04   -3.162e-03    1.813e-02    0.0000  0.6000 -0.7868  1346  -0.2321  -0.0065  -9.9000  -9.9000  0.7174  0.6257
0.280       1.6863  -0.003346  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.3285  0.0000  -0.0238     1.679e-04   -3.159e-03    1.775e-02    0.0000  0.6000 -0.8152  1327  -0.2254  -0.0066  -9.9000  -9.9000  0.7086  0.6203
0.300       1.6391  -0.003262  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.3383  0.0000  -0.0279     1.686e-04   -3.141e-03    1.734e-02    0.0000  0.6000 -0.8417  1308  -0.2191  -0.0067  -9.9000  -9.9000  0.7005  0.6152
0.350       1.5325  -0.003079  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.4082  0.0000  -0.0379     1.723e-04   -3.086e-03    1.629e-02    0.0000  0.5893 -0.8788  1279  -0.2066  -0.0069  -9.9000  -9.9000  0.6831  0.6069
0.400       1.4467  -0.002933  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.4688  0.0000  -0.0475     1.712e-04   -3.047e-03    1.565e-02    0.0000  0.5800 -0.9109  1253  -0.1958  -0.0071  -9.9000  -9.9000  0.6680  0.5998
0.450       1.3702  -0.002813  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.5162  0.0000  -0.0565     1.655e-04   -3.011e-03    1.547e-02    0.0000  0.5694 -0.9417  1227  -0.1848  -0.0073  -9.9000  -9.9000  0.6556  0.5943
0.500       1.3013  -0.002713  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.5586  0.0000  -0.0650     1.550e-04   -2.964e-03    1.566e-02    0.0000  0.5600 -0.9693  1204  -0.1750  -0.0074  -9.9000  -9.9000  0.6446  0.5893
0.550       1.2428  -0.002635  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.5876  0.0000  -0.0733     1.477e-04   -2.910e-03    1.553e-02    0.0000  0.5529 -0.9801  1191  -0.1665  -0.0076  -7.5512  -7.5590  0.6354  0.5854
0.600       1.1898  -0.002567  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.6141  0.0000  -0.0814     1.454e-04   -2.875e-03    1.478e-02    0.0000  0.5465 -0.9900  1179  -0.1587  -0.0077  -5.4070  -5.4218  0.6270  0.5819
0.650       1.1442  -0.002524  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.6385  0.0000  -0.0895     1.409e-04   -2.840e-03    1.415e-02    0.0000  0.5406 -0.9991  1167  -0.1515  -0.0079  -3.4345  -3.4558  0.6193  0.5786
0.750       1.0448  -0.002523  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.6821  0.0000  -0.1044     1.275e-04   -2.727e-03    1.319e-02    0.0000  0.5300 -1.0154  1148  -0.1387  -0.0081  0.0920   0.0590   0.6055  0.5728
0.850       0.9275  -0.002584  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7173  0.0000  -0.1180     1.026e-04   -2.513e-03    1.245e-02    0.0000  0.5169 -1.0305  1131  -0.1241  -0.0083  0.2116   0.1238   0.5943  0.5669
1.000       0.6928  -0.002658  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7630  0.0000  -0.1360     3.420e-05   -1.965e-03    1.227e-02    0.0000  0.5000 -1.0500  1110  -0.1052  -0.0084  0.3670   0.2080   0.5797  0.5593
1.100       0.4995  -0.002630  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7800  0.0000  -0.1465    -3.040e-05   -1.493e-03    1.338e-02    0.0000  0.4812 -1.0489  1101  -0.0950  -0.0083  0.4307   0.2317   0.5717  0.5545
1.200       0.3002  -0.002568  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7956  0.0000  -0.1559    -1.122e-04   -9.342e-04    1.591e-02    0.0000  0.4640 -1.0479  1093  -0.0858  -0.0081  0.4889   0.2534   0.5644  0.5501
1.300       0.1286  -0.002495  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.8099  0.0000  -0.1644    -1.897e-04   -4.667e-04    1.895e-02    0.0000  0.4482 -1.0470  1086  -0.0772  -0.0080  0.5424   0.2734   0.5577  0.5460
1.500      -0.1423  -0.002160  6.75   4.5    -0.7626  0.22  -0.0209  -0.3309  2.8355  0.0000  -0.1792    -3.026e-04    1.986e-04    2.302e-02    0.0000  0.4200 -1.0454  1072  -0.0620  -0.0077  0.6380   0.3090   0.5457  0.5388
1.700      -0.3346  -0.001818  6.75   4.5    -0.7622  0.22  -0.0209  -0.3309  2.8624  0.0000  -0.1914    -3.802e-04    6.619e-04    2.494e-02    0.0000  0.3895 -1.0427  1045  -0.0507  -0.0064  0.7394   0.3408   0.5362  0.5324
2.000      -0.6010  -0.001338  6.75   4.5    -0.7595  0.22  -0.0209  -0.3309  2.8973  0.0000  -0.2062    -4.649e-04    1.213e-03    2.586e-02    0.0000  0.3500 -1.0392  1009  -0.0361  -0.0048  0.8710   0.3820   0.5239  0.5240
2.200      -0.7595  -0.001087  6.7665 4.5    -0.7567  0.22  -0.0209  -0.3309  2.8994  0.0000  -0.2143    -5.032e-04    1.549e-03    2.533e-02    0.0000  0.3147 -1.0326  989   -0.0308  -0.0041  0.9331   0.4135   0.5180  0.5180
2.400      -0.8951  -0.000881  6.7815 4.5    -0.7535  0.22  -0.0209  -0.3309  2.9013  0.0000  -0.2211    -5.111e-04    1.845e-03    2.269e-02    0.0000  0.2826 -1.0266  970   -0.0260  -0.0035  0.9897   0.4423   0.5125  0.5126
2.600      -1.0299  -0.000730  6.7953 4.5    -0.7472  0.22  -0.0209  -0.3309  2.9030  0.0000  -0.2268    -4.640e-04    2.079e-03    1.563e-02    0.0000  0.2529 -1.0211  953   -0.0215  -0.0029  1.0418   0.4687   0.5075  0.5076
2.800      -1.1476  -0.000611  6.8081 4.5    -0.7422  0.22  -0.0209  -0.3309  2.9046  0.0000  -0.2314    -3.883e-04    2.283e-03    6.109e-03    0.0000  0.2255 -1.0160  937   -0.0174  -0.0023  1.0901   0.4932   0.5029  0.5029
3.000      -1.2695  -0.000529  6.82   4.5    -0.7346  0.22  -0.0209  -0.3309  2.9061  0.0000  -0.2350    -3.127e-04    2.480e-03   -2.759e-03    0.0000  0.2000 -1.0112  922   -0.0136  -0.0018  1.1350   0.5160   0.4986  0.4986
3.500      -1.5564  -0.000372  6.8736 4.5    -0.7134  0.22  -0.0209  -0.3309  2.8968  0.0000  -0.2413    -1.302e-04    2.843e-03   -2.288e-02    0.0000  0.0928 -0.9888  881   -0.0080  -0.0017  1.2079   0.5765   0.4917  0.4917
4.000      -1.7879  -0.000309  6.92   4.5    -0.6882  0.22  -0.0209  -0.3309  2.8888  0.0000  -0.2451     4.180e-05    2.939e-03   -4.045e-02    0.0000  0.0000 -0.9694  844   -0.0032  -0.0015  1.2710   0.6290   0.4857  0.4857
4.400      -1.9478  -0.000294  6.9542 4.5    -0.6698  0.22  -0.0209  -0.3309  2.8929  0.0000  -0.2472     1.500e-04    2.822e-03   -5.119e-02    0.0000  0.0000 -0.9481  823   -0.0020  -0.0015  1.2958   0.6756   0.4828  0.4828
5.000      -2.1623  -0.000294  7.00   4.5    -0.6449  0.22  -0.0209  -0.3309  2.8984  0.0000  -0.2498     2.338e-04    2.132e-03   -5.931e-02    0.0000  0.0000 -0.9195  793   -0.0003  -0.0014  1.3290   0.7380   0.4789  0.4789
5.500      -2.3222  -0.000294  7.0314 4.5    -0.6261  0.22  -0.0209  -0.3309  2.8969  0.0000  -0.2517     2.670e-04    1.366e-03   -6.241e-02    0.0000  0.0000 -0.8859  788   -0.0003  -0.0014  1.3290   0.7547   0.4773  0.4773
6.000      -2.4682  -0.000294  7.06   4.5    -0.6088  0.22  -0.0209  -0.3309  2.8955  0.0000  -0.2534     2.800e-04    6.464e-04   -6.331e-02    0.0000  0.0000 -0.8552  783   -0.0002  -0.0014  1.3290   0.7699   0.4758  0.4758
6.500      -2.6025  -0.000294  7.0905 4.5    -0.5926  0.22  -0.0209  -0.3309  2.8864  0.0000  -0.2549     2.597e-04    2.179e-04   -6.046e-02    0.0000  0.0000 -0.8270  779   -0.0002  -0.0014  1.3290   0.7839   0.4745  0.4744
7.500      -2.8425  -0.000294  7.145  4.5    -0.5633  0.22  -0.0209  -0.3309  2.8700  0.0000  -0.2575     1.959e-04   -4.168e-04   -5.238e-02    0.0000  0.0000 -0.7766  771   -0.0001  -0.0014  1.3290   0.8090   0.4721  0.4720
8.500      -2.8563  -0.000294  7.1907 4.5    -0.5371  0.22  -0.0209  -0.3309  2.8583  0.0000  -0.2595     1.410e-04   -6.883e-04   -4.461e-02    0.0000  0.0000 -0.7240  773   -0.0001  -0.0014  1.2655   0.7629   0.4712  0.4711
10.000     -3.3252  -0.000294  7.25   4.5    -0.5025  0.22  -0.0209  -0.3309  2.8431  0.0000  -0.2621     7.450e-05   -9.020e-04   -3.454e-02    0.0000  0.0000 -0.6558  775   0.0000   -0.0014  1.1830   0.7030   0.4700  0.4700
""")


# ---------------------------------------------------------------------------
# NonCratonic subclass
# ---------------------------------------------------------------------------
class BaylessSomerville2024NonCratonic(BaylessSomerville2024Base):
    """
    Bayless and Somerville (2024) GMM — Non-Cratonic Australia.

    Applicable to Eastern Australian Phanerozoic Accretionary Terranes,
    extended and oceanic crust (NSHA23). 

    Lower short-period ground motions and more rapid attenuation than Cratonic version.

    Differs from Cratonic only in a1 and a17 (Table D-7 NonCratonic columns).
    """
    COEFFS = CoeffsTable(sa_damping=5, table="""\
IMT      a1        a17        M1      c4     a2       a3      a4       a5       a6      a7       a8        d1          d2          d3          d4        a13    c_site    vc      b4        b5       b6        b7      PhiA    PhiB
pga         0.8943  -0.007517  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1541  0.0000  -0.0017     1.680e-04   -3.109e-03    1.730e-02    0.0000  0.6000 -0.6037  1500  -0.1483  -0.0070  -9.9000  -9.9000  0.7131  0.5770
0.010       0.9145  -0.007517  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1541  0.0000  -0.0017     1.680e-04   -3.109e-03    1.730e-02    0.0000  0.6000 -0.6037  1500  -0.1483  -0.0070  -9.9000  -9.9000  0.7131  0.5770
0.011       0.9187  -0.007525  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1530  0.0000  -0.0017     1.680e-04   -3.109e-03    1.731e-02    0.0000  0.6000 -0.5996  1500  -0.1481  -0.0070  -9.9000  -9.9000  0.7130  0.5771
0.012       0.9225  -0.007533  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1520  0.0000  -0.0017     1.681e-04   -3.109e-03    1.731e-02    0.0000  0.6000 -0.5959  1500  -0.1480  -0.0071  -9.9000  -9.9000  0.7130  0.5772
0.013       0.9265  -0.007540  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1511  0.0000  -0.0017     1.681e-04   -3.110e-03    1.731e-02    0.0000  0.6000 -0.5924  1500  -0.1478  -0.0071  -9.9000  -9.9000  0.7129  0.5773
0.015       0.9343  -0.007555  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1494  0.0000  -0.0017     1.682e-04   -3.110e-03    1.732e-02    0.0000  0.6000 -0.5863  1500  -0.1476  -0.0072  -9.9000  -9.9000  0.7128  0.5774
0.017       0.9427  -0.007568  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1480  0.0000  -0.0017     1.683e-04   -3.111e-03    1.733e-02    0.0000  0.6000 -0.5809  1500  -0.1474  -0.0072  -9.9000  -9.9000  0.7127  0.5775
0.020       0.9578  -0.007603  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1461  0.0000  -0.0017     1.685e-04   -3.113e-03    1.736e-02    0.0000  0.6000 -0.5739  1500  -0.1471  -0.0073  -9.9000  -9.9000  0.7126  0.5777
0.022       0.9694  -0.007640  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1486  0.0000  -0.0017     1.685e-04   -3.115e-03    1.738e-02    0.0000  0.6000 -0.5645  1501  -0.1489  -0.0073  -9.9000  -9.9000  0.7137  0.5793
0.025       0.9920  -0.007700  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1519  0.0000  -0.0017     1.686e-04   -3.118e-03    1.745e-02    0.0000  0.6000 -0.5520  1502  -0.1514  -0.0073  -9.9000  -9.9000  0.7151  0.5814
0.029       1.0297  -0.007802  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1557  0.0000  -0.0017     1.690e-04   -3.123e-03    1.754e-02    0.0000  0.6000 -0.5374  1503  -0.1542  -0.0073  -9.9000  -9.9000  0.7167  0.5838
0.032       1.0610  -0.007898  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1475  0.0000  -0.0017     1.695e-04   -3.127e-03    1.761e-02    0.0000  0.6000 -0.5245  1503  -0.1596  -0.0072  -9.9000  -9.9000  0.7194  0.5875
0.035       1.1006  -0.008007  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1348  0.0000  -0.0017     1.700e-04   -3.135e-03    1.771e-02    0.0000  0.6000 -0.5111  1502  -0.1661  -0.0071  -9.9000  -9.9000  0.7226  0.5918
0.040       1.1711  -0.008203  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1160  0.0000  -0.0017     1.709e-04   -3.153e-03    1.788e-02    0.0000  0.6000 -0.4912  1502  -0.1758  -0.0069  -9.9000  -9.9000  0.7274  0.5982
0.045       1.2462  -0.008412  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0994  0.0000  -0.0017     1.718e-04   -3.174e-03    1.807e-02    0.0000  0.6000 -0.4737  1502  -0.1843  -0.0067  -9.9000  -9.9000  0.7407  0.6147
0.050       1.3193  -0.008607  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0845  0.0000  -0.0017     1.729e-04   -3.188e-03    1.823e-02    0.0000  0.6000 -0.4580  1501  -0.1920  -0.0065  -9.9000  -9.9000  0.7526  0.6295
0.055       1.3879  -0.008781  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0713  0.0000  -0.0017     1.736e-04   -3.194e-03    1.838e-02    0.0000  0.6000 -0.4547  1500  -0.2021  -0.0063  -9.9000  -9.9000  0.7614  0.6405
0.060       1.4512  -0.008931  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0593  0.0000  -0.0017     1.728e-04   -3.204e-03    1.865e-02    0.0000  0.6000 -0.4517  1498  -0.2113  -0.0061  -9.9000  -9.9000  0.7694  0.6505
0.065       1.5067  -0.009053  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0483  0.0000  -0.0017     1.726e-04   -3.213e-03    1.887e-02    0.0000  0.6000 -0.4490  1497  -0.2198  -0.0060  -9.9000  -9.9000  0.7767  0.6597
0.075       1.5979  -0.009201  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0285  0.0000  -0.0017     1.729e-04   -3.229e-03    1.913e-02    0.0000  0.6000 -0.4441  1494  -0.2350  -0.0057  -9.9000  -9.9000  0.7899  0.6761
0.085       1.6660  -0.009252  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0339  0.0000  -0.0017     1.744e-04   -3.237e-03    1.917e-02    0.0000  0.6000 -0.4629  1488  -0.2412  -0.0057  -9.9000  -9.9000  0.7932  0.6809
0.100       1.7330  -0.009259  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0408  0.0000  -0.0017     1.759e-04   -3.245e-03    1.911e-02    0.0000  0.6000 -0.4872  1479  -0.2492  -0.0056  -9.9000  -9.9000  0.7974  0.6872
0.110       1.7629  -0.009177  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0596  0.0000  -0.0017     1.761e-04   -3.248e-03    1.915e-02    0.0000  0.6000 -0.5089  1471  -0.2511  -0.0057  -9.9000  -9.9000  0.7927  0.6833
0.120       1.7813  -0.009085  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0768  0.0000  -0.0017     1.753e-04   -3.251e-03    1.926e-02    0.0000  0.6000 -0.5287  1463  -0.2528  -0.0057  -9.9000  -9.9000  0.7884  0.6797
0.130       1.7880  -0.008987  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.0926  0.0000  -0.0017     1.760e-04   -3.253e-03    1.912e-02    0.0000  0.6000 -0.5470  1456  -0.2543  -0.0058  -9.9000  -9.9000  0.7844  0.6765
0.150       1.7895  -0.008729  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1208  0.0000  -0.0017     1.761e-04   -3.247e-03    1.889e-02    0.0000  0.6000 -0.5796  1443  -0.2571  -0.0059  -9.9000  -9.9000  0.7773  0.6706
0.170       1.7849  -0.008484  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.1657  0.0000  -0.0031     1.746e-04   -3.236e-03    1.877e-02    0.0000  0.6000 -0.6266  1421  -0.2525  -0.0060  -9.9000  -9.9000  0.7646  0.6607
0.200       1.7751  -0.008129  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.2241  0.0000  -0.0080     1.710e-04   -3.195e-03    1.876e-02    0.0000  0.6000 -0.6876  1393  -0.2466  -0.0061  -9.9000  -9.9000  0.7481  0.6478
0.220       1.7679  -0.007908  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.2618  0.0000  -0.0120     1.699e-04   -3.173e-03    1.864e-02    0.0000  0.6000 -0.7236  1377  -0.2419  -0.0063  -9.9000  -9.9000  0.7370  0.6396
0.240       1.7593  -0.007703  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.2962  0.0000  -0.0159     1.692e-04   -3.157e-03    1.841e-02    0.0000  0.6000 -0.7564  1363  -0.2377  -0.0064  -9.9000  -9.9000  0.7268  0.6321
0.260       1.7474  -0.007512  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.3180  0.0000  -0.0198     1.679e-04   -3.162e-03    1.813e-02    0.0000  0.6000 -0.7868  1346  -0.2321  -0.0065  -9.9000  -9.9000  0.7174  0.6257
0.280       1.7332  -0.007335  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.3285  0.0000  -0.0238     1.679e-04   -3.159e-03    1.775e-02    0.0000  0.6000 -0.8152  1327  -0.2254  -0.0066  -9.9000  -9.9000  0.7086  0.6203
0.300       1.7174  -0.007174  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.3383  0.0000  -0.0279     1.686e-04   -3.141e-03    1.734e-02    0.0000  0.6000 -0.8417  1308  -0.2191  -0.0067  -9.9000  -9.9000  0.7005  0.6152
0.350       1.6736  -0.006823  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.4082  0.0000  -0.0379     1.723e-04   -3.086e-03    1.629e-02    0.0000  0.5893 -0.8788  1279  -0.2066  -0.0069  -9.9000  -9.9000  0.6831  0.6069
0.400       1.6232  -0.006533  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.4688  0.0000  -0.0475     1.712e-04   -3.047e-03    1.565e-02    0.0000  0.5800 -0.9109  1253  -0.1958  -0.0071  -9.9000  -9.9000  0.6680  0.5998
0.450       1.5730  -0.006280  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.5162  0.0000  -0.0565     1.655e-04   -3.011e-03    1.547e-02    0.0000  0.5694 -0.9417  1227  -0.1848  -0.0073  -9.9000  -9.9000  0.6556  0.5943
0.500       1.5229  -0.006059  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.5586  0.0000  -0.0650     1.550e-04   -2.964e-03    1.566e-02    0.0000  0.5600 -0.9693  1204  -0.1750  -0.0074  -9.9000  -9.9000  0.6446  0.5893
0.550       1.4728  -0.005863  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.5876  0.0000  -0.0733     1.477e-04   -2.910e-03    1.553e-02    0.0000  0.5529 -0.9801  1191  -0.1665  -0.0076  -7.5512  -7.5590  0.6354  0.5854
0.600       1.4261  -0.005685  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.6141  0.0000  -0.0814     1.454e-04   -2.875e-03    1.478e-02    0.0000  0.5465 -0.9900  1179  -0.1587  -0.0077  -5.4070  -5.4218  0.6270  0.5819
0.650       1.3758  -0.005522  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.6385  0.0000  -0.0895     1.409e-04   -2.840e-03    1.415e-02    0.0000  0.5406 -0.9991  1167  -0.1515  -0.0079  -3.4345  -3.4558  0.6193  0.5786
0.750       1.2723  -0.005212  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.6821  0.0000  -0.1044     1.275e-04   -2.727e-03    1.319e-02    0.0000  0.5300 -1.0154  1148  -0.1387  -0.0081  0.0920   0.0590   0.6055  0.5728
0.850       1.1440  -0.004891  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7173  0.0000  -0.1180     1.026e-04   -2.513e-03    1.245e-02    0.0000  0.5169 -1.0305  1131  -0.1241  -0.0083  0.2116   0.1238   0.5943  0.5669
1.000       0.9075  -0.004428  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7630  0.0000  -0.1360     3.420e-05   -1.965e-03    1.227e-02    0.0000  0.5000 -1.0500  1110  -0.1052  -0.0084  0.3670   0.2080   0.5797  0.5593
1.100       0.7354  -0.004103  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7800  0.0000  -0.1465    -3.040e-05   -1.493e-03    1.338e-02    0.0000  0.4812 -1.0489  1101  -0.0950  -0.0083  0.4307   0.2317   0.5717  0.5545
1.200       0.5857  -0.003822  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.7956  0.0000  -0.1559    -1.122e-04   -9.342e-04    1.591e-02    0.0000  0.4640 -1.0479  1093  -0.0858  -0.0081  0.4889   0.2534   0.5644  0.5501
1.300       0.4481  -0.003562  6.75   4.5    -0.7627  0.22  -0.0209  -0.3309  2.8099  0.0000  -0.1644    -1.897e-04   -4.667e-04    1.895e-02    0.0000  0.4482 -1.0470  1086  -0.0772  -0.0080  0.5424   0.2734   0.5577  0.5460
1.500       0.2021  -0.003244  6.75   4.5    -0.7626  0.22  -0.0209  -0.3309  2.8355  0.0000  -0.1792    -3.026e-04    1.986e-04    2.302e-02    0.0000  0.4200 -1.0454  1072  -0.0620  -0.0077  0.6380   0.3090   0.5457  0.5388
1.700      -0.0132  -0.003000  6.75   4.5    -0.7622  0.22  -0.0209  -0.3309  2.8624  0.0000  -0.1914    -3.802e-04    6.619e-04    2.494e-02    0.0000  0.3895 -1.0427  1045  -0.0507  -0.0064  0.7394   0.3408   0.5362  0.5324
2.000      -0.2927  -0.002803  6.75   4.5    -0.7595  0.22  -0.0209  -0.3309  2.8973  0.0000  -0.2062    -4.649e-04    1.213e-03    2.586e-02    0.0000  0.3500 -1.0392  1009  -0.0361  -0.0048  0.8710   0.3820   0.5239  0.5240
2.200      -0.4566  -0.002712  6.7665 4.5    -0.7567  0.22  -0.0209  -0.3309  2.8994  0.0000  -0.2143    -5.032e-04    1.549e-03    2.533e-02    0.0000  0.3147 -1.0326  989   -0.0308  -0.0041  0.9331   0.4135   0.5180  0.5180
2.400      -0.6062  -0.002615  6.7815 4.5    -0.7535  0.22  -0.0209  -0.3309  2.9013  0.0000  -0.2211    -5.111e-04    1.845e-03    2.269e-02    0.0000  0.2826 -1.0266  970   -0.0260  -0.0035  0.9897   0.4423   0.5125  0.5126
2.600      -0.7439  -0.002463  6.7953 4.5    -0.7472  0.22  -0.0209  -0.3309  2.9030  0.0000  -0.2268    -4.640e-04    2.079e-03    1.563e-02    0.0000  0.2529 -1.0211  953   -0.0215  -0.0029  1.0418   0.4687   0.5075  0.5076
2.800      -0.8713  -0.002292  6.8081 4.5    -0.7422  0.22  -0.0209  -0.3309  2.9046  0.0000  -0.2314    -3.883e-04    2.283e-03    6.109e-03    0.0000  0.2255 -1.0160  937   -0.0174  -0.0023  1.0901   0.4932   0.5029  0.5029
3.000      -0.9899  -0.002111  6.82   4.5    -0.7346  0.22  -0.0209  -0.3309  2.9061  0.0000  -0.2350    -3.127e-04    2.480e-03   -2.759e-03    0.0000  0.2000 -1.0112  922   -0.0136  -0.0018  1.1350   0.5160   0.4986  0.4986
3.500      -1.2550  -0.001697  6.8736 4.5    -0.7134  0.22  -0.0209  -0.3309  2.8968  0.0000  -0.2413    -1.302e-04    2.843e-03   -2.288e-02    0.0000  0.0928 -0.9888  881   -0.0080  -0.0017  1.2079   0.5765   0.4917  0.4917
4.000      -1.4847  -0.001348  6.92   4.5    -0.6882  0.22  -0.0209  -0.3309  2.8888  0.0000  -0.2451     4.180e-05    2.939e-03   -4.045e-02    0.0000  0.0000 -0.9694  844   -0.0032  -0.0015  1.2710   0.6290   0.4857  0.4857
4.400      -1.6486  -0.001106  6.9542 4.5    -0.6698  0.22  -0.0209  -0.3309  2.8929  0.0000  -0.2472     1.500e-04    2.822e-03   -5.119e-02    0.0000  0.0000 -0.9481  823   -0.0020  -0.0015  1.2958   0.6756   0.4828  0.4828
5.000      -1.8684  -0.001106  7.00   4.5    -0.6449  0.22  -0.0209  -0.3309  2.8984  0.0000  -0.2498     2.338e-04    2.132e-03   -5.931e-02    0.0000  0.0000 -0.9195  793   -0.0003  -0.0014  1.3290   0.7380   0.4789  0.4789
5.500      -2.0323  -0.001106  7.0314 4.5    -0.6261  0.22  -0.0209  -0.3309  2.8969  0.0000  -0.2517     2.670e-04    1.366e-03   -6.241e-02    0.0000  0.0000 -0.8859  788   -0.0003  -0.0014  1.3290   0.7547   0.4773  0.4773
6.000      -2.1819  -0.001106  7.06   4.5    -0.6088  0.22  -0.0209  -0.3309  2.8955  0.0000  -0.2534     2.800e-04    6.464e-04   -6.331e-02    0.0000  0.0000 -0.8552  783   -0.0002  -0.0014  1.3290   0.7699   0.4758  0.4758
6.500      -2.3196  -0.001106  7.0905 4.5    -0.5926  0.22  -0.0209  -0.3309  2.8864  0.0000  -0.2549     2.597e-04    2.179e-04   -6.046e-02    0.0000  0.0000 -0.8270  779   -0.0002  -0.0014  1.3290   0.7839   0.4745  0.4744
7.500      -2.5657  -0.001106  7.145  4.5    -0.5633  0.22  -0.0209  -0.3309  2.8700  0.0000  -0.2575     1.959e-04   -4.168e-04   -5.238e-02    0.0000  0.0000 -0.7766  771   -0.0001  -0.0014  1.3290   0.8090   0.4721  0.4720
8.500      -2.7809  -0.001106  7.1907 4.5    -0.5371  0.22  -0.0209  -0.3309  2.8583  0.0000  -0.2595     1.410e-04   -6.883e-04   -4.461e-02    0.0000  0.0000 -0.7240  773   -0.0001  -0.0014  1.2655   0.7629   0.4712  0.4711
10.000     -3.0604  -0.001106  7.25   4.5    -0.5025  0.22  -0.0209  -0.3309  2.8431  0.0000  -0.2621     7.450e-05   -9.020e-04   -3.454e-02    0.0000  0.0000 -0.6558  775   0.0000   -0.0014  1.1830   0.7030   0.4700  0.4700
""")
