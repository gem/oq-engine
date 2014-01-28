"""
Data is taken from the report "PEER 2010/106 - Verification of Probabilistic
Seismic Hazard Analysis Computer Programs" by  Patricia Thomas, Ivan Wong,
Norman Abrahamson, see
`http://peer.berkeley.edu/publications/peer_reports/reports_2010/web_PEER_10106_THOMASetal.pdf`_.
"""
from openquake.hazardlib.geo import Polygon, Point, Line
from openquake.hazardlib.site import Site
from openquake.hazardlib.imt import PGA
from openquake.hazardlib.mfd import TruncatedGRMFD, EvenlyDiscretizedMFD
from openquake.hazardlib.source import SimpleFaultSource
from openquake.hazardlib.pmf import PMF

import numpy
from decimal import Decimal


IMT = PGA()

# page 12
SET1_RUPTURE_ASPECT_RATIO = 2.0

# page A-3
SET1_CASE10_SOURCE_POLYGON = SET1_CASE11_SOURCE_POLYGON = Polygon([
    Point(-122.000, 38.901),
    Point(-121.920, 38.899),
    Point(-121.840, 38.892),
    Point(-121.760, 38.881),
    Point(-121.682, 38.866),
    Point(-121.606, 38.846),
    Point(-121.532, 38.822),
    Point(-121.460, 38.794),
    Point(-121.390, 38.762),
    Point(-121.324, 38.727),
    Point(-121.261, 38.688),
    Point(-121.202, 38.645),
    Point(-121.147, 38.600),
    Point(-121.096, 38.551),
    Point(-121.050, 38.500),
    Point(-121.008, 38.446),
    Point(-120.971, 38.390),
    Point(-120.940, 38.333),
    Point(-120.913, 38.273),
    Point(-120.892, 38.213),
    Point(-120.876, 38.151),
    Point(-120.866, 38.089),
    Point(-120.862, 38.026),
    Point(-120.863, 37.963),
    Point(-120.869, 37.900),
    Point(-120.881, 37.838),
    Point(-120.899, 37.777),
    Point(-120.921, 37.717),
    Point(-120.949, 37.658),
    Point(-120.982, 37.601),
    Point(-121.020, 37.545),
    Point(-121.063, 37.492),
    Point(-121.110, 37.442),
    Point(-121.161, 37.394),
    Point(-121.216, 37.349),
    Point(-121.275, 37.308),
    Point(-121.337, 37.269),
    Point(-121.403, 37.234),
    Point(-121.471, 37.203),
    Point(-121.542, 37.176),
    Point(-121.615, 37.153),
    Point(-121.690, 37.133),
    Point(-121.766, 37.118),
    Point(-121.843, 37.108),
    Point(-121.922, 37.101),
    Point(-122.000, 37.099),
    Point(-122.078, 37.101),
    Point(-122.157, 37.108),
    Point(-122.234, 37.118),
    Point(-122.310, 37.133),
    Point(-122.385, 37.153),
    Point(-122.458, 37.176),
    Point(-122.529, 37.203),
    Point(-122.597, 37.234),
    Point(-122.663, 37.269),
    Point(-122.725, 37.308),
    Point(-122.784, 37.349),
    Point(-122.839, 37.394),
    Point(-122.890, 37.442),
    Point(-122.937, 37.492),
    Point(-122.980, 37.545),
    Point(-123.018, 37.601),
    Point(-123.051, 37.658),
    Point(-123.079, 37.717),
    Point(-123.101, 37.777),
    Point(-123.119, 37.838),
    Point(-123.131, 37.900),
    Point(-123.137, 37.963),
    Point(-123.138, 38.026),
    Point(-123.134, 38.089),
    Point(-123.124, 38.151),
    Point(-123.108, 38.213),
    Point(-123.087, 38.273),
    Point(-123.060, 38.333),
    Point(-123.029, 38.390),
    Point(-122.992, 38.446),
    Point(-122.950, 38.500),
    Point(-122.904, 38.551),
    Point(-122.853, 38.600),
    Point(-122.798, 38.645),
    Point(-122.739, 38.688),
    Point(-122.676, 38.727),
    Point(-122.610, 38.762),
    Point(-122.540, 38.794),
    Point(-122.468, 38.822),
    Point(-122.394, 38.846),
    Point(-122.318, 38.866),
    Point(-122.240, 38.881),
    Point(-122.160, 38.892),
    Point(-122.080, 38.899),
])

# page A-3
SET1_CASE10_SITE1 = SET1_CASE11_SITE1 = Site(
    location=Point(-122.0, 38.0), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE10_SITE2 = SET1_CASE11_SITE2 = Site(
    location=Point(-122.0, 37.550), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE10_SITE3 = SET1_CASE11_SITE3 = Site(
    location=Point(-122.0, 37.099), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE10_SITE4 = SET1_CASE11_SITE4 = Site(
    location=Point(-122.0, 36.874), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)


# page 14
SET1_CASE10_MFD = TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                                 max_mag=6.5, bin_width=0.1)
SET1_CASE11_MFD = SET1_CASE10_MFD
# page 14
SET1_CASE10_HYPOCENTER_DEPTH = 5.0

# page A-15
SET1_CASE10_IMLS = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
SET1_CASE10_SITE1_POES = [
    3.87E-02, 2.19E-02, 2.97E-03, 9.22E-04, 3.59E-04,
    1.31E-04, 4.76E-05, 1.72E-05, 5.38E-06, 1.18E-06
]
SET1_CASE10_SITE2_POES = [
    3.87E-02, 1.82E-02, 2.96E-03, 9.21E-04, 3.59E-04,
    1.31E-04, 4.76E-05, 1.72E-05, 5.37E-06, 1.18E-06
]
SET1_CASE10_SITE3_POES = [
    3.87E-02, 9.32E-03, 1.39E-03, 4.41E-04, 1.76E-04,
    6.47E-05, 2.27E-05, 8.45E-06, 2.66E-06, 5.84E-07
]
SET1_CASE10_SITE4_POES = [
    3.83E-02, 5.33E-03, 1.25E-04, 1.63E-06, 0,
    0, 0, 0, 0, 0
]

# page 21
SET1_CASE11_HYPOCENTERS = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

# page A-16
SET1_CASE11_IMLS = [0.001, 0.01, 0.05, 0.1, 0.15,
                    0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
SET1_CASE11_SITE1_POES = [
    3.87E-02, 2.18E-02, 2.83E-03, 7.91E-04, 2.43E-04,
    7.33E-05, 2.23E-05, 6.42E-06, 1.31E-06, 1.72E-07,
    3.05E-09
]
SET1_CASE11_SITE2_POES = [
    3.87E-02, 1.81E-02, 2.83E-03, 7.90E-04, 2.44E-04,
    7.32E-05, 2.21E-05, 6.50E-06, 1.30E-06, 1.60E-07,
    3.09E-09
]
SET1_CASE11_SITE3_POES = [
    3.87E-02, 9.27E-03, 1.32E-03, 3.79E-04, 1.18E-04,
    3.60E-05, 1.08E-05, 2.95E-06, 6.18E-07, 7.92E-08,
    1.34E-09
]
SET1_CASE11_SITE4_POES = [
    3.84E-02, 5.33E-03, 1.18E-04, 1.24E-06, 0,
    0, 0, 0, 0, 0,
    0
]

# Starting from the input data as defined in the PEER Report page 13:
#
# magnitude = 6.0
# b_value = -0.9
# slip_rate = 2e-3 # m/year
# rigidity = 3e10 # N/m^2
# fault_length = 25.0 * 1e3 # m
# fault_width = 12.0 * 1e3 # m
#
# The total seismic moment rate can be computed as:
#
# seismic_moment_rate = rigidity * fault_length * fault_width * slip_rate
#
# From which we can derived the incremental a value:
#
# a_incremental = log10(seismic_moment_rate) - (1.5 + b_value) * magnitude - 9.05
#
# and finally the rate:
#
# rate = 10 ** (a_incremental + b_value * magnitude)
SET1_CASE2_MFD = EvenlyDiscretizedMFD(min_mag=6.0, bin_width=0.01,
                                      occurrence_rates=[0.0160425168864])
SET1_CASE1TO9_RAKE = 0

# page A-3
SET1_CASE1TO9_FAULT_TRACE = Line([Point(-122.0, 38.0),
                                  Point(-122.0, 38.22480)])

# page A-17
SET1_CASE1TO9_UPPER_SEISMOGENIC_DEPTH = 0.0
SET1_CASE1TO9_LOWER_SEISMOGENIC_DEPTH = 12.0
SET1_CASE1TO9_DIP = 90

# page A-3
SET1_CASE1TO9_SITE1 = Site(
    location=Point(-122.000, 38.113), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE1TO9_SITE2 = Site(
    location=Point(-122.114, 38.113), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE1TO9_SITE3 = Site(
    location=Point(-122.570, 38.111), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE1TO9_SITE4 = Site(
    location=Point(-122.000, 38.000), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE1TO9_SITE5 = Site(
    location=Point(-122.000, 37.910), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE1TO9_SITE6 = Site(
    location=Point(-122.000, 38.225), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)
SET1_CASE1TO9_SITE7 = Site(
    location=Point(-121.886, 38.113), vs30=800.0, vs30measured=True,
    z1pt0=1.0, z2pt5=2.0
)

# page A-8
SET1_CASE2_IMLS = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3,
                   0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65]
SET1_CASE2_SITE1_POES = [
    1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02,
    1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02, 1.18E-02,
    8.23E-03, 5.23E-03, 2.64E-03, 3.63E-04, 0.00E+00
]
SET1_CASE2_SITE2_POES = [
    1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02,
    1.59E-02, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
    0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00
]
SET1_CASE2_SITE3_POES = [
    1.59E-02, 1.59E-02, 0.00E+00, 0.00E+00, 0.00E+00,
    0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
    0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00
]
SET1_CASE2_SITE4_POES = [
    1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02,
    1.58E-02, 1.20E-02, 8.64E-03, 5.68E-03, 3.09E-03,
    1.51E-03, 6.08E-04, 1.54E-04, 2.92E-06, 0.00E+00
]
SET1_CASE2_SITE5_POES = [
    1.59E-02, 1.59E-02, 1.59E-02, 1.56E-02, 7.69E-03,
    1.60E-03, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
    0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00
]
SET1_CASE2_SITE6_POES = [
    1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02,
    1.58E-02, 1.20E-02, 8.64E-03, 5.68E-03, 3.09E-03,
    1.51E-03, 6.08E-04, 1.54E-04, 2.92E-06, 0.00E+00
]
SET1_CASE2_SITE7_POES = [
    1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02, 1.59E-02,
    1.59E-02, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
    0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00
]

# page 13
SET1_CASE5_MFD = TruncatedGRMFD(a_val=3.1292, b_val=0.9, min_mag=5.0,
                                max_mag=6.5, bin_width=0.1)

# page A-9
SET1_CASE5_IMLS = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4,
                   0.45, 0.5, 0.55, 0.6, 0.7, 0.8]
SET1_CASE5_SITE4_POES = [
    3.99E-02, 3.99E-02, 3.98E-02, 2.99E-02, 2.00E-02,
    1.30E-02, 8.58E-03, 5.72E-03, 3.88E-03, 2.69E-03,
    1.91E-03, 1.37E-03, 9.74E-04, 6.75E-04, 2.52E-04,
    0.00E+00
]
SET1_CASE5_SITE5_POES = [
    3.99E-02, 3.99E-02, 3.14E-02, 1.21E-02, 4.41E-03,
    1.89E-03, 7.53E-04, 1.25E-04, 0.00E+00, 0.00E+00,
    0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00, 0.00E+00,
    0.00E+00
]
SET1_CASE5_SITE6_POES = [
    3.99E-02, 3.99E-02, 3.98E-02, 2.99E-02, 2.00E-02,
    1.30E-02, 8.58E-03, 5.72E-03, 3.88E-03, 2.69E-03,
    1.91E-03, 1.37E-03, 9.74E-04, 6.75E-04, 2.52E-04,
    0.00E+00
]

# page A-11
SET1_CASE5_SITE1_POES = [
    4.00E-02, 4.00E-02, 4.00E-02, 3.99E-02, 3.46E-02,
    2.57E-02, 1.89E-02, 1.37E-02, 9.88E-03, 6.93E-03,
    4.84E-03, 3.36E-03, 2.34E-03, 1.52E-03, 5.12E-04,
    0
]
SET1_CASE5_SITE2_POES = [
    4.00E-02, 4.00E-02, 4.00E-02, 3.31E-02, 1.22E-02,
    4.85E-03, 1.76E-03, 2.40E-04, 0, 0,
    0, 0, 0, 0, 0,
    0
]
SET1_CASE5_SITE3_POES = [
    4.00E-02, 4.00E-02, 0, 0, 0,
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,
    0
]
SET1_CASE5_SITE7_POES = [
    4.00E-02, 4.00E-02, 4.00E-02, 3.31E-02, 1.22E-02,
    4.85E-03, 1.76E-03, 2.40E-04, 0, 0,
    0, 0, 0, 0, 0,
    0
]

# rupture-related data for case 2 source
SET1_CASE2_SOURCE_DATA = {
    'num_rups_strike': 12,
    'num_rups_dip': 6,
    'mag': 6.,
    'rake': 0.,
    'tectonic_region_type': 'Active Shallow Crust',
    'source_typology': SimpleFaultSource,
    'pmf': PMF([(Decimal('0.9997772'), 0), (Decimal('0.0002228'), 1)]),
    'lons': numpy.zeros((8, 15)) - 122.,
    'lats': [
        numpy.tile(numpy.linspace(38.0, 38.126, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.009, 38.135, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.018, 38.144, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.027, 38.153, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.036, 38.162, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.045, 38.171, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.054, 38.180, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.063, 38.189, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.072, 38.198, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.081, 38.207, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.090, 38.216, 15), (8, 1)),
        numpy.tile(numpy.linspace(38.099, 38.225, 15), (8, 1)),
    ],
    'depths':[
        numpy.tile(numpy.linspace(0., 7., 8).reshape(-1, 1), (1, 15)),
        numpy.tile(numpy.linspace(1., 8., 8).reshape(-1, 1), (1, 15)),
        numpy.tile(numpy.linspace(2., 9., 8).reshape(-1, 1), (1, 15)),
        numpy.tile(numpy.linspace(3., 10., 8).reshape(-1, 1), (1, 15)),
        numpy.tile(numpy.linspace(4., 11., 8).reshape(-1, 1), (1, 15)),
        numpy.tile(numpy.linspace(5., 12., 8).reshape(-1, 1), (1, 15)),
    ],
    'hypo_lons': numpy.zeros((6, 12)) - 122.,
    'hypo_lats': numpy.tile(numpy.linspace(38.063, 38.162, 12), (6, 1)),
    'hypo_depths': \
        numpy.tile(numpy.linspace(3.5, 8.5, 6).reshape(-1, 1), (1, 12))
}
