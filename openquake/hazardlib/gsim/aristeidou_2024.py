# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2024, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Mon Apr 08 2024
Authors: savvinos.aristeidou@iusspavia.it, davit.shahnazaryan@iusspavia.it

Module exports :class:`AristeidouEtAl2024`
               :class:`AristeidouEtAl2024Geomean`
               :class:`AristeidouEtAl2024RotD100`
"""

import pathlib
import numpy as np
from scipy.interpolate import interp1d

from openquake.hazardlib import const
from openquake.hazardlib.imt import (
    RSD575, RSD595, Sa_avg2, Sa_avg3, SA, PGA, PGV, PGD, FIV3)
from openquake.hazardlib.gsim.base import GMPE
from openquake.hazardlib.gsim.campbell_bozorgnia_2014 import _get_z2pt5_ref
import h5py

ASSET_DIR = pathlib.Path(__file__).resolve().parent / "aristeidou_2024_assets"


def load_hdf5_to_list(group):
    """
    Recursively load an HDF5 group or dataset into a nested list or value.
    """
    # If it's a dataset, return its data as a list
    if isinstance(group, h5py.Dataset):
        return group[:].tolist()
    # If it's a group, recurse into its members
    elif isinstance(group, h5py.Group):
        keys = list(group.keys())  # Convert KeysViewHDF5 to list of strings
        # Sort keys numerically
        sorted_keys = sorted(keys, key=lambda k: int(k.split("_")[-1]))
        return [load_hdf5_to_list(group[key]) for key in sorted_keys]


def get_period_im(name: str):
    """
    Returns the period of IM and IM type, given the IM name string
    """
    period = float(name.split('(')[-1].split(')')[0])
    return period


def linear(x):
    """
    Calculate the linear activation function
    """
    return x


def tanh(x):
    """
    Calculate the tanh activation function
    """
    return np.tanh(x)


def softmax(x):
    """
    Calculate the softmax activation function
    """
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


def sigmoid(x):
    """
    Calculate the sigmoid activation function
    """
    return 1 / (1 + np.exp(-x))


def _get_style_of_faulting_term(rake):
    """
    Get fault type dummy variables
    Fault type (Strike-slip, Normal, Reverse, Reverse-Oblique,
    Normal-oblique) is derived from rake angle.
                        SOF encoding    Rake Angles
    _______________________________________________________
    Strike-slip     |    0            | -180 < rake < -150
                    |                 | -30 < rake < 30
                    |                 | 150 < rake < 180
                    |                 |
    Normal          |    1            | -120 < rake < -60
                    |                 |
    Reverse         |    2            | 60 < rake < 120
                    |                 |
    Reverse-Oblique |    3            | 30 < rake < 60
                    |                 | 120 < rake < 150
                    |                 |
    Normal-oblique  |    4            | -150 < rake < -120
                    |                 | -60 < rake < -30
                    |                 |
    Note that the 'Unspecified' case is not considered here as
    rake is always given.
    """
    sof = np.full_like(rake, 0)

    sof[((rake >= -180) & (rake <= -150)) | ((rake > -30) &
        (rake <= 30)) | ((rake > 150) & (rake <= 180))] = 0

    sof[(rake > -120) & (rake <= -60)] = 1

    sof[(rake > 60) & (rake <= 120)] = 2

    sof[((rake > 30) & (rake <= 60)) | ((rake > 120) &
        (rake <= 150))] = 3

    sof[((rake > -150) & (rake <= -120)) |
        ((rake > -60) & (rake <= -30))] = 4

    return sof


def extract_im_names(imts, component_definition):
    """
    Convert the im strings of openquake to the im naming convention
    used in the GMM
    """
    imts_base = []
    im_names = []
    for imt in imts:
        # Keep the im text before the occurance of '('
        base = imt.string.split('(')[0]
        # Keep the im text before the last occurance of '_'
        base = base.split('_')[:2]
        base = "_".join(base[:2])
        im_name_mapping = {
            "RSD575": "Ds575",
            "RSD595": "Ds595",
            "Sa_avg2": "Sa_avg2" + f"_{component_definition}({imt.period})",
            "Sa_avg3": "Sa_avg3" + f"_{component_definition}({imt.period})",
            "SA": "SA" + f"_{component_definition}({imt.period})",
            "Sa": "SA" + f"_{component_definition}({imt.period})",
            "FIV3": "FIV3" + f"({imt.period})",
            "PGA": "PGA",
            "PGV": "PGV",
            "PGD": "PGD",
        }
        im_name = im_name_mapping[base]
        imts_base.append(base)
        im_names.append(im_name)
    im_names = np.array(im_names)
    return im_names


def _get_means_stddevs(DATA, imts, means, stddevs, component_definition):
    """
    Extract the means and standard deviations of the requested IMs and
    horizontal compoent definitions
    """
    supported_ims = np.char.decode(DATA["output_ims"], 'UTF-8')
    im_names = extract_im_names(imts, component_definition)

    if len(means.shape) == 1:
        means = means.reshape(1, means.shape[0])

    # Get means and standard deviations of the IMs that do not need
    # interpolation
    idx = [np.where(supported_ims == im_name)[0] for im_name in im_names]
    idx = np.concatenate(idx)
    if idx.size == 0:
        means_no_interp = np.array([])
        stddevs_no_interp = np.array([])
    else:
        means_no_interp = means[:, idx].T
        stddevs_no_interp = stddevs[:, idx, :]

    idx_no_interp = np.isin(im_names, supported_ims)

    means_interp = []
    stddevs_interp = np.full(
        (stddevs.shape[0], len(im_names[~idx_no_interp]),
         stddevs.shape[2]), np.nan)
    # Perform linear interpolation in the logarithmic space for periods
    # not included in the set of periods of the GMM
    for m, im_name in enumerate(im_names[~idx_no_interp]):
        idxs = np.where(np.char.startswith(
            supported_ims, im_name.split("(")[0]))
        ims = supported_ims[idxs]
        means_for_interp = means[:, idxs]
        stddevs_for_interp = stddevs[:, idxs, :]

        periods = []
        for im in ims:
            _t = get_period_im(im)
            periods.append(_t)

        # Create interpolators
        interp_stddevs = interp1d(np.log(periods), stddevs_for_interp,
                                  axis=2)
        interp_means = interp1d(np.log(periods), means_for_interp)
        try:
            mean_interp = interp_means(
                np.log(imts[np.where([~idx_no_interp])[1][m]].period))
            stddev_interp = interp_stddevs(
                np.log(imts[np.where([~idx_no_interp])[1][m]].period))
        except ValueError:
            raise KeyError(imts[np.where([~idx_no_interp])[1][m]])
        means_interp.append(np.squeeze(mean_interp, axis=1))
        stddevs_interp[:, m, :] = np.squeeze(stddev_interp, axis=1)
    means_interp = np.array(means_interp)
    stddevs_interp = np.array(stddevs_interp)

    # Combine interpolated and not interpolated values in the
    # final mean and standard deviation estimations
    mean = np.full((len(im_names), means.shape[0]), np.nan)
    stddev = np.full((
        stddevs.shape[0], len(im_names), stddevs.shape[2]), np.nan)
    if means_interp.size != 0 and means_no_interp.size != 0:
        mean[idx_no_interp, :] = means_no_interp
        mean[~idx_no_interp, :] = means_interp

        stddev[:, idx_no_interp, :] = stddevs_no_interp
        stddev[:, ~idx_no_interp, :] = stddevs_interp
        return mean, stddev
    elif means_interp.size == 0:
        mean = means_no_interp
        stddev = stddevs_no_interp
        return mean, stddev
    else:
        mean = means_interp
        stddev = stddevs_interp
        return mean, stddev


def _generate_function(x, biases, weights):
    """
    Returns the output of a layer based on the input, biases, and weights
    """
    biases = np.asarray(biases)
    weights = np.asarray(weights).T
    return biases.reshape(1, -1) + np.dot(weights, x.T).T


def _minmax_scaling(DATA, x, SUGGESTED_LIMITS, feature_range=(-3, 3)):
    """
    Returns the min-max transformation scaling of input features
    """
    pars = np.char.decode(DATA['parameters'], 'UTF-8')
    min_max = np.asarray([
        SUGGESTED_LIMITS[par] for par in pars])

    scaled_data = (x - min_max[:, 0]) / (min_max[:, 1] - min_max[:, 0])
    scaled_data = scaled_data * \
        (feature_range[1] - feature_range[0]) + feature_range[0]
    return scaled_data


class AristeidouEtAl2024(GMPE):
    """
    Aristeidou, S., Shahnazaryan, D. and O’Reilly, G.J. (2024) ‘Artificial
    neural network-based ground motion model for next-generation seismic
    intensity measures’, Soil Dynamics and Earthquake Engineering, 184,
    108851. Available at: https://doi.org/10.1016/j.soildyn.2024.108851.
    """
    #: Supported tectonic region type is subduction interface
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        PGA, PGV, PGD, SA, Sa_avg2, Sa_avg3}

    #: Supported intensity measure components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = {const.IMC.RotD50}

    #: Supported standard deviation types
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT}

    #: Requires sites parameters
    REQUIRES_SITES_PARAMETERS = {'vs30', 'z2pt5'}

    #: Required rupture parameters
    REQUIRES_RUPTURE_PARAMETERS = {
        'mag', 'ztor', 'hypo_depth', 'rake'}

    #: Required distance measures
    REQUIRES_DISTANCES = {'rrup', 'rjb', 'rx'}

    # Suggested usage range of the GMM
    SUGGESTED_LIMITS = {
        "magnitude": [4.5, 7.9],
        "Rjb": [0., 299.44],
        "Rrup": [0.07, 299.59],
        "D_hyp": [2.3, 18.65],
        "Vs30": [106.83, 1269.78],
        "mechanism": [0, 4],
        "Z2pt5": [0., 7780.],
        "Rx": [-297.13, 292.39],
        "Ztor": [0, 16.23],
    }

    component_definition = "RotD50"

    def __init__(self):
        # Load background information about the model from a hdf5 file
        # (i.e., weight, biases, standard devation values, etc.)
        with h5py.File(ASSET_DIR / "gmm_ann.hdf5", 'r') as h5:
            self.DATA = {}
            for key in h5:
                self.DATA[key] = load_hdf5_to_list(h5[key])

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        # Reshaping and stacking context parameters to be in an
        # appropriate format as an input to the ANN model
        mag = np.array(ctx.mag).reshape(-1, 1)
        rjb = np.array(ctx.rjb).reshape(-1, 1)
        rrup = np.array(ctx.rrup).reshape(-1, 1)
        d_hyp = np.array(ctx.hypo_depth).reshape(-1, 1)
        vs30 = np.array(ctx.vs30).reshape(-1, 1)
        rake = np.array(ctx.rake).reshape(-1, 1)
        mechanism = _get_style_of_faulting_term(rake)
        z2pt5 = ctx.z2pt5.copy()
        # Use non-Japan CB14 vs30 to z2pt5 relationship for none-measured values
        mask = z2pt5 == -999
        z2pt5[mask] = _get_z2pt5_ref(False, ctx.vs30[mask])
        # Transform z2pt5 to [m]
        z2pt5 = np.array(z2pt5).reshape(-1, 1) * 1000
        rx = np.array(ctx.rx).reshape(-1, 1)
        ztor = np.array(ctx.ztor).reshape(-1, 1)
        ctx_params = np.column_stack([
            rjb, rrup, d_hyp, mag, vs30, mechanism, z2pt5, rx, ztor
        ])

        # Get biases and weights of the ANN model
        biases = self.DATA["biases"]
        weights = self.DATA["weights"]

        # Input layer
        # Transform the input
        x_transformed = _minmax_scaling(
            self.DATA, ctx_params, self.SUGGESTED_LIMITS)

        _data = _generate_function(
            x_transformed, biases[0], weights[0])
        a1 = softmax(_data)

        # Hidden layer
        _data = _generate_function(
            a1, biases[1], weights[1]
        )
        a2 = tanh(_data)

        # Output layer
        _data = _generate_function(
            a2, biases[2], weights[2]
        )
        output_log10 = linear(_data)

        # Reverse log10
        output = 10 ** output_log10

        # The shape of the obtained means is:
        # (scenarios, total number of offered IMs)
        means = np.squeeze(np.log(output))

        # get the standard deviations
        stddevs = np.asarray((self.DATA["total_stdev"],
                              self.DATA["inter_stdev"],
                              self.DATA["intra_stdev"]))
        stddevs = np.expand_dims(stddevs, axis=2).repeat(
            ctx_params.shape[0], axis=2)

        # Transform the standard deviations from log10 to natural logarithm
        stddevs = np.log(10**stddevs)

        # Get the means and stddevs at index corresponding to the IM
        mean[:], stddevs = _get_means_stddevs(
            self.DATA, imts, means, stddevs, self.component_definition)

        sig[:] = stddevs[0, :, :]
        tau[:] = stddevs[1, :, :]
        phi[:] = stddevs[2, :, :]


class AristeidouEtAl2024Geomean(AristeidouEtAl2024):

    #: Supported intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        SA, Sa_avg2, Sa_avg3, RSD595, RSD575, FIV3}

    #: Supported intensity measure components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = {const.IMC.GEOMETRIC_MEAN}

    component_definition = "geomean"


class AristeidouEtAl2024RotD100(AristeidouEtAl2024):

    #: Supported intensity measure types
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        SA, Sa_avg2, Sa_avg3}

    #: Supported intensity measure components
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = {const.IMC.RotD100}

    component_definition = "RotD100"
