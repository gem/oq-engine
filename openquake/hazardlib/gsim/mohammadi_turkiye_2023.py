# -*- coding: utf-8 -*-
"""
Mohammadi et al. (2023) Turkiye ML-based Ground-Motion Model
===========================================================

This module implements the XGBoost-based, region-specific ground-motion model
for Turkiye by Mohammadi et al. (2023) as an OpenQuake GSIM/GMPE.

Reference
---------
Mohammadi A, Karimzadeh S, Banimahd SA, Ozsarac V, Lourenço PB (2023).
"The potential of region-specific machine-learning-based ground motion models:
 application to Turkiye."
Soil Dynamics and Earthquake Engineering, 172:108008.
https://doi.org/10.1016/j.soildyn.2023.108008

Model overview
--------------
- Trained on strong-motion data from Turkiye.
- ML regressor: XGBoost for each intensity measure (PGA, PGV, PSA(T)).
- Inputs (in the order used for training and ONNX):
    1. Mw         : moment magnitude
    2. Vs30       : averaged shear-wave velocity in the top 30 m (m/s)
    3. RJB        : Joyner–Boore distance (km)
    4. normal     : 1 if normal faulting, else 0
    5. reverse    : 1 if reverse faulting, else 0
    6. strike_slip: 1 if strike-slip, else 0

Outputs 
-----
Training units (used inside the ONNX models):
    - PGA, PSA(T): cm/s^2
    - PGV       : cm/s

OpenQuake interface (this GSIM returns *logarithms* of IMs):
    - PGA, SA(T): ln(g)
    - PGV       : ln(cm/s)

Standard deviations (all defined in ln-space)
---------------------------------------------
The file ``stds.csv`` stores, for each IM, the following columns:

    ID    : string, e.g. "ln(PGA)", "ln(PSA=0.01)"
    Sigma : intra-event standard deviation (σ_intra)
    Tau   : inter-event standard deviation (τ)
    Phi   : total standard deviation (σ_total)

In this implementation we adopt the following convention:

    Sigma -> intra-event  (σ_intra)  → mapped to const.StdDev.INTRA_EVENT
    Tau   -> inter-event  (τ)        → mapped to const.StdDev.INTER_EVENT
    Phi   -> total        (σ_total)  → mapped to const.StdDev.TOTAL

This GSIM *does not* recompute residuals; it simply reads σ, τ, Φ from
``stds.csv`` and returns them in the order requested by ``stddev_types``.
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

# ---------------------------------------------------------------------
# 1. Paths
# ---------------------------------------------------------------------

_DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "mohammadi_turkiye_2023_data",
)

_ONNX_DIR = os.path.join(_DATA_DIR, "onnx_models")
_STDS_FILE = os.path.join(_DATA_DIR, "stds.csv")

# ---------------------------------------------------------------------
# 2. Load standard deviation tables (stds.csv)
#
#    convention:
#        Sigma -> intra-event (σ_intra)
#        Tau   -> inter-event (τ)
#        Phi   -> total (σ_total)
#
#    All values are in natural-logarithmic units.
# ---------------------------------------------------------------------

_SIGMA_INTRA = {}  # from "Sigma" (intra-event)
_TAU_INTER = {}    # from "Tau"   (inter-event)
_PHI_TOTAL = {}    # from "Phi"   (total)


def _load_stddev_tables():
    """
    Populate the global dictionaries _SIGMA_INTRA, _TAU_INTER and _PHI_TOTAL
    from the CSV file ``stds.csv``.

    Each CSV row must contain:
        ID, Sigma, Tau, Phi

    Example IDs:
        "ln(PGA)", "ln(PGV)", "ln(PSA=0.01)", ...
    """
    if not os.path.exists(_STDS_FILE):
        raise IOError(f"Cannot find stds.csv at {_STDS_FILE}")

    with open(_STDS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["ID"]           # e.g. 'ln(PGA)', 'ln(PSA=0.01)'
            sigma_intra = float(row["Sigma"])
            tau_inter   = float(row["Tau"])
            phi_total   = float(row["Phi"])

            _SIGMA_INTRA[key] = sigma_intra  # intra-event
            _TAU_INTER[key]   = tau_inter    # inter-event
            _PHI_TOTAL[key]   = phi_total    # total


__all__ = ["Mohammadi2023Turkiye"]
_load_stddev_tables()

# ---------------------------------------------------------------------
# 3. MinMaxScaler parameters (from scx.pkl)
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# 4. ONNX model handling (Single bundled model)
# ---------------------------------------------------------------------

_BUNDLED_MODEL_NAME = "mohammadi_turkiye_2023_bundled.onnx"
_SESS_CACHE = None  # Will hold the single session


def _get_output_name(kind: str, period: float | None) -> str:
    """
    Map (kind, period) to the output node name in the bundled ONNX model.
    
    Structure determined by bundling script:
      - "ln(PGA)"
      - "ln(PGV)"
      - "ln(PSA={period})"
    """
    if kind == "PGA":
        return "ln(PGA)"
    if kind == "PGV":
        return "ln(PGV)"
    if kind == "SA":
        return f"ln(PSA={period})"
    raise ValueError(f"Unknown IM kind: {kind}")


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


def _predict_ln_im(kind: str, period: float | None, X_scaled: np.ndarray) -> np.ndarray:
    """
    Evaluate the bundled ONNX model and return ln(IM) in training units.
    """
    sess = _get_session()
    
    # Identify the correct output node
    target_output = _get_output_name(kind, period)
    
    # Input name is shared and fixed by bundling script
    # It was 'float_input' in all original models.
    input_name = sess.get_inputs()[0].name  # Should be 'float_input'

    # Run inference only for the requested output
    out = sess.run([target_output], {input_name: X_scaled})[0]
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

    # -------------------------------------------------------------
    # Fault mechanism flags (vectorized)
    # -------------------------------------------------------------
    normal      = np.zeros(N, dtype=float)
    reverse     = np.zeros(N, dtype=float)
    strike_slip = np.zeros(N, dtype=float)

    normal[rake < -30.0] = 1.0
    reverse[rake > 30.0] = 1.0
    strike_slip[(rake >= -30.0) & (rake <= 30.0)] = 1.0

    # Order: Mw, Vs30, RJB, normal, reverse, strike_slip
    X = np.column_stack([Mw, Vs30, RJB, normal, reverse, strike_slip])
    X_scaled = _scale_features(X).astype(np.float32)

    if getattr(gsim, "_debug_scaling", False):
        print("\n--- GSIM Scaling Debug ---")
        print("Scaled input:", X_scaled)
        print("--------------------------\n")

    # -------------------------------------------------------------
    # IMT identification
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # Prediction in training units, then convert to OQ units
    # -------------------------------------------------------------
    ln_im_train = _predict_ln_im(kind, period, X_scaled)

    if kind in ("PGA", "SA"):
        # cm/s^2 -> g (still in ln)
        ln_im = ln_im_train - np.log(981.0)
    else:
        # PGV already in cm/s
        ln_im = ln_im_train

    # -------------------------------------------------------------
    # Standard deviations from stds.csv (all in ln-units)
    #   Sigma -> intra-event
    #   Tau   -> inter-event
    #   Phi   -> total
    # -------------------------------------------------------------
    if key not in _SIGMA_INTRA:
        raise KeyError(f"No stddev entry for IM key '{key}' in stds.csv")

    sigma_val = _SIGMA_INTRA[key]  # intra-event
    tau_val   = _TAU_INTER[key]    # inter-event
    phi_val   = _PHI_TOTAL[key]    # total

    sigma_intra = np.full_like(ln_im, sigma_val)
    tau_inter   = np.full_like(ln_im, tau_val)
    phi_total   = np.full_like(ln_im, phi_val)

    return ln_im, sigma_intra, tau_inter, phi_total

# ---------------------------------------------------------------------
# 5. GSIM class
# ---------------------------------------------------------------------

class Mohammadi2023Turkiye(GMPE):
    """
    Machine-learning Ground-Motion Model for Turkiye (Mohammadi et al., 2023).

    This GSIM wraps a set of XGBoost regression models exported to ONNX,
    one per intensity measure (PGA, PGV, PSA(T)). It performs the same
    feature scaling as the original training pipeline and returns
    **mean ln(IM)** and **standard deviations in ln-units**.

    Supported inputs
    ----------------
    - Rupture:
        - mag  : scalar moment magnitude
        - rake : scalar rake angle (degrees, used to define fault mechanism)
    - Distance:
        - rjb  : Joyner–Boore distance (km)
    - Site:
        - vs30 : averaged shear-wave velocity to 30 m (m/s)

    Fault mechanism encoding
    ------------------------
    The rake is mapped to one-hot style flags:

        rake < -30°      → normal = 1, reverse = 0, strike_slip = 0
        rake >  30°      → normal = 0, reverse = 1, strike_slip = 0
        otherwise        → normal = 0, reverse = 0, strike_slip = 1

    Returned units
    --------------
    - mean ln(PGA), ln(SA(T)) : logarithm of acceleration in g
    - mean ln(PGV)            : logarithm of velocity in cm/s
    - Std devs (Tau, Sigma, Phi):
        all are in natural-logarithmic units, directly taken from stds.csv
        according to the convention:
            Sigma -> intra-event  (σ_intra)
            Tau   -> inter-event  (τ)
            Phi   -> total        (σ_total)
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

    # ------------------------------------------------------------------
    # NEW OQ API: vectorized compute()
    # ------------------------------------------------------------------
    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Vectorized OpenQuake entry point.

        Parameters
        ----------
        ctx : numpy.recarray
            Rupture + site context with fields:
                - mag, rake, rjb, vs30
            (plus any others OQ adds).
        imts : list of IMT instances
            For example: [PGA(), PGV(), SA(0.2), ...]
        mean : np.ndarray, shape (M, N)
            mean[m, i] = ln(IM_m) at site i
        sig : np.ndarray, shape (M, N)
            Total stddev (σ_total = Phi) in ln-units.
        tau : np.ndarray, shape (M, N)
            Inter-event stddev (τ) in ln-units.
        phi : np.ndarray, shape (M, N)
            Intra-event stddev (σ_intra = Sigma) in ln-units.

        Notes
        -----
        This matches the standard GMPE API used by OpenQuake 3.x
        (see openquake.hazardlib.gsim.base.GMPE.compute).
        """
        N = len(ctx)
        if N == 0:
            return  # nothing to do

        for m, imt in enumerate(imts):
            ln_im, sigma_intra, tau_inter, phi_total = _mean_and_std_from_ctx(
                self, ctx, imt
            )
            # Fill rows for IMT m
            mean[m, :] = ln_im
            sig[m, :]  = phi_total     # TOTAL
            tau[m, :]  = tau_inter     # INTER-EVENT
            phi[m, :]  = sigma_intra   # INTRA-EVENT

        # No epistemic adjustment implemented -> return None
        return None
