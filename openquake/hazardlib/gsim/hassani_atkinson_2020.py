

import numpy as np
import pandas as pd

def HA20_Jp(eq_type,m,Dp,Drup,reg1_por,reg2_por,reg3_por,vs30,z2p5,fpeak):
    f = np.array(np.nan, np.nan, 10 ** np.linspace(-1, 2, num=31))
    kappa = csvread('Kappa_BC_Japan.csv',1,0)

    fz_coeff_japan = csvread('FZ_coeff_Japan.csv',1,1)
    b1 = fz_coeff_japan[eq_type, 1]
    b2 = fz_coeff_japan[eq_type, 2]
    Rt = fz_coeff_japan[eq_type, 3]

    dsigma = Dsigma_HA20_Jp(eq_type, Dp)

    fm = _FM_HA18(m)
    fz = _FZ_HA18(m, Drup, b1, b2, Rt)
    fdsigma = _FDS_HA18(m, dsigma)
    fkappa = _Fkp_HA18(m, dsigma, kappa)
    fgamma = _Fgamma_HA20_Jp(eq_type, Drup, reg1_por, reg2_por, reg3_por)
    Cc = _Cc_HA20_Jp(eq_type)
    Clf = _Clf_HA20_Jp(eq_type, m)
    Chf = _Chf_HA20_Jp()
    fsref = _FSref_HA20_Jp()
    PGA_rock = _PGA_rock_HA20_Jp(eq_type, m, Dp, Drup, reg1_por, reg2_por, reg3_por)
    fsnonlin = _FSnonlin_SS14(vs30,PGA_rock)
    fvs30 = _FVS30_HA20_Jp(vs30)
    fz2p5 = _FZ2p5_HA20_Jp(z2p5)
    ffpeak = _Ffpeak_HA20_Jp(fpeak)

    f_all = fm + fdsigma + fz + fkappa + fgamma + Cc + Clf + Chf + fsref + fvs30 + fz2p5 + ffpeak + fsnonlin

    sa = 10 ** f_all
    return sa, f

def HA20_sigma(eq_type):
    data = csvread('Sigma_Model.csv',1,1)
    tau = data[:, 0]
    phis2s = data[:, 1]
    phiss = data[:, eq_type + 2]
    phi = math.sqrt(phis2s ** 2 + phiss ** 2)
    sigma = data[:, eq_type + 5]
    return sigma, tau, phi, phiss, phis2s


def _Cc_HA20_Jp(eq_type):
    # interface, in-slab, crustal
    return np.repeat((0.85, 0.9, 0.45)[eq_type], 33)

def _Chf_HA20_Jp():
    return csvread('Chf_Japan.csv',1,1)

def _Clf_HA20_Jp(eq_type, m):
    coeff = csvread('Clf_coeff_Japan.csv',1,1)
    
    assert 0 <= eq_type <= 2
    clf0 = coeff[:, eq_type * 2]
    clf1 = coeff[:, eq_type * 2 + 1]
    mlf0 = 5.5
    mlf1 = 7
    
    out = np.copy(clf0)
    if m > mlf0:
        return out + clf1 * (min(m, mlf1) - mlf0)
    return out

def _Dsigma_HA20_Jp(eq_type, dp):
    # interface, in-slab, crustal
    cd0, cd1, dp0, dp1 = np.array([[1.606, 1.9241, 2.5011],
        [0.0097, 0.0133, 0],
        [25, 40, 0],
        [55, 90, 30]])[:, 0]

    out = cd0
    if dp > dp0:
        out += cd1 * (min(dp, dp1) - dp0)
    return 10 ** out

def _FDS_HA18(m, dsigma):
    coeff = csvread('Fdsigma_coeff.csv',1,1)
    # why is this going through all IMs?
    fds = np.zeros(coeff.count)
    for i in range(coeff.count):
        eds1 = np.polyval(coeff[i, 4::-1], m)
        eds2 = np.polyval(coeff(i, 9:4:-1], m)
        eds0 = -2 * eds1 - 4 * eds2
        fds[i] = eds0 + eds1 * math.log10(dsigma) + eds2 * math.log10(dsigma) ** 2
    return fds

def _Ffpeak_HA20_Jp(fpeak):
    f = 10 ** np.linspace(-1, 2, num=31)
    cfp0 = -0.011
    cfp1 = 0.421
    cfp2 = -0.604
    cfp3 = 0.086
    x0 = 0.5
    x1 = 1.0
    x2 = 2.5
    
    x = fpeak / f
    out = np.zeros(33)
    for i in range(2, len(out)):
        xi = x[i - 2]
        if xi < 0:
            pass
        elif xi <= x0:
            out[i] = cfp0
        elif xi <= x1:
            out[i] = cfp0 + cfp1 * math.log10(xi / x0)
        elif xi <= x2:
            out[i] = cfp0 + cfp1 * math.log10(x1 / x0) + cfp2 * math.log10(xi / x1)
        else:
            out[i] = cfp0 + cfp1 * math.log10(x1 / x0) + cfp2 * math.log10(x2 / x1) + cfp3 * math.log10(xi / x2)

    return out

