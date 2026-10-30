# The Hazard Library
# Copyright (C) 2012-2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Horizontal-component intensity-measure-component (IMC) conversion.

Only pairs for which Beyer & Bommer (2006) or Boore & Kishida (2017)
publish a direct ratio are supported currently. The eight directly
tabulated pairs, with their SA source (PGA/PGV sources noted
separately below) are:

    GMRotI50 <-> GEOM        (SA: BB06 Table 3)
    RANDOM   <-> GEOM        (SA: BB06 Table 3; PGA/PGV: BB06 Table 2)
    RotD50   <-> GEOM        (SA: BK17 Table 2 col 2)
    RotD50   <-> GMRotI50    (SA: BK17 Table 2 col 1)
    RotD100  <-> RotD50      (SA: BK17 Table 2 col 3)
    Larger   <-> GEOM        (SA: BK17 Table 2 col 5)
    Larger   <-> GMRotI50    (SA: BK17 Table 2 col 4)
    Larger   <-> RotD50      (SA: BK17 Table 2 col 6)

Any other pair (e.g. RANDOM <-> RotD50, RotD100 <-> GEOM) is left
unconverted; callers skip the GSIM (i.e., no conversion) and log a
notice.

Every direct ratio is a Ratio record keyed by (source, target). The
triple returned by ratio_at(imt) is (conv_median, conv_sigma,
ratio_sigma), where:

    conv_median  : median of source_IM / target_IM
    conv_sigma   : standard deviation of ln(ratio)
    ratio_sigma  : total_sigma(source) / total_sigma(target)

PGV for every BK17-sourced pair, plus PGA and PGV for the GMRotI50/GEOM
pair (whose SA is BB06 Table 3 but whose PGA/PGV BB06 does not publish),
come from the BK17 electronic supplement, specifically the
Rrup <= 200 km, M 2-9 all-magnitude CSVs:

    nga-w2.gmean.Rot_Ratios.Sdev.RrupMin_0000.RrupMax_0200.Mmin_2.00.Mmax_9.00.4paper.csv
    nga-w2.gmean.Larger_Ratios.Sdev.RrupMin_0000.RrupMax_0200.Mmin_2.00.Mmax_9.00.4paper.csv

BK17 PGA (for the six BK17-sourced pairs) is kept at R1, the first
knot of the SA line-segment fit. Equation (2) clamps to R1 at T=0,
so R1 is the mathematically consistent T->0 plateau. The real
e-supp PGA differs by ~0.5-1.5% but to minimise Mosaic/AELO changes
we retain the R1 values.

For PGV from the e-supplement, ratio_sigma is kept at 1.0 as an
approximation; the full propagation per BK17 eq. (3) inflates the
output sigma by only ~1% across all periods (BK17 p. 339 Table 3).
BK17 SA uses conv_sigma=0, ratio_sigma=1 for the same reason: the
~1% figure applies at SA periods too.

References
----------
Beyer, K., and J. J. Bommer (2006). Relationships between median values
    and between aleatory variabilities for different definitions of the
    horizontal component of motion, Bulletin of the Seismological
    Society of America 96(4A), 1512-1522.
Boore, D. M., and T. Kishida (2017). Relations between some
    horizontal-component ground-motion intensity measures used in
    practice, Bulletin of the Seismological Society of America 107(1),
    334-343.
"""
import logging
from typing import NamedTuple
import numpy as np

from openquake.hazardlib.const import IMC


TARGET_NAMES = {
    'geometric_mean': IMC.GEOMETRIC_MEAN,
    'gmroti50': IMC.GMRotI50,
    'rotd50': IMC.RotD50,
    'rotd100': IMC.RotD100,
    'greater_of_two_horizontal': IMC.GREATER_OF_TWO_HORIZONTAL,
    'random_horizontal': IMC.RANDOM_HORIZONTAL,
}


class Ratio(NamedTuple):
    paper: str   # inline citation, e.g. 'BK17 Table 2 col 1 + e-supp'
    kind: str    # 'bb06' or 'bk17' selects the SA evaluator
    sa: tuple    # paper-specific SA coefficients
    pga: tuple   # (conv_median, conv_sigma, ratio_sigma) at PGA
    pgv: tuple   # (conv_median, conv_sigma, ratio_sigma) at PGV


_RATIOS = {
    (IMC.GMRotI50, IMC.GEOMETRIC_MEAN): Ratio(
        paper='SA: BB06 Table 3 | PGA/PGV: BK17 e-supp (GMRotI50/GMAR)',
        kind='bb06',
        sa=(1.0, 1.0, 0.03, 0.04, 1.0),
        pga=(1.013, 0.076, 1.0),
        pgv=(1.011, 0.085, 1.0)),
    (IMC.RANDOM_HORIZONTAL, IMC.GEOMETRIC_MEAN): Ratio(
        paper='BB06 Tables 2, 3 (Random/GMxy)',
        kind='bb06',
        sa=(1.0, 1.0, 0.07, 0.11, 1.05),
        pga=(1.0, 0.07, 1.03),
        pgv=(1.0, 0.09, 1.03)),
    # BK17 PGA uses R1 (short-period SA plateau from Table 2) as a proxy
    # rather than the e-supp PGA value, to avoid regenerating ~40 QA
    # expected files pinned to the historical R1-proxy behavior. The real
    # e-supp PGA differs by ~0.5-1.5%; see hconv.md "Accuracy upgrades"
    # for the per-pair comparison. PGV is sourced from the e-supp directly.
    (IMC.RotD50, IMC.GMRotI50): Ratio(
        paper='BK17 Table 2 col 1 (RotD50/GMRotI50); PGA=R1 proxy, PGV from e-supp',
        kind='bk17',
        sa=(0.06, 0.999, 0.71, 1.019, 4.21, 1.028, 10.00, 1.057, 1.057),
        pga=(0.999, 0.0, 1.0),
        pgv=(1.010, 0.061, 1.0)),
    (IMC.RotD50, IMC.GEOMETRIC_MEAN): Ratio(
        paper='BK17 Table 2 col 2 (RotD50/GMAR); PGA=R1 proxy, PGV from e-supp',
        kind='bk17',
        sa=(0.09, 1.009, 0.58, 1.028, 4.59, 1.042, 8.93, 1.077, 1.077),
        pga=(1.009, 0.0, 1.0),
        pgv=(1.021, 0.088, 1.0)),
    (IMC.RotD100, IMC.RotD50): Ratio(
        paper='BK17 Table 2 col 3 (RotD100/RotD50); PGA=R1 proxy, PGV from e-supp',
        kind='bk17',
        sa=(0.12, 1.188, 0.41, 1.225, 3.14, 1.241, 10.00, 1.287, 1.287),
        pga=(1.188, 0.0, 1.0),
        pgv=(1.218, 0.087, 1.0)),
    (IMC.GREATER_OF_TWO_HORIZONTAL, IMC.GMRotI50): Ratio(
        paper='BK17 Table 2 col 4 (Larger/GMRotI50); PGA=R1 proxy, PGV from e-supp',
        kind='bk17',
        sa=(0.08, 1.106, 0.56, 1.158, 4.40, 1.178, 8.70, 1.241, 1.241),
        pga=(1.106, 0.0, 1.0),
        pgv=(1.138, 0.114, 1.0)),
    # BB06 Env/GMxy == BK17 Larger/GMAR. BB06 flags this ratio as non-lognormal
    # and advises against GM->Env in PSHA; BK17 refits from NGA-West2 and used
    (IMC.GREATER_OF_TWO_HORIZONTAL, IMC.GEOMETRIC_MEAN): Ratio(
        paper='BK17 Table 2 col 5 (Larger/GMAR); PGA=R1 proxy, PGV from e-supp',
        kind='bk17',
        sa=(0.10, 1.117, 0.53, 1.165, 4.48, 1.195, 8.70, 1.266, 1.266),
        pga=(1.117, 0.0, 1.0),
        pgv=(1.150, 0.129, 1.0)),
    (IMC.GREATER_OF_TWO_HORIZONTAL, IMC.RotD50): Ratio(
        paper='BK17 Table 2 col 6 (Larger/RotD50); PGA=R1 proxy, PGV from e-supp',
        kind='bk17',
        sa=(0.10, 1.107, 0.45, 1.133, 4.36, 1.149, 8.78, 1.178, 1.178),
        pga=(1.107, 0.0, 1.0),
        pgv=(1.127, 0.098, 1.0)),
}


### CONVERTERS ###
def _bb06_sa(C, T):
    """
    BB06 Table 3 SA ratio.
    """
    # flat below T=0.15 s and above T=0.80 s; linear in log10(T) between
    if T <= 0.15:
        return C[0], C[2], C[4]
    if T >= 0.80:
        return C[1], C[3], C[4]
    w = np.log10(T / 0.15) / np.log10(0.80 / 0.15)
    return C[0] + (C[1] - C[0]) * w, C[2] + (C[3] - C[2]) * w, C[4]


def _bk17_sa(C, T):
    """
    BK17 Table 2 SA ratio (eq. 2); sigma unchanged by convention.
    """
    # four line segments between knots (T1,R1)..(T4,R4), flat at R5 beyond
    t1 = C[1] + (C[3] - C[1]) / np.log(C[2] / C[0]) * np.log(T / C[0])
    t2 = C[3] + (C[5] - C[3]) / np.log(C[4] / C[2]) * np.log(T / C[2])
    t3 = C[5] + (C[7] - C[5]) / np.log(C[6] / C[4]) * np.log(T / C[4])
    t4 = C[8]
    conv_median = float(np.maximum(
        C[1], np.maximum(np.minimum(t1, t2), np.minimum(t3, t4))))
    return conv_median, 0.0, 1.0


def ratio_at(r, imt):
    """
    Evaluate a Ratio object at the given IMT and return
    (conv_median, conv_sigma, ratio_sigma).
    """
    if imt.name == 'PGA':
        return r.pga
    if imt.name == 'PGV':
        return r.pgv
    if imt.name == 'SA':
        if r.kind == 'bb06':
            return _bb06_sa(r.sa, imt.period)
        return _bk17_sa(r.sa, imt.period)
    return 1.0, 0.0, 1.0


def can_convert(src_imc, tgt_imc):
    """
    :returns: True if a direct ratio exists between src_imc and tgt_imc
        (in either direction), or they are the same IMC.
    """
    return (src_imc is tgt_imc
            or (src_imc, tgt_imc) in _RATIOS
            or (tgt_imc, src_imc) in _RATIOS)


def apply_conversion(src_imc, tgt_imc, imt):
    """
    Build the sequence of steps that converts a GSIM prediction from
    src_imc to tgt_imc at the given IMT.

    :param src_imc: the GSIM's native IMC
    :param tgt_imc: the desired target IMC
    :param imt: the intensity measure type
    :returns:
        A tuple of steps for "apply_in_place" function to use.
    """
    if src_imc is tgt_imc:
        return ()
    r = _RATIOS.get((src_imc, tgt_imc))
    if r is not None:
        return (('forward',) + ratio_at(r, imt),)
    r = _RATIOS.get((tgt_imc, src_imc))
    if r is not None:
        return (('reverse',) + ratio_at(r, imt),)
    raise KeyError((src_imc, tgt_imc))


def apply_in_place(mean_sig, steps):
    """
    Apply a sequence of steps to a (mean, sigma) pair in place. Each step
    is (kind, conv_median, conv_sigma, ratio_sigma):

        "forward": me -= ln(conv_median)
                   si = sqrt((si**2 - conv_sigma**2) / ratio_sigma**2)

        "reverse": me += ln(conv_median)
                   si = sqrt(si**2 * ratio_sigma**2 + conv_sigma**2)
    """
    me, si = mean_sig
    for kind, conv_median, conv_sigma, ratio_sigma in steps:
        if kind == 'forward':
            me[:] = np.log(np.exp(me) / conv_median)
            si[:] = ((si ** 2 - conv_sigma ** 2) / ratio_sigma ** 2) ** 0.5
        else:  # 'reverse'
            me[:] = np.log(np.exp(me) * conv_median)
            si[:] = (si ** 2 * ratio_sigma ** 2 + conv_sigma ** 2) ** 0.5


def target_from_name(name):
    """
    :returns: the IMC enum member for a horiz_comp_to value, or None if
        the value is empty (no conversion requested).
    """
    if not name:
        return None
    try:
        return TARGET_NAMES[name]
    except KeyError:
        raise ValueError(
            f"horiz_comp_to={name!r} is not a supported target IMC; "
            f"choose one of {sorted(TARGET_NAMES)}")


# Triples (gsim_cls_name, src_imc, tgt_imc) already warned about; the
# same ContextMaker setup can run many times (per TRT, after
# restrict_imts, etc.) and we only want one message per unique case.
_LOGGED_UNSUPPORTED = set()


def log_unsupported(gsim_cls_name, src_imc, tgt_imc):
    """
    Log once that no direct ratio connects a GSIM's native IMC to the
    requested target. Repeated calls for the same triple are silent.
    """
    key = (gsim_cls_name, src_imc, tgt_imc)
    if key in _LOGGED_UNSUPPORTED:
        return
    _LOGGED_UNSUPPORTED.add(key)
    logging.info(
        f'No direct ratio from {src_imc.name} to {tgt_imc.name}; '
        f'{gsim_cls_name} contribution left unchanged')
