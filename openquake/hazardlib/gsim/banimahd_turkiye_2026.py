# -*- coding: utf-8 -*-
"""
Banimahd et al. (2026) Turkiye ANN-based Ground-Motion Model
=============================================================

This module implements the ANN-based, region-specific ground-motion model
for Turkiye by Banimahd et al. (2026) as an OpenQuake GSIM/GMPE.

Reference
---------
Banimahd A, Karimzadeh S, et al. (2026).
"Artificial neural network-based non-parametric ground motion models for
 multiple intensity measures in Turkiye."
Engineering Applications of Artificial Intelligence.

Model overview
--------------
- Trained on strong-motion data from Turkiye.
- ML regressor: ensemble of 10 feed-forward neural networks.
- Inputs (in the order used for training and ONNX):
    1. FD         : focal depth (km)
    2. FM         : fault mechanism (1=Normal, 2=Reverse, 3=StrikeSlip)
    3. Mw         : moment magnitude
    4. RJB        : Joyner-Boore distance (km)
    5. Vs30       : averaged shear-wave velocity in the top 30 m (m/s)

Outputs (25 values, in ln-space):
    - PGA, PSA(T): ln(g)
    - PGV       : ln(cm/s)
"""

import os
import csv
import numpy as np
import onnxruntime as ort

from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

# ---------------------------------------------------------------------
# Choose a suitable IM component, robust across OQ versions
# ---------------------------------------------------------------------
_IMC_GMEAN = const.IMC.GEOMETRIC_MEAN

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
_DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "banimahd_turkiye_2026_data",
)

_ONNX_FILE = os.path.join(_DATA_DIR, "onnx_models", "GMM_Turkiye_2026.onnx")
_STDS_FILE = os.path.join(_DATA_DIR, "stds.csv")


# ---------------------------------------------------------------------
# Load standard deviation tables from stds.csv
# ---------------------------------------------------------------------
_SIGMA_INTRA = {}
_TAU_INTER = {}
_PHI_TOTAL = {}


def _load_stddev_tables():
    if not os.path.exists(_STDS_FILE):
        raise IOError(f"Cannot find stds.csv at {_STDS_FILE}")

    with open(_STDS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["ID"]
            _SIGMA_INTRA[key] = float(row["Sigma"])
            _TAU_INTER[key] = float(row["Tau"])
            _PHI_TOTAL[key] = float(row["Phi"])


_load_stddev_tables()


# ---------------------------------------------------------------------
# ONNX session cache
# ---------------------------------------------------------------------
_SESSION = None


def _get_session():
    global _SESSION
    if _SESSION is None:
        if not os.path.exists(_ONNX_FILE):
            raise IOError(f"Cannot find ONNX file: {_ONNX_FILE}")
        opt = ort.SessionOptions()
        opt.intra_op_num_threads = 1
        opt.inter_op_num_threads = 1
        _SESSION = ort.InferenceSession(_ONNX_FILE, sess_options=opt)
    return _SESSION


__all__ = ["Banimahd2026Turkiye"]


# ---------------------------------------------------------------------
# GSIM class
# ---------------------------------------------------------------------
class Banimahd2026Turkiye(GMPE):
    """
    ANN-based Ground-Motion Model for Turkiye (Banimahd et al., 2026).

    This GSIM wraps an ensemble of 10 feed-forward neural networks exported
    to a single ONNX file. It returns the mean ln(IM) and standard deviations
    (intra-event, inter-event, total) for each requested IMT.
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = _IMC_GMEAN

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.INTRA_EVENT,
        const.StdDev.INTER_EVENT,
        const.StdDev.TOTAL,
    }

    DEFINED_FOR_REFERENCE_VELOCITY = 760.0

    REQUIRES_RUPTURE_PARAMETERS = {"mag", "hypo_depth", "rake"}
    REQUIRES_DISTANCES = {"rjb"}
    REQUIRES_SITES_PARAMETERS = {"vs30"}

    _PERIODS = [0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4,
                0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Compute mean and standard deviations for all requested IMTs at once.

        Parameters
        ----------
        ctx : np.recarray
            Context object with rupture, distance, and site parameters.
        imts : list
            List of intensity measure types.
        mean : np.ndarray
            Output array for mean values, shape (M, N).
        sig : np.ndarray
            Output array for total stddev, shape (M, N).
        tau : np.ndarray
            Output array for inter-event stddev, shape (M, N).
        phi : np.ndarray
            Output array for intra-event stddev, shape (M, N).
        """
        # Number of sites
        N = len(ctx)

        mw = ctx.mag.astype(float)
        rjb = ctx.rjb.astype(float)
        vs30 = ctx.vs30.astype(float)
        fd = ctx.hypo_depth.astype(float)
        rake = ctx.rake.astype(float)

        # Fault mechanism (vectorized)
        # Normal: rake close to -90
        # Reverse: rake close to +90
        # Strike-slip: rake close to 0 or ±180
        fm = np.ones(N, dtype=np.float32)
        fm[(rake > -30.0) & (rake < 30.0)] = 3.0
        fm[rake > 30.0] = 2.0
        fm[(rake > 150.0) | (rake < -150.0)] = 3.0

        # Build input matrix (FD, FM, Mw, RJB, VS30)
        X = np.column_stack([fd, fm, mw, rjb, vs30]).astype(np.float32)
     
        # Run ONNX inference once for all 25 outputs
        sess = _get_session()
        input_name = sess.get_inputs()[0].name
        output_name = sess.get_outputs()[0].name
        out = sess.run([output_name], {input_name: X})[0]

        # Fill mean/sig/tau/phi for each requested IMT
        for m, imt in enumerate(imts):
            imt_str = imt.string
         
            if imt_str == "PGA":
                out_idx = 0
                key = "ln(PGA)"
            elif imt_str == "PGV":
                out_idx = 1
                key = "ln(PGV)"
            elif imt_str.startswith("SA(") and imt_str.endswith(")"):
                period = float(imt_str[3:-1])
                out_idx = 7 + self._PERIODS.index(period)
                key = f"ln(PSA={period})"
            else:
                raise ValueError(f"IMT {imt_str} not supported")

            mean[m, :] = out[:, out_idx]
            sig[m, :]  = _PHI_TOTAL[key]     # TOTAL
            tau[m, :]  = _TAU_INTER[key]     # INTER-EVENT
            phi[m, :]  = _SIGMA_INTRA[key]   # INTRA-EVENT
         
