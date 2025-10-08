# -*- coding: utf-8 -*-
"""
Taherian et al. 2024 GMPE - Inland scenarios with embedded scalers
"""

import os
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from openquake.baselib.onnx import PicklableInferenceSession
from openquake.hazardlib.gsim.base import GMPE
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
    """Apply scaling transformation"""
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


def get_additional_data():
    """Return DataFrame with sigma, tau, phi values for all IMs"""
    return pd.DataFrame({
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


def run_onnx_prediction(ort_session, Mw_scaled, Rjb_scaled,
                        Depth_scaled, FM, case):
    """Execute ONNX model and return predictions"""
    Input_data = np.column_stack((case, Mw_scaled.flatten(),
                                  Rjb_scaled.flatten(),
                                  Depth_scaled.flatten(),
                                  FM)).astype(np.float32)

    input_name = ort_session.get_inputs()[0].name
    return np.exp(ort_session.run(None, {input_name: Input_data})[0])


def process_predictions(Median_GM, IM_list, additional_data):
    """Convert predictions to periods and ground motion arrays"""
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

        if col == 'PGV':
            psa_col = Median_GM[col].values
        else:
            psa_col = Median_GM[col].values / 981

        additional_row = additional_data[additional_data['IM'] == col]

        if not additional_row.empty:
            mean_values.append(psa_col)
            sigma_values.append(additional_row['total_sigma'].values[0])
            tau_values.append(additional_row['between_event'].values[0])
            phi_values.append(additional_row['residual'].values[0])

    return {
        'periods': np.array(periods),
        'mean': np.array(mean_values).T,
        'sigma': np.array(sigma_values),
        'tau': np.array(tau_values),
        'phi': np.array(phi_values)
    }


def calculate_psa_TEA24_inland(Mw, Rjb, Depth, FM, ort_session):
    """Calculate PSA for inland scenarios"""
    additional_data = get_additional_data()
    IM_list = additional_data['IM'].tolist()

    Mw_scaled = scale_input(Mw, SCALER_PARAMS['mw'])
    Rjb_scaled = scale_input(Rjb, SCALER_PARAMS['rjb'])
    Depth_scaled = scale_input(Depth, SCALER_PARAMS['depth'])

    case = np.zeros_like(Mw)

    predictions = run_onnx_prediction(
        ort_session, Mw_scaled, Rjb_scaled, Depth_scaled, FM, case)

    Median_GM = pd.DataFrame(predictions, columns=IM_list, dtype=float)

    return process_predictions(Median_GM, IM_list, additional_data)


def rake_to_fm(rake):
    """Convert rake angle to fault mechanism"""
    rake = rake % 360
    if rake > 180:
        rake -= 360

    if 60 <= rake <= 120:
        return 0
    elif -120 <= rake <= -60:
        return 1
    else:
        return 0


def create_interpolators(periods_sorted, mean_sorted, sigma_sorted,
                         tau_sorted, phi_sorted):
    """Create interpolation functions for all ground motion parameters"""
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
    return interpolator_mean, interpolator_sigma, interpolator_tau, \
        interpolator_phi


def get_period_from_imt(imt):
    """Extract period value from IMT object"""
    if imt.string.startswith('SA'):
        return imt.period
    elif imt.string == 'PGA':
        return 0.01
    elif imt.string == 'PGV':
        return -1
    else:
        raise ValueError("Unsupported IMT type: {}".format(imt.string))


class Taherian2024Inland(GMPE):
    """
    Taherian et al. (2024) GMPE for inland scenarios in Western Iberia.

    Reference:
    Taherian, A., Silva, V., Kalakonas, P., & Vicente, R. (2024).
    An earthquake ground-motion model for Southwest Iberia.
    Bulletin of the Seismological Society of America, 114(5),
    2613-2638. https://doi.org/10.1785/0120230250
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

    def __init__(self):
        """Initialize with model path only"""
        base_dir = os.path.dirname(__file__)
        self.session = PicklableInferenceSession(
            os.path.join(base_dir, "taherian_2024_data",
                         "ANN_Portugal_rock.onnx"))

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """Compute ground motion using cached ONNX session"""
        FM = np.array([rake_to_fm(r) for r in np.atleast_1d(ctx.rake)])
        Mw = np.atleast_1d(ctx.mag)
        Rjb = np.atleast_1d(ctx.rjb)
        Depth = np.atleast_1d(ctx.hypo_depth)

        psa_data = calculate_psa_TEA24_inland(
            Mw, Rjb, Depth, FM, ort_session=self.session)

        psa_data['mean'] = np.log(psa_data['mean'])

        sort_idx = np.argsort(psa_data['periods'])
        periods_sorted = psa_data['periods'][sort_idx]
        mean_sorted = psa_data['mean'][:, sort_idx]
        sigma_sorted = psa_data['sigma'][sort_idx]
        tau_sorted = psa_data['tau'][sort_idx]
        phi_sorted = psa_data['phi'][sort_idx]

        interp_mean, interp_sig, interp_tau, interp_phi = \
            create_interpolators(periods_sorted, mean_sorted,
                                 sigma_sorted, tau_sorted, phi_sorted)

        for m, imt in enumerate(imts):
            period = get_period_from_imt(imt)
            mean[m] = interp_mean(period)
            sig[m] = interp_sig(period)
            tau[m] = interp_tau(period)
            phi[m] = interp_phi(period)
