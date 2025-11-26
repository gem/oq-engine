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
# 4. ONNX model handling (one ONNX per IM)
# ---------------------------------------------------------------------

_SESS_CACHE = {}


def _onnx_filename(kind: str, period: float | None) -> str:
    """
    Map (kind, period) to an ONNX filename inside the ``onnx_models`` folder.

    Parameters
    ----------
    kind : {"PGA", "PGV", "SA"}
        Type of intensity measure.
    period : float or None
        Period in seconds for SA. Must exactly match the period used
        in training/filenames. For PGA and PGV this is ignored.

    Returns
    -------
    fname : str
        ONNX filename, for example:
            - "Xgboost_ln(PGA).onnx"
            - "Xgboost_ln(PGV).onnx"
            - "Xgboost_ln(PSA=0.01).onnx"

    Raises
    ------
    ValueError
        If the IM kind is not recognized.
    """
    if kind == "PGA":
        return "Xgboost_ln(PGA).onnx"
    if kind == "PGV":
        return "Xgboost_ln(PGV).onnx"
    if kind == "SA":
        # period is a float; filenames must match exactly the training ones
        return f"Xgboost_ln(PSA={period}).onnx"
    raise ValueError(f"Unknown IM kind: {kind}")


def _get_session(fname: str) -> ort.InferenceSession:
    """
    Return a cached ONNXRuntime session for the given model filename.

    Parameters
    ----------
    fname : str
        Filename of the ONNX model (e.g. "Xgboost_ln(PGA).onnx"),
        relative to the ``onnx_models`` directory.

    Returns
    -------
    sess : onnxruntime.InferenceSession
        A cached session ready for inference.

    Raises
    ------
    IOError
        If the ONNX model file cannot be found.
    """
    if fname not in _SESS_CACHE:
        full_path = os.path.join(_ONNX_DIR, fname)
        if not os.path.exists(full_path):
            raise IOError(f"Cannot find ONNX file: {full_path}")

        opt = ort.SessionOptions()
        opt.intra_op_num_threads = 1
        opt.inter_op_num_threads = 1

        _SESS_CACHE[fname] = ort.InferenceSession(full_path, sess_options=opt)

    return _SESS_CACHE[fname]


def _predict_ln_im(kind: str, period: float | None, X_scaled: np.ndarray) -> np.ndarray:
    """
    Evaluate the appropriate ONNX model and return ln(IM) in training units.

    Parameters
    ----------
    kind : {"PGA", "PGV", "SA"}
        Type of intensity measure.
    period : float or None
        SA period in seconds (ignored for PGA and PGV).
    X_scaled : np.ndarray, shape (N, 6)
        Scaled features, as returned by :func:`_scale_features`.

    Returns
    -------
    ln_im_train : np.ndarray, shape (N,)
        Natural logarithm of IM in **training units**:
            - PGA, SA: ln(cm/s^2)
            - PGV    : ln(cm/s)
    """
    fname = _onnx_filename(kind, period)
    sess = _get_session(fname)

    input_name = sess.get_inputs()[0].name    # usually 'float_input'
    output_name = sess.get_outputs()[0].name  # e.g. 'Xgboost_ln(PGA)'

    out = sess.run([output_name], {input_name: X_scaled})[0]
    return np.asarray(out, dtype=float).reshape(-1)


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

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Compute mean ln(IM) and standard deviations for the requested IMT.

        Parameters
        ----------
        sites : :class:`openquake.hazardlib.site.SiteCollection`
            Collection of sites. Only ``vs30`` is used by this model.
        rup : object
            Rupture-like object with attributes:
                - mag  : moment magnitude
                - rake : rake angle in degrees
                - tectonic_region_type (ignored here; assumed compatible).
        dists : object
            Distance context with attribute:
                - rjb : Joyner–Boore distance (array-like, km)
        imt : instance of :mod:`openquake.hazardlib.imt` (PGA, PGV, SA)
            Intensity measure type for which to evaluate the model.
        stddev_types : list of :class:`openquake.hazardlib.const.StdDev`
            Standard deviation types required. Any subset of:
                - const.StdDev.INTRA_EVENT
                - const.StdDev.INTER_EVENT
                - const.StdDev.TOTAL

        Returns
        -------
        mean : np.ndarray, shape (N,)
            Mean **logarithm** of IM at each site:
                - ln(PGA), ln(SA(T)) in g
                - ln(PGV) in cm/s
        stds : list of np.ndarray
            One array per requested stddev type, same shape as ``mean``.
            Values are in natural-logarithmic units, taken directly from
            ``stds.csv`` using the convention:
                Sigma -> intra-event  (σ_intra)
                Tau   -> inter-event  (τ)
                Phi   -> total        (σ_total)

        Raises
        ------
        ValueError
            If the IMT is not supported or a StdDev type is unknown.
        KeyError
            If no stddev entry is found in ``stds.csv`` for the given IMT.
        """

        N = len(sites)

        Mw = np.full(N, rup.mag, dtype=float)
        RJB = np.asarray(dists.rjb, dtype=float)
        Vs30 = np.asarray(sites.vs30, dtype=float)

        rake = float(rup.rake)

        # Fault mechanism flags (scalar rake, broadcast to N-length arrays)
        if rake < -30.0:
            normal = np.ones(N, dtype=float)
            reverse = np.zeros(N, dtype=float)
            strike_slip = np.zeros(N, dtype=float)
        elif rake > 30.0:
            normal = np.zeros(N, dtype=float)
            reverse = np.ones(N, dtype=float)
            strike_slip = np.zeros(N, dtype=float)
        else:
            normal = np.zeros(N, dtype=float)
            reverse = np.zeros(N, dtype=float)
            strike_slip = np.ones(N, dtype=float)

        # Order: Mw, Vs30, RJB, normal, reverse, strike_slip
        X = np.column_stack([Mw, Vs30, RJB, normal, reverse, strike_slip])
        X_scaled = _scale_features(X).astype(np.float32)

        # -----------------------------------------------------------------
        # IMT identification – robust to old OQ versions
        # -----------------------------------------------------------------
        imt_str = str(imt)  # e.g. 'PGA', 'PGV', 'SA(0.2)'

        if imt_str == "PGA":
            kind, period = "PGA", None
            key = "ln(PGA)"

        elif imt_str == "PGV":
            kind, period = "PGV", None
            key = "ln(PGV)"

        elif imt_str.startswith("SA(") and imt_str.endswith(")"):
            inside = imt_str[3:-1]  # strip 'SA(' and ')'
            period = float(inside)
            kind = "SA"
            key = f"ln(PSA={period})"

        else:
            raise ValueError(f"IMT {imt_str} not supported in Mohammadi2023Turkiye")

        if getattr(self, "_debug_scaling", False):
            print("\n--- GSIM Scaling Debug ---")
            print("Scaled input:", X_scaled)
            print("--------------------------\n")

        # -----------------------------------------------------------------
        # Prediction in training units (log)
        # -----------------------------------------------------------------
        ln_im_train = _predict_ln_im(kind, period, X_scaled)

        # Convert to OpenQuake units, STILL ln:
        #   - PGA, SA: cm/s^2 -> g
        #   - PGV: stays in cm/s
        if kind in ("PGA", "SA"):
            ln_im = ln_im_train - np.log(981.0)   # ln(g)
        else:
            ln_im = ln_im_train                   # ln(cm/s)

        # -----------------------------------------------------------------
        # Standard deviations from stds.csv (all in ln-units)
        #   Sigma -> intra-event
        #   Tau   -> inter-event
        #   Phi   -> total
        # -----------------------------------------------------------------
        if key not in _SIGMA_INTRA:
            raise KeyError(f"No stddev entry for IM key '{key}' in stds.csv")

        sigma = _SIGMA_INTRA[key]  # intra-event
        tau   = _TAU_INTER[key]    # inter-event
        phi   = _PHI_TOTAL[key]    # total

        stds = []
        for s in stddev_types:
            if s == const.StdDev.INTRA_EVENT:
                stds.append(np.full_like(ln_im, sigma))
            elif s == const.StdDev.INTER_EVENT:
                stds.append(np.full_like(ln_im, tau))
            elif s == const.StdDev.TOTAL:
                stds.append(np.full_like(ln_im, phi))
            else:
                raise ValueError(f"StdDev type {s} not supported.")

        return ln_im, stds
