# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""Monteiro et al. (2026) spatial cross-IMT correlation model.

The principal-component coefficients use the full precision distributed
with the authors' Matlab implementation. Coefficients at intermediate periods
are linearly interpolated in period, as specified by the publication and the
authors' code.

References
----------
Monteiro, V.A, Aristeidou, S., and O'Reilly, G. J. (2026). Spatial Cross-Correlation
Models for Next-Generation Amplitude and Cumulative Intensity Measures.
Earthquake Spectra 2026, 42, e70076. https://doi.org/10.1002/esp4.70076

Author-maintained Python implementation
---------------------------------------
https://github.com/vitorazevedomonteiro/cross-spatial-correlation-model.git
"""

import numpy
from openquake.hazardlib.correlation_models.base import (
    ResidualComponent, SpatialCrossIMTCorrelationModel)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, SA, Sa_avg2, Sa_avg3, PGV, FIV3

_PERIODS = numpy.array([
    0.1, 0.5, 1.0, 2.0, 3.0], dtype=numpy.float64)

# Row ranges of _PCA_COEFFICIENTS. SA, Sa_avg2, Sa_avg3 and FIV3 each occupy
# a five-row block, one row per entry of _PERIODS, in that order; PGA and
# PGV are period-independent and each occupy a single row.
_IMT_ROWS = {
    'SA': slice(0, 5),
    'Sa_avg2': slice(5, 10),
    'Sa_avg3': slice(10, 15),
    'FIV3': slice(15, 20),
    'PGA': 20,
    'PGV': 21,
}

# Full-precision PCA loadings from PCA_coefficients.mat. All nineteen
# components are used by the authors' current reference implementation.
_PCA_COEFFICIENTS = numpy.array([
    [0.135925640, 0.425895839, -0.304606915,
     0.215062751, 0.090762964, 0.214068375, 
     -0.019522902, 0.365363877, 0.609631498,
     -0.110867056, -0.151692723, -0.027955892,
     -0.088830512,	-0.042040118,  0.070210847,
     -0.116691381, -0.027943943, 0.028561306,
     -0.107261362,  0.086681025, 0.074181340,
     0.105391963],
    [0.183322706, 0.186191781, 0.297506932,
     -0.469258899, -0.465951413, -0.296623665,
     -0.058762200, 0.291364610,	0.252421534,
     0.165038896, 0.166516239, -0.111470366,
     0.244123792, -0.011611688, -0.135229415,
     0.052474300, -0.010159638,	0.033378241,
     -0.081522994, -0.083252688, 0.006655717,
     0.053387842],
    [0.211835488, -0.016367706, 0.397640891,
     0.133421264, 0.126035527, 0.535801932,
     0.228683847, -0.293643500, 0.204983605,
     0.409680264, 0.085597792, -0.132990641,
     0.186001950, 0.054228931, -0.209246130,
     -0.053197205, -0.044143152, 0.069113205,
     -0.027967290, 0.030732392, -0.057380220,
     0.081739653],
    [0.221822560, -0.174642377, -0.001307827,
     0.504314050, -0.087984181,	-0.366669062,
     -0.491985706, -0.077535462, 0.160547688,
     0.319657007, 0.019017470,  0.041756772,
     -0.148232733, 0.171287993, -0.211936594,
     -0.135083432, 0.116850905, -0.039240380,
     0.007375816, -0.065817510, -0.071982402,
     -0.080068339],
    [0.216286415, -0.211744610, -0.318130387,
     0.146790669, -0.351890882,	-0.142898418,
     0.684447313, -0.023099142,	0.030584922,
     -0.040101402, -0.072329408, -0.041461491,
     0.032764186, 0.287496964, -0.096049513,
     -0.136181568, 0.104706389, -0.166786546,
     0.020909404, -0.090005721,	0.063733406,
     0.002583636],
    [0.147704017, 0.419328798, -0.230014625,
     0.119174270, 0.025833476, 0.063898394,
     -0.021201818, 0.011270772, -0.173294313,
     0.085624225, -0.002614084, 0.084677461,
     0.259770272, 0.045567760, -0.228277887,
     0.481758931, -0.053478440,	-0.086368953,
     0.450393104, -0.226966094, -0.074011094,
     -0.247885015],
    [0.205560782, 0.211019175, 0.224509564,
     -0.157223773, -0.172781347, 0.068794972,
     0.027545953, -0.016193682, -0.093532941,
     0.083069815, -0.229579044, 0.184158618,
     -0.373222220, 0.084275560, 0.161301421,
     -0.190036755, 0.290250964, 0.028369349,
     0.498256908, 0.392512836, -0.019223462,
     -0.062762642],
    [0.232906094, 0.028446169, 0.227469062,
     0.129062179, -0.066973735,	0.025780410,
     -0.147493482, -0.067110848, -0.134906022,
     -0.159388968, -0.187964832, -0.187526482,
     -0.060288095, 0.010960500, 0.150321577,
     0.143106630, -0.126397473,	-0.334735354,
     0.107430839, -0.228614814,	0.486024030,
     0.506118741],
    [0.242847633, -0.122874441, -0.045336653,
     0.105405583, -0.180115480,	-0.028342355,
     0.067796941, -0.059091063, -0.009189205,
     -0.108337356, -0.059576622, -0.088587410,
     -0.193206107, -0.288101183, 0.108232277,
     0.115096130, -0.171974694,	0.673750743,
     0.161139878, -0.261987392, -0.276069554,
     0.220418058],
    [0.235088181, -0.174112632, -0.208723859,
     -0.127705401, -0.122843848, 0.157208333,
     -0.120965285, -0.118316643, 0.061630742,
     -0.116613381, 0.091032849, 0.066321052,
     -0.047503336, -0.352047894, -0.132652447,
     0.203055994, 0.184548353, -0.445420791,
     -0.071255945, 0.213661762, -0.458622322,
     0.278354751],
    [0.154169146, 0.403140216, -0.157418772,
     0.023244310, -0.074720701,	-0.011534520,
     -0.046036991, -0.085095471, -0.498324925,
     0.147770209, -0.217234584, 0.190338668,
     0.186037411, -0.062976864, -0.141862301,
     -0.320459310, 0.041340672,	0.135483114,
     -0.422434468, 0.030055061, -0.040688145,
     0.239288612],
    [0.222262342, 0.118286784, 0.244865139,
     0.008291649, -0.064748255,	 0.135375204,
     -0.020436624, -0.014214755, -0.061447133,
     -0.195966760, -0.194755176, -0.162949209,
     -0.15442191, -0.003028258,  0.244614559,
     -0.109932070, 0.010826480, -0.241584206,
     -0.280339819, -0.408761888, -0.306713991,
     -0.502766158],
    [0.242951743, -0.046412545, 0.066748683,
     0.190233898, -0.151323153,	-0.081518982,
     0.001332679, -0.037190805, -0.070122153,
     -0.069259813, -0.118034033, -0.076186718,
     0.113068211, 0.098191125, 0.187008287, 
     0.412549251, -0.315731094,	0.095492110,
     -0.280914157, 0.605941336,	0.064778650,
     -0.226103595],
    [0.237248768, -0.154234894, -0.205108842,
     -0.134118480, -0.129924219, 0.167259367,
     -0.109659948, -0.164464841, 0.025823657,
     -0.019486942, 0.058369302, 0.027229155,
     -0.018419170, -0.485551630, -0.173867654,
     -0.134818788, 0.059287675, 0.079494160,
     -0.008579490, -0.013893918, 0.562252721,
     -0.400009232],
    [0.219848464, -0.176862315, -0.286890567,
     -0.356754602, -0.024634216, 0.252354379,
     -0.346679081, -0.213386608, 0.106068753,
     -0.121269744, -0.006371576, 0.141032841,
     0.216395053, 0.548463329, 0.208909414,
     -0.083820137, -0.075687469, 0.138572169,
     0.037394192, -0.091951988, -0.017511413,
     0.038858075],
    [0.228923987, 0.010300995, 0.232469904,
     -0.029120446, 0.195023193,	-0.133762317,
     0.103626729, 0.007055554, 0.061032524,
     -0.362675536, 0.130076252, 0.502880397,
     -0.106485633, 0.028505024, -0.347141087,
     -0.186374930, -0.492510408, -0.081091062,
     0.053279783, 0.007791766, -0.035732980,
     -0.010143409],
    [0.231549529, -0.079028972, 0.214156250,
     0.106398076, 0.196913760, 0.037884632,
     0.056187977, 0.213684841, -0.044978131,
     -0.268531093, 0.161413910, 0.271998819,
     0.067292398, 0.117096864, -0.033087385,
     0.282985918, 0.632949827, 0.225627478,
     -0.209363579, -0.078511395, 0.133670772,
     0.030715028],
    [0.234055192, -0.143068708, 0.044134728,
     0.178174413, 0.170016118, -0.065533550,
     -0.042980331, 0.280826435, -0.145154146,
     -0.141630622, 0.138341875, -0.204991522,
     0.549674382, -0.180753987, 0.231598241,
     -0.395824102, 0.018754492, -0.045713111,
     0.305798504, 0.140044224, -0.116285362,
     -0.025267097],
    [0.230112173, -0.157553595, -0.113490261,
     -0.089557491, 0.185838467, -0.002733499,
     0.127164162, 0.300583508, -0.081938915,
     0.556192813, 0.126726282, 0.356235441,
     -0.136120756, -0.107598358, 0.429541096,
     0.101875777, -0.172924367,	-0.131946559,
     -0.080054545, -0.140770137, 0.049480523,
     0.015997258],
    [0.223534065, -0.149771535, -0.119896544,
     -0.225231821, 0.279322296, 0.098460754,
     -0.051361149, 0.402673436, -0.271745958,
     0.054887155, -0.054640175, -0.461622418,
     -0.314150456, 0.198619064, -0.403903742,
     0.008987361, -0.071696476, 0.053353502,
     -0.024229093, 0.082586104, -0.014334545,
     -0.009941565],
    [0.168501568, 0.362160761, -0.121224871,
     0.007123073, 0.089290615,-0.138881354,
     0.060204080, -0.292995192, -0.071898471,
     -0.058992196, 0.722159436, -0.249721220,
     -0.245712199, 0.087409427, 0.189317198,
     -0.062756133, 0.021245565, -0.001256152, 
     -0.047401856, 0.061373806, 0.039507412,
     0.024958721],
    [0.213470506, 0.052739442, -0.036445378,
     -0.268495629, 0.517932378,	-0.468898279,
     0.135030388, -0.349477293,	0.231423352,
     0.064842413, -0.362337983, -0.129135597,	
     0.104233036, -0.104265433, 0.035913972,  
     0.069090490, 0.126649676, 0.009687264,
     -0.004816915, 0.001118124, -0.007737344,
     0.000237981],
])


# Full-precision values from variogramModel_19PC.mat. Only the first four
# components have short- and long-range structure; the rest are nugget.
_NUGGET = numpy.array([
    8.14481289, 0.953752621, 0.286321863, 0.111971649, 0.095674817, 0.06665654,
    0.049370678, 0.037466934, 0.030873087, 0.022642474, 0.017726169, 0.01420243, 
    0.01151974, 0.006642143, 0.00818584, 0.004073281, 0.004029638, 0.002213756, 
    0.002462062, 0.001954815, 0.001336528, 0.000919364
])
_SHORT_SILL = numpy.array([
    13.20035514, 2.257911792, 0.413021836, 0.093559985, 0.122092004, 0.070614382, 
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0,
])
_SHORT_RANGE = numpy.array([
    94.14906432, 61.67331411, 46.64523871, 28.43299213, 31.26680244, 28.0277504,
    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    1.0,
])
_LONG_SILL = numpy.array([
    0.00, 1.429126771, 0.638822635, 0.244837227, 0.065942052, 0.054436852,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0,
])
_LONG_RANGE = numpy.array([
    216.8645443, 226.4852379, 227.7251389, 228.1269782, 228.0093191, 228.023073,
    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    1.0,
])
_SILLS = _NUGGET + _SHORT_SILL + _LONG_SILL

def _interpolate_coefficients(imts):
    """Linearly interpolate each PCA coefficient at the requested IMTs.

    SA, Sa_avg2, Sa_avg3 and FIV3 vary continuously with period and are
    interpolated within their own block of _PCA_COEFFICIENTS; PGA and PGV
    are period-independent and contribute a single, fixed row.
    """
    rows = []
    for imt in imts:
        block = _PCA_COEFFICIENTS[_IMT_ROWS[imt.name]]
        if block.ndim == 1:
            rows.append(block)
        else:
            rows.append([
                numpy.interp(imt.period, _PERIODS, coefficients)
                for coefficients in block.T
            ])
    return numpy.array(rows)

def _principal_component_covariances(distances):
    """Return the twenty-two principal-component covariance blocks."""
    distances = distances[numpy.newaxis, :, :]
    same_site = distances == 0
    short_range = numpy.exp(
        -3 * distances / _SHORT_RANGE[:, numpy.newaxis, numpy.newaxis])
    long_range = numpy.exp(
        -3 * distances / _LONG_RANGE[:, numpy.newaxis, numpy.newaxis])
    return (
        _NUGGET[:, numpy.newaxis, numpy.newaxis] * same_site +
        _SHORT_SILL[:, numpy.newaxis, numpy.newaxis] * short_range +
        _LONG_SILL[:, numpy.newaxis, numpy.newaxis] * long_range)


def _normalized_coefficients(imts):
    coefficients = _interpolate_coefficients(imts)
    variances = (coefficients ** 2) @ _SILLS
    return coefficients / numpy.sqrt(variances[:, numpy.newaxis])

@register_model(
    description='Monteiro et al. (2026) within-event joint correlation')
class MonteiroEtAl2026(SpatialCrossIMTCorrelationModel):
    """Within-event spatial cross-IMT model by monteiro et al. (2026).

    The model uses all twenty two principal components, following the authors'
    current reference implementation, and was calibrated for 5%-damped SA,
    average spectral acceleration (Sa_avg2 and Sa_avg3), filtered incremental
    velocity (FIV3) from 0.1 to 3 seconds. PGA and PGV are also suported in this study.
    """

    SUPPORTS_CIRCULANT_EMBEDDING = True
    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.WITHIN_EVENT
    # Note: aside from FIV3, all intensity measures are defined for RotD50
    # (FIV3 is defined for the geometric mean), therefore
    # DEFINED_FOR_INTENSITY_MEASURE_COMPONENT cannot be uniformly specific as RotD50 for this model
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        SA, PGA, PGV, Sa_avg2, Sa_avg3, FIV3}
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.1, 3.0)
    DEFINED_FOR_Sa_avg_PERIOD_RANGE = (0.1, 3.0)


    def _correlation_block(self, distances, imts1, imts2, context=None):
        """Return the joint correlation block in IMT-major order."""
        coefficients1 = _normalized_coefficients(imts1)
        coefficients2 = _normalized_coefficients(imts2)
        pc_covariances = _principal_component_covariances(distances)
        correlation = numpy.einsum(
            'ik,kab,jk->iajb', coefficients1, pc_covariances,
            coefficients2)
        return correlation.reshape(
            len(imts1) * distances.shape[0],
            len(imts2) * distances.shape[1])
