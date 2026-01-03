# -*- coding: utf-8 -*-
"""
Mohammadi et al. (2023) Turkiye ML-based Ground-Motion Model
"""

import os
import csv
import numpy as np
import onnxruntime as ort

from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

# MinMaxScaler parameters (from scx.pkl)
_DATA_MIN = np.array([4.1, 131.0, 0.1, 0.0, 0.0, 0.0], dtype=float)
_DATA_MAX = np.array([7.6, 1380.0, 199.0, 1.0, 1.0, 1.0], dtype=float)

_SCALE = np.array(
    [
        0.17142857142857146,
        0.00048038430744595686,
        0.00301659125188537,
        0.6000000000000001,
        0.6000000000000001,
        0.6000000000000001,
    ],
    dtype=float,
)

_MIN = np.array(
    [-0.5028571428571429, 0.13706965572457966, 0.19969834087481148, 0.2, 0.2, 0.2],
    dtype=float,
)

# Paths
_DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "mohammadi_turkiye_2023_data",
)

_ONNX_DIR = os.path.join(_DATA_DIR, "onnx_models")
_STDS_FILE = os.path.join(_DATA_DIR, "stds.csv")


# IM component
_IMC_CANDIDATES = [
    "GMEAN",
    "GEOMETRIC_MEAN",
    "AVERAGE_HORIZONTAL",
    "HORIZONTAL",
    "RANDOM_HORIZONTAL",
]

for _name in _IMC_CANDIDATES:
    if hasattr(const.IMC, _name):
        _IMC_GMEAN = getattr(const.IMC, _name)
        break
else:
    # Fallback: first enum member (whatever it is)
    _IMC_GMEAN = list(const.IMC)[0]


def _scale_features(X: np.ndarray) -> np.ndarray:
    """
    Apply the *same* feature scaling that was used in training (scx.pkl).

    Parameters
    ----------
    X : np.ndarray, shape (N, 6)
        Columns in the following order:
            [Mw, Vs30, RJB, normal, reverse, strike_slip]

    Returns
    -------
    X_scaled : np.ndarray, shape (N, 6)
        MinMax-scaled features, consistent with the original scx.pkl:

            X_scaled = X * SCALE + MIN

    Notes
    -----
    - All 6 features are scaled simultaneously using the pre-extracted
      SCALE and MIN parameters.
    - This matches the behaviour of the original MinMaxScaler used
      when training the XGBoost models.
    """
    return X * _SCALE + _MIN


_BUNDLED_MODEL_NAME = "mohammadi_turkiye_2023_bundled.onnx"
_SESS_CACHE = None  # Will hold the single session


def _get_session() -> ort.InferenceSession:
    """
    Return the cached ONNXRuntime session for the bundled model.
    """
    global _SESS_CACHE
    if _SESS_CACHE is None:
        full_path = os.path.join(_DATA_DIR, _BUNDLED_MODEL_NAME)
        if not os.path.exists(full_path):
            raise IOError(f"Cannot find bundled ONNX file: {full_path}")

        opt = ort.SessionOptions()
        opt.intra_op_num_threads = 1
        opt.inter_op_num_threads = 1

        _SESS_CACHE = ort.InferenceSession(full_path, sess_options=opt)

    return _SESS_CACHE


def _predict_ln_im(output_name: str, X_scaled: np.ndarray) -> np.ndarray:
    """
    Evaluate the bundled ONNX model and return ln(IM) in training units.
    """
    sess = _get_session()

    # Input name is shared and fixed by bundling script
    # It was 'float_input' in all original models.
    input_name = sess.get_inputs()[0].name  # Should be 'float_input'

    # Run inference only for the requested output
    out = sess.run([output_name], {input_name: X_scaled})[0]
    return np.asarray(out, dtype=float).reshape(-1)


def _mean_and_std_from_ctx(gsim, ctx, imt):
    """
    Core prediction logic for a single IMT, using the vectorized `ctx`
    (numpy.recarray) used by modern OpenQuake.

    Parameters
    ----------
    gsim : Mohammadi2023Turkiye instance
    ctx  : numpy.recarray
        Must provide fields: mag, rake, rjb, vs30
    imt  : IMT instance (PGA, PGV, SA(...))

    Returns
    -------
    ln_im : np.ndarray, shape (N,)
        ln(IM) in OQ units:
           - ln(PGA), ln(SA) in g
           - ln(PGV) in cm/s
    sigma_intra : np.ndarray, shape (N,)
        Intra-event stddev (σ_intra)
    tau_inter   : np.ndarray, shape (N,)
        Inter-event stddev (τ)
    phi_total   : np.ndarray, shape (N,)
        Total stddev (σ_total)
    """
    N = len(ctx)

    Mw   = np.asarray(ctx.mag,  dtype=float)
    RJB  = np.asarray(ctx.rjb,  dtype=float)
    Vs30 = np.asarray(ctx.vs30, dtype=float)
    rake = np.asarray(ctx.rake, dtype=float)

    # Fault mechanism flags (vectorized)
    normal      = np.zeros(N, dtype=float)
    reverse     = np.zeros(N, dtype=float)
    strike_slip = np.zeros(N, dtype=float)

    normal[rake < -30.0] = 1.0
    reverse[rake > 30.0] = 1.0
    strike_slip[(rake >= -30.0) & (rake <= 30.0)] = 1.0

    # Order: Mw, Vs30, RJB, normal, reverse, strike_slip
    X = np.column_stack([Mw, Vs30, RJB, normal, reverse, strike_slip])
    X_scaled = _scale_features(X).astype(np.float32)

    # IMT identification
    imt_str = str(imt)  # e.g. "PGA", "PGV", "SA(0.2)"

    if imt_str == "PGA":
        kind, period = "PGA", None
        key = "ln(PGA)"

    elif imt_str == "PGV":
        kind, period = "PGV", None
        key = "ln(PGV)"

    elif imt_str.startswith("SA(") and imt_str.endswith(")"):
        inside = imt_str[3:-1]
        period = float(inside)
        kind = "SA"
        key = f"ln(PSA={period})"

    else:
        raise ValueError(f"IMT {imt_str} not supported in Mohammadi2023Turkiye")


    # Prediction in training units, then convert to OQ units
    ln_im_train = _predict_ln_im(key, X_scaled)

    if kind in ("PGA", "SA"):
        # cm/s^2 -> g (still in ln)
        ln_im = ln_im_train - np.log(981.0)
    else:
        # PGV already in cm/s
        ln_im = ln_im_train

    # Standard deviations from stds.csv (all in ln-units)
    #   Sigma -> intra-event
    #   Tau   -> inter-event
    #   Phi   -> total
    sigma_val = gsim.sigma_intra[key]  # intra-event
    tau_val   = gsim.tau_inter[key]    # inter-event
    phi_val   = gsim.phi_total[key]    # total

    sigma_intra = np.full_like(ln_im, sigma_val)
    tau_inter   = np.full_like(ln_im, tau_val)
    phi_total   = np.full_like(ln_im, phi_val)

    return ln_im, sigma_intra, tau_inter, phi_total


class Mohammadi2023Turkiye(GMPE):
    """
    Machine-learning Ground-Motion Model for Turkiye (Mohammadi et al., 2023).

    Reference
    ---------
    Mohammadi A, Karimzadeh S, Banimahd SA, Ozsarac V, Lourenço PB (2023).
    "The potential of region-specific machine-learning-based ground motion models:
    application to Turkiye."
    Soil Dynamics and Earthquake Engineering, 172:108008.
    https://doi.org/10.1016/j.soildyn.2023.108008
    """

    # Tectonic region
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    # Intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    # Component: geometric mean or closest available
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = _IMC_GMEAN

    # Std dev types – order doesn't matter; mapping is defined in code.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.INTRA_EVENT,
        const.StdDev.INTER_EVENT,
        const.StdDev.TOTAL,
    }

    # Reference velocity (not really used but required by some tools)
    DEFINED_FOR_REFERENCE_VELOCITY = 760.0

    # Required contexts
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "rake"}
    REQUIRES_DISTANCES = {"rjb"}
    REQUIRES_SITES_PARAMETERS = {"vs30"}


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sigma_intra = {}
        self.tau_inter = {}
        self.phi_total = {}
        if not os.path.exists(_STDS_FILE):
            raise IOError(f"Cannot find stds.csv at {_STDS_FILE}")

        with open(_STDS_FILE, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row["ID"]
                self.sigma_intra[key] = float(row["Sigma"])
                self.tau_inter[key]   = float(row["Tau"])
                self.phi_total[key]   = float(row["Phi"])


    # Vectorized compute()
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Compute method for Mohammadi et al. 2023 GSIM.
        """
        for m, imt in enumerate(imts):
            ln_im, sigma_intra, tau_inter, phi_total = _mean_and_std_from_ctx(
                self, ctx, imt
            )
            # Fill rows for IMT m
            mean[m, :] = ln_im
            sig[m, :]  = phi_total     # TOTAL
            tau[m, :]  = tau_inter     # INTER-EVENT
            phi[m, :]  = sigma_intra   # INTRA-EVENT