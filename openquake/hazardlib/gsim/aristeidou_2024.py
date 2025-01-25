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

from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d
from openquake.hazardlib import const
from openquake.hazardlib.imt import (
    RSD575, RSD595, Sa_avg2, Sa_avg3, SA, PGA, PGV, PGD, FIV3)
from openquake.hazardlib.gsim.base import GMPE
import json

ASSET_DIR = Path(__file__).resolve().parent / "aristeidou_2024_assets"


def read_json(filename: Path):
    with open(filename) as f:
        filename = json.load(f)
    return filename


# Load background information about the model from a json file (i.e., weight,
# biases, standard devation values, etc.)
DATA = read_json(ASSET_DIR / "gmm_ann.json")


def get_period_im(name: str):
    """
    Returns the period of IM and IM type, given the IM name string
    """
    if '(' in name:
        im_type = name.split('(', 1)[0].strip()
        period = float(name.split('(')[-1].split(')')[0])
    else:
        im_type = name
        period = None

    return im_type, period


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


def extract_base(im):
    """
    Remove the text after the last underscore and any trailing
    parentheses with numbers
    """
    # Keep the im text before the last occurance of '_'
    base = im.rsplit('_', 1)[0]
    # Keep the im text before the occurance of '('
    base = base.split('(')[0]
    return base


def _get_means_stddevs(DATA, imt, means, stddevs, component_definition):
    """
    Extract the means and standard deviations of the requested IMs and
    horizontal compoent definitions
    """
    supported_ims = np.asarray(DATA["output-ims"])
    supported_im_types = np.unique(np.array(
        [extract_base(supported_im) for supported_im in supported_ims]))

    im_name_mapping = {
        "RSD575": "Ds575",
        "RSD595": "Ds595",
        "Sa_avg2": "Sa_avg2",
        "Sa_avg3": "Sa_avg3",
        "SA": "SA",
        "Sa": "SA",
        "FIV3": "FIV3",
        "PGA": "PGA",
        "PGV": "PGV",
        "PGD": "PGD",
    }

    im_name = im_name_mapping[extract_base(imt.string)]

    if im_name not in supported_im_types:
        raise NameError(
            f"IM name {im_name} is not supported by this GMM")

    # if im_name.startswith("SA") or im_name.startswith("Sa"):
    #     im_name = "SA" + f'_{component_definition}'

    if im_name.startswith("SA") or im_name.startswith("Sa"):
        # Find the position of the first parenthesis
        pos = imt.string.index("(")
        # Insert using slicing
        im_name = (imt.string[:pos] + f'_{component_definition}'
                   + imt.string[pos:])
    elif im_name.startswith("FIV3"):
        im_name = imt.string

    if len(means.shape) == 1:
        means = means.reshape(1, means.shape[0])

    if im_name in supported_ims:
        idx = np.where(supported_ims == im_name)[0][0]
        return means[:, idx], stddevs[idx, :]

    # Period not supported, perform linear interpolation
    idxs = np.where(np.char.find(
        supported_ims, im_name[:im_name.index("(")]) != -1)

    ims = supported_ims[idxs]
    means = means[:, idxs]
    stddevs = stddevs[idxs, :]

    periods = []
    for im in ims:
        _, _t = get_period_im(im)
        periods.append(_t)

    # TODO: interpolate in the log space
    # Create interpolators
    interp_stddevs = interp1d(np.log(periods), stddevs, axis=1)
    interp_means = interp1d(np.log(periods), means)

    mean, stddev = (np.squeeze(interp_means(np.log(imt.period))),
                    np.squeeze(interp_stddevs(np.log(imt.period))))
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
    pars = DATA["parameters"]
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
    intensity measures’, Under Review.
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

    def compute(self, ctx: np.recarray, imts, mean, sig, tau, phi):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.compute>`
        for spec of input and result values.
        """
        breakpoint()
        for m, imt in enumerate(imts):

            mag = np.array(ctx.mag).reshape(-1, 1)
            rjb = np.array(ctx.rjb).reshape(-1, 1)
            rrup = np.array(ctx.rrup).reshape(-1, 1)
            d_hyp = np.array(ctx.hypo_depth).reshape(-1, 1)
            vs30 = np.array(ctx.vs30).reshape(-1, 1)
            rake = np.array(ctx.rake).reshape(-1, 1)
            mechanism = _get_style_of_faulting_term(rake)
            # Transform z2pt5 to [m]
            z2pt5 = np.array(ctx.z2pt5).reshape(-1, 1) * 1000
            rx = np.array(ctx.rx).reshape(-1, 1)
            ztor = np.array(ctx.ztor).reshape(-1, 1)

            ctx_params = np.column_stack([
                rjb, rrup, d_hyp, mag, vs30, mechanism, z2pt5, rx, ztor
            ])

            # Get biases and weights of the ANN model
            biases = DATA["biases"]
            weights = DATA["weights"]

            # Input layer
            # Transform the input
            x_transformed = _minmax_scaling(
                DATA, ctx_params, self.SUGGESTED_LIMITS)

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

            # Means (shape=(cases, n_im)) and standard deviations (n_im, )
            means = np.squeeze(np.log(output))

            stddevs = np.asarray((DATA["total-stdev"],
                                 DATA["inter-stdev"],
                                 DATA["intra-stdev"])).T

            # Transform the standard deviations from log10 to natural
            # logarithm
            stddevs = np.log(10**stddevs)

            # Get the means and stddevs at index corresponding to the IM
            mean[m], stddevs = _get_means_stddevs(
                DATA, imt, means, stddevs, self.component_definition)

            sig[m] = stddevs[0]
            tau[m] = stddevs[1]
            phi[m] = stddevs[2]


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
