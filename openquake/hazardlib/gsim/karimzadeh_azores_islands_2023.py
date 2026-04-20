# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024-2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports :class:`Karimzadeh2023Azores`
"""

import os
import csv
import gzip
import numpy as np

from openquake.baselib.onnx import PicklableInferenceSession
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

_DATA_DIR = os.path.join(
    os.path.dirname(__file__),
    "karimzadeh_azores_2023_data",
)

# Standard deviations file
_STDS_FILE = os.path.join(_DATA_DIR, "stds.csv")
# ONNX model handling (Single bundled model)
_BUNDLED_MODEL_NAME = "karimzadeh_azores_islands_2023_bundled.onnx.gz"

# Period to column index mapping, as learned from models.predict().
# Index 0: PGA, Index 1: PGV, Index 2+: SA periods
_PERIOD_TO_INDEX = {
    0.03: 2, 0.05: 3, 0.075: 4, 0.1: 5, 0.15: 6, 0.2: 7, 0.25: 8,
    0.3: 9, 0.4: 10, 0.5: 11, 0.75: 12, 1.0: 13, 1.5: 14, 2.0: 15
}

def _predict_im(sess: PicklableInferenceSession, X: np.ndarray) -> np.ndarray:
    """
    Evaluate the bundled ONNX model and return outputs for all IMTs
    (shape: N x 16).
    """
    input_name = sess.get_inputs()[0].name
    # Access underlying session to get outputs
    out_name = sess.inference_session.get_outputs()[0].name
    out = sess.run([out_name], {input_name: X.astype(np.float32)})[0]
    return np.asarray(out, dtype=float)

def _mean_and_std_from_ctx(gsim, ctx, imt):
    Mw = np.asarray(ctx.mag, dtype=float)
    RJB = np.asarray(ctx.rjb, dtype=float)
    hypo_depth = np.asarray(ctx.hypo_depth, dtype=float)

    # Order expected by the model: [Mw, RJB, Focal Depth]
    X = np.column_stack([Mw, RJB, hypo_depth])

    if imt.string == "PGA":
        kind = "PGA"
        key = "ln(PGA)"
        index = 0
    elif imt.string == "PGV":
        kind = "PGV"
        key = "ln(PGV)"
        index = 1
    elif imt.period:
        period = float(imt.period)
        kind = "SA"
        key = f"ln(PSA={period})"
        if period not in _PERIOD_TO_INDEX:
            raise ValueError(f"Period {period} not supported in Karimzadeh2023Azores.")
        index = _PERIOD_TO_INDEX[period]
    else:
        raise ValueError(f"IMT {imt} not supported in Karimzadeh2023Azores.")

    # Predict all IMTs at once (N, 16).
    all_outputs = _predict_im(gsim.session, X)
    
    # Extract the requested IMT
    ln_im_train = all_outputs[:, index]

    # Outputs are already in ln(cm/s^2) and ln(cm/s).
    if kind in ("PGA", "SA"):
        # Convert ln(cm/s^2) to ln(g)
        ln_im = ln_im_train - np.log(981.0)
    else:
        # PGV remains in ln(cm/s)
        ln_im = ln_im_train

    # Stds from stds.csv
    sigma_val = gsim.sigma_intra[key]
    tau_val   = gsim.tau_inter[key]
    phi_val   = gsim.phi_total[key]

    sigma_intra = np.full_like(ln_im, sigma_val)
    tau_inter   = np.full_like(ln_im, tau_val)
    phi_total   = np.full_like(ln_im, phi_val)

    return ln_im, sigma_intra, tau_inter, phi_total

class Karimzadeh2023Azores(GMPE):
    """
    Machine-learning Ground-Motion Model for Azores Islands
    (Karimzadeh et al., 2023).

    Reference
    ---------
    Karimzadeh S, Mohammadi A, Salahuddin U, Carvalho A, Lourenço PB.
    Backbone ground motion model through simulated records and XGBoost
    machine learning algorithm: An application for the Azores plateau
    (Portugal). Earthquake Engineering & Structural Dynamics. 2024 Feb;
    53(2):668-93.

    https://doi.org/10.1002/eqe.4040
    """

    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.GEOMETRIC_MEAN
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.INTRA_EVENT,
        const.StdDev.INTER_EVENT,
        const.StdDev.TOTAL,
    }
    DEFINED_FOR_REFERENCE_VELOCITY = 760.0

    REQUIRES_RUPTURE_PARAMETERS = {"mag", "hypo_depth"}
    REQUIRES_DISTANCES = {"rjb"}
    REQUIRES_SITES_PARAMETERS = set()

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

        model_path = os.path.join(_DATA_DIR, _BUNDLED_MODEL_NAME)
        with gzip.open(model_path, "rb") as f:
            model_bytes = f.read()
        self.session = PicklableInferenceSession(model_bytes)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Compute method for Karimzadeh2023Azores GSIM.
        """
        for m, imt in enumerate(imts):
            ln_im, sigma_intra, tau_inter, phi_total = _mean_and_std_from_ctx(
                self, ctx, imt
            )
            mean[m, :] = ln_im
            sig[m, :]  = phi_total     # TOTAL
            tau[m, :]  = tau_inter     # INTER-EVENT
            phi[m, :]  = sigma_intra   # INTRA-EVENT
