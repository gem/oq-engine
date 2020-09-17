
import math

import numpy as np
import pandas as pd

def HA20_Jp(eq_type, m, Dp, Drup, reg1_por, reg2_por, reg3_por, vs30, z2p5, fpeak):
    f = np.concatenate((np.array([np.nan, np.nan]), \
        10 ** np.linspace(-1, 2, num=31)))
    kappa = 0.04

    b1 = -1.3
    b2 = -0.5
    Rt = (150, 250, 50)[eq_type]

    dsigma = _Dsigma_HA20_Jp(eq_type, Dp)
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

def _PGA_rock_HA20_Jp(eq_type, m, Dp, Drup, reg1_por, reg2_por, reg3_por):
    kappa = 0.04

    b1 = -1.3
    b2 = -0.5
    Rt = (150, 250, 50)[eq_type]

    dsigma = _Dsigma_HA20_Jp(eq_type, Dp)
    fm = _FM_HA18(m)
    fz = _FZ_HA18(m, Drup, b1, b2, Rt)
    fdsigma = _FDS_HA18(m, dsigma)
    fkappa = _Fkp_HA18(m, dsigma, kappa)
    fgamma = _Fgamma_HA20_Jp(eq_type, Drup, reg1_por, reg2_por, reg3_por)
    Cc = _Cc_HA20_Jp(eq_type)
    Clf = _Clf_HA20_Jp(eq_type, m)
    Chf = _Chf_HA20_Jp()
    fsref = _FSref_HA20_Jp()
    f_all = fm + fz + fdsigma + fkappa + fgamma + Cc + Clf + Chf + fsref

    return 10 ** f_all[1]

def HA20_sigma(eq_type):
    data = pd.read_csv('Sigma_Model.csv', index_col=0)
    tau = data.tou_ln.values
    phis2s = data.phis2s_ln.values
    phiss = data.iloc[:, eq_type + 2].values
    phi = np.sqrt(phis2s ** 2 + phiss ** 2)
    sigma = data.iloc[:, eq_type + 5].values
    return sigma, tau, phi, phiss, phis2s


def _Cc_HA20_Jp(eq_type):
    # interface, in-slab, crustal
    return (0.85, 0.9, 0.45)[eq_type]

def _Chf_HA20_Jp():
    return pd.read_csv('Chf_Japan.csv', index_col=0).Chf.values

def _Clf_HA20_Jp(eq_type, m):
    coeff = pd.read_csv('Clf_coeff_Japan.csv', index_col=0)

    assert 0 <= eq_type <= 2
    clf0 = coeff.iloc[:, eq_type * 2].values
    clf1 = coeff.iloc[:, eq_type * 2 + 1].values
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
        [55, 90, 30]])[:, eq_type]

    out = cd0
    if dp > dp0:
        out += cd1 * (min(dp, dp1) - dp0)
    return 10 ** out

def _FDS_HA18(m, dsigma):
    coeff = pd.read_csv('Fdsigma_coeff.csv', index_col=0)
    # why is this going through all IMs?
    fds = np.zeros(33)
    for i in range(33):
        eds1 = np.polyval(coeff.iloc[i, 4::-1].values, m)
        eds2 = np.polyval(coeff.iloc[i, 9:4:-1].values, m)
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
            out[i] = cfp0 + cfp1 * math.log10(x1 / x0) \
                + cfp2 * math.log10(xi / x1)
        else:
            out[i] = cfp0 + cfp1 * math.log10(x1 / x0) \
                + cfp2 * math.log10(x2 / x1) + cfp3 * math.log10(xi / x2)

    return out

def _Fgamma_HA20_Jp(eq_type, Drup, reg1_por, reg2_por, reg3_por):
    coeff = pd.read_csv('Fgamma_coeff_Japan.csv', index_col=0)

    i0 = 3 * eq_type
    gamma1 = coeff.iloc[:, i0].values
    gamma2 = coeff.iloc[:, i0 + 1].values
    gamma3 = coeff.iloc[:, i0 + 2].values

    reg_por_all = reg1_por + reg2_por + reg3_por
    return gamma1 * Drup * reg1_por / reg_por_all \
        + gamma2 * Drup * reg2_por / reg_por_all \
        + gamma3 * Drup * reg3_por / reg_por_all

def _Fkp_HA18(m, ds, kp):
    coeff = pd.read_csv('Fkappa_coeff.csv', index_col=0)
    l10kp = math.log10(kp)

    fkp = np.zeros(33)
    for k in range(33):
        i1 = 0
        p = np.zeros((4, 4))
        ek0 = np.zeros(4)
        for i in range(4):
            for j in range(4):
                i1 += 1
                p[i, j] = np.polyval(coeff.iloc[k, (i1 - 1) * 3 : i1 * 3].values[::-1], \
                    math.log10(ds))
            ek0[i] = np.polyval(p[i, ::-1], math.log10(m))
        ek00 = 3 * ek0[0] - 9 * ek0[1] + 27 * ek0[2] - 81 * ek0[3]
        fkp[k] = ek00 + ek0[0] * l10kp + ek0[1] * l10kp ** 2 \
            + ek0[2] * l10kp ** 3 + ek0[3] * l10kp ** 4

    return fkp

def _FM_HA18(m):
    coeff = pd.read_csv('FM_coeff.csv', index_col=0)
    mh = coeff.Mh.values
    e0 = coeff.e0.values
    e1 = coeff.e1.values
    e2 = coeff.e2.values
    e3 = coeff.e3.values

    fm = np.zeros(33)
    for i in range(33):
        if m <= mh[i]:
            fm[i] = e0[i] + e1[i] * (m - mh[i]) + e2[i] * (m - mh[i]) ** 2
        else:
            fm[i] = e0[i] + e3[i] * (m - mh[i])

    return fm

def _FSnonlin_SS14(vs30, PGA_rock):
    # this function just returns 0 always?

    coeff = pd.read_csv('Fnonlin_coeff.csv', index_col=0)
    f1 = coeff.f1.values
    f3 = coeff.f3.values
    f4 = coeff.f4.values
    f5 = coeff.f5.values

    f2 = f4 * (np.exp(f5 * (min(vs30, 760) - 360)) - np.exp(f5 * (760 - 360)))

    return f1 + f2 * np.log((PGA_rock + f3) / f3)

def _FSref_HA20_Jp():
    # crustal amplification (log10)
    return pd.read_csv('FSref_Japan.csv', index_col=0).iloc[:, 1].values

def _FVS30_HA20_Jp(vs30):
    # only returns -0?

    coeff = pd.read_csv('FVS30_coeff_Japan.csv', index_col=0)
    vref = 760
    cv1 = coeff.CV1.values
    cv2 = coeff.CV2.values
    v0 = 100
    v1 = 250
    v2 = 1000

    out = np.zeros(33)
    for i in range(33):
        if vs30 <= v0:
            out[i] = cv1[i] * math.log10(v0 / vref) \
                + (cv2[i] - cv1[i]) * math.log10(v1 / vref)
        elif vs30 <= v1:
            out[i] = cv1[i] * math.log10(vs30 / vref) \
                + (cv2[i] - cv1[i]) * math.log10(v1 / vref)
        elif vs30 <= v2:
            out[i] = cv2[i] * math.log10(vs30 / vref)
        else:
            out[i] = cv2[i] * math.log10(v2 / vref)

    return out

def _FZ2p5_HA20_Jp(z2p5):
    coeff = pd.read_csv('FZ2p5_coeff_Japan.csv', index_col=0)
    cz0 = coeff.CZ0.values
    cz1 = coeff.CZ1.values
    cz2 = coeff.CZ2.values
    zx0 = 150
    zx1 = 800
    zx2 = 4200

    out = np.zeros(33)
    for i in range(33):
        if z2p5 < 0:
            pass
        elif z2p5 <= zx0:
            out[i] = cz0[i]
        elif z2p5 <= zx1:
            out[i] = cz0[i] + cz1[i] * math.log10(z2p5 / zx0)
        elif z2p5 <= zx2:
            out[i] = cz0[i] + cz1[i] * math.log10(zx1 / zx0) \
                + cz2[i] * math.log10(z2p5 / zx1)
        else:
            out[i] = cz0[i] + cz1[i] * math.log10(zx1 / zx0) \
                + cz2[i] * math.log10(zx2 / zx1)

    return out

def _FZ_HA18(m, Drup, b1, b2, rt):
    coeff = pd.read_csv('FZ_coeff.csv', index_col=0)
    h = 10 ** (-0.405 + 0.235 * m)
    b3 = coeff.b3.values
    b4 = coeff.b4.values
    ref = math.sqrt(Drup ** 2 + h ** 2)
    rref = math.sqrt(1 ** 2 + h ** 2)
    if ref <= rt:
        return b1 * math.log10(ref) + (b3 + b4 * m) * math.log10(ref / rref)
    else:
        return b1 * math.log10(rt) + b2 * math.log10(ref / rt) \
            + (b3 + b4 * m) * math.log10(ref / rref)
