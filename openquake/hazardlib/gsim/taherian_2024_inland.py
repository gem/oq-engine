# -*- coding: utf-8 -*-
"""
Taherian et al. 2024 GMPE - Inland scenarios with embedded scalers
No external scaler files needed!
"""

import os
import numpy as np
import pandas as pd
import onnxruntime as ort
from scipy.interpolate import interp1d

from openquake.hazardlib.gsim.base import GMPE, registry
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA, PGV

# ============================================================================
# EMBEDDED SCALER PARAMETERS
# ============================================================================

SCALER_PARAMS = {
    'mw': {
        'type': 'MinMaxScaler',
        'min_': np.array([-0.5454545454545454]),
        'scale': np.array([0.18181818181818182])
    },
    'rjb': {
        'type': 'MinMaxScaler',
        'min_': np.array([0.0]),
        'scale': np.array([0.0016666666666666668])
    },
    'depth': {
        'type': 'MinMaxScaler',
        'min_': np.array([-0.07248234670638956]),
        'scale': np.array([0.035807897789936545])
    }
}


def scale_input(value, scaler_params):
    """Apply scaling transformation without using joblib scalers"""
    value = np.atleast_1d(value).reshape(-1, 1)

    if scaler_params['type'] == 'StandardScaler':
        return (value - scaler_params['mean']) / scaler_params['scale']
    elif scaler_params['type'] == 'MinMaxScaler':
        return value * scaler_params['scale'] + scaler_params['min_']
    elif scaler_params['type'] == 'RobustScaler':
        return (value - scaler_params['center']) / scaler_params['scale']
    else:
        raise ValueError("Unknown scaler type: {}".format(
            scaler_params['type']))


def calculate_psa_TEA24_inland(Mw, Rjb, Depth, FM):
    """
    Calculate PSA for inland scenarios using TEA24 model with embedded
    scalers.

    Parameters:
    - Mw: float, earthquake magnitude.
    - Rjb: float, distance in km.
    - Depth: float, hypocenter depth in km.
    - FM: int, fault mechanism (0 for Reverse, 1 for Normal).

    Returns:
    - Dictionary with 'periods', 'mean', 'sigma', 'tau', 'phi' values.
    """

    # Define additional data inside the function
    additional_data = pd.DataFrame({
        'between_event': [0.519290669, 0.524470346, 0.529756778,
                          0.529688794, 0.532506304, 0.530049414,
                          0.532964882, 0.53110028, 0.536437409,
                          0.539748677, 0.539697967, 0.540025487,
                          0.547286421, 0.552996317, 0.571526251,
                          0.581546766, 0.594193527, 0.586797102,
                          0.560534959, 0.536437409],
        'residual': [0.264047911, 0.260283973, 0.251218468,
                     0.244845183, 0.241076109, 0.237037624,
                     0.23417217, 0.232926235, 0.23273434,
                     0.234710867, 0.238736016, 0.240160935,
                     0.24949612, 0.251870684, 0.25531389,
                     0.256991427, 0.257851675, 0.250420973,
                     0.243669106, 0.249203819],
        'total_sigma': [0.582566818, 0.585505671, 0.586304496,
                        0.583540386, 0.584534562, 0.580636905,
                        0.582141023, 0.579932874, 0.584748122,
                        0.588572702, 0.590143017, 0.591020136,
                        0.601473806, 0.607654316, 0.625961211,
                        0.635799681, 0.647729445, 0.637998042,
                        0.611207063, 0.584748122],
        'IM': ['f=0.25', 'f=0.32', 'f=0.5', 'f=0.67', 'f=0.8', 'f=1',
               'f=1.3', 'f=1.6', 'f=2', 'f=2.5', 'f=4', 'f=5', 'f=8',
               'f=10', 'f=15', 'f=20', 'f=25', 'f=50', 'PGA', 'PGV']
    })

    IM_list = additional_data['IM'].tolist()

    # Using embedded scalers
    Mw_scaled = scale_input(Mw, SCALER_PARAMS['mw'])
    Rjb_scaled = scale_input(Rjb, SCALER_PARAMS['rjb'])
    Depth_scaled = scale_input(Depth, SCALER_PARAMS['depth'])

    # Load ONNX model
    base_dir = os.path.dirname(__file__)
    onnx_model_path = os.path.join(
        base_dir, "taherian_2024_data", "ANN_Portugal_rock.onnx")

    ort_session = ort.InferenceSession(onnx_model_path)

    # Set case = 0 for inland scenarios
    case = np.zeros_like(Mw)

    # Prepare input array for model
    Input_data = np.column_stack((case, Mw_scaled.flatten(),
                                  Rjb_scaled.flatten(),
                                  Depth_scaled.flatten(),
                                  FM)).astype(np.float32)

    # Make predictions using ONNX model
    input_name = ort_session.get_inputs()[0].name
    Median_GM = np.exp(ort_session.run(None, {input_name: Input_data})[0])

    # Convert predictions to DataFrame
    Median_GM = pd.DataFrame(Median_GM, columns=IM_list, dtype=float)

    # Map PSA values to periods
    periods = []
    mean_values = []
    sigma_values = []
    tau_values = []
    phi_values = []

    for col in Median_GM.columns:
        if col == 'PGA':
            periods.append(0.01)
        elif '=' in col:
            periods.append(1.0 / float(col.split('=')[1]))
        elif col == 'PGV':
            periods.append(-1.0)

        # Apply correct unit conversions
        if col == 'PGV':
            # PGV: in cm/s
            psa_col = Median_GM[col].values
        else:
            # PGA and SA: Convert from cm/s² to g
            psa_col = Median_GM[col].values / 981

        additional_row = additional_data[additional_data['IM'] == col]

        if not additional_row.empty:
            mean_values.append(psa_col)
            sigma_values.append(additional_row['total_sigma'].values[0])
            tau_values.append(additional_row['between_event'].values[0])
            phi_values.append(additional_row['residual'].values[0])

    # Convert lists to numpy arrays
    mean = np.array(mean_values).T
    sigma = np.array(sigma_values)
    tau = np.array(tau_values)
    phi = np.array(phi_values)

    return {
        'periods': np.array(periods),
        'mean': mean,
        'sigma': sigma,
        'tau': tau,
        'phi': phi
    }


def rake_to_fm(rake):
    """
    Convert rake angle to fault mechanism based on Aki & Richards (1980).

    Parameters:
    - rake: float, rake angle in degrees

    Returns:
    - FM: int, fault mechanism (0 for Reverse, 1 for Normal)
    """
    # Normalize rake to [-180, 180] range
    rake = rake % 360
    if rake > 180:
        rake -= 360

    if 60 <= rake <= 120:
        return 0  # Reverse
    elif -120 <= rake <= -60:
        return 1  # Normal
    else:
        # For strike-slip and intermediate mechanisms, default to reverse
        return 0


class Taherian2024Inland(GMPE):
    """
    Implements the Taherian et al. (2024) Ground Motion Prediction
    Equation for inland scenarios in Western Iberia using an Artificial
    Neural Network.

    This GMPE uses an ANN trained on ground motion data from Portugal
    and surrounding regions. It predicts ground motion for rock sites
    (Vs30 = 760 m/s).

    Reference:
    Taherian, A., et al. (2024). "ANN-based Ground Motion Model for
    Western Iberia." [Add full citation when available]
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.MEDIAN_HORIZONTAL
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    }
    REQUIRES_SITES_PARAMETERS = set()
    DEFINED_FOR_REFERENCE_VELOCITY = 760.0
    REQUIRES_RUPTURE_PARAMETERS = {"mag", "hypo_depth", "rake"}
    REQUIRES_DISTANCES = {"rjb"}
    SUPPORTED_SA_PERIODS = (0.01, 4.0)

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        Vectorized implementation for Taherian 2024 Inland GMPE.
        """
        # Extract parameters
        Depth = ctx.hypo_depth
        Mw = ctx.mag
        Rjb = ctx.rjb
        rake = ctx.rake

        # Convert rake to fault mechanism
        FM = np.array([rake_to_fm(r) for r in np.atleast_1d(rake)])

        # Ensure numpy arrays for inputs
        Mw = np.atleast_1d(Mw)
        Rjb = np.atleast_1d(Rjb)
        Depth = np.atleast_1d(Depth)

        psa_data = calculate_psa_TEA24_inland(
            Mw=Mw,
            Rjb=Rjb,
            Depth=Depth,
            FM=FM
        )

        # Convert to natural log
        psa_data['mean'] = np.log(psa_data['mean'])

        # Sort periods and corresponding data for interpolation
        sort_idx = np.argsort(psa_data['periods'])
        periods_sorted = psa_data['periods'][sort_idx]
        mean_sorted = psa_data['mean'][:, sort_idx]
        sigma_sorted = psa_data['sigma'][sort_idx]
        tau_sorted = psa_data['tau'][sort_idx]
        phi_sorted = psa_data['phi'][sort_idx]

        for m, imt in enumerate(imts):
            # Determine the period based on IMT
            if imt.string.startswith('SA'):
                period = imt.period
            elif imt.string == 'PGA':
                period = 0.01
            elif imt.string == 'PGV':
                period = -1
            else:
                raise ValueError("Unsupported IMT type: {}".format(
                    imt.string))

            # Create interpolators with SORTED data
            interpolator_mean = interp1d(
                periods_sorted, mean_sorted,
                kind='linear', bounds_error=False,
                fill_value='extrapolate', axis=1
            )
            interpolator_sigma = interp1d(
                periods_sorted, sigma_sorted,
                kind='linear', bounds_error=False,
                fill_value='extrapolate'
            )
            interpolator_tau = interp1d(
                periods_sorted, tau_sorted,
                kind='linear', bounds_error=False,
                fill_value='extrapolate'
            )
            interpolator_phi = interp1d(
                periods_sorted, phi_sorted,
                kind='linear', bounds_error=False,
                fill_value='extrapolate'
            )

            # Assign interpolated values
            mean[m] = interpolator_mean(period)
            sig[m] = interpolator_sigma(period)
            tau[m] = interpolator_tau(period)
            phi[m] = interpolator_phi(period)


# Register the GMPE
registry["Taherian2024Inland"] = Taherian2024Inland
