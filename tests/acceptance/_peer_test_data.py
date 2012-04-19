"""
Data is taken from the report "PEER 2010/106 - Verification of Probabilistic
Seismic Hazard Analysis Computer Programs" by  Patricia Thomas, Ivan Wong,
Norman Abrahamson, see
`http://peer.berkeley.edu/publications/peer_reports/reports_2010/web_PEER_10106_THOMASetal.pdf`_.
"""
from nhlib.geo import Polygon, Point
from nhlib.site import Site
from nhlib.imt import PGA
from nhlib.mfd import TruncatedGRMFD


IMT = PGA()

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

# page A-15
SET1_CASE10_IMLS = [0.001, 0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]

# page 14
SET1_CASE10_MFD = TruncatedGRMFD(a_val=3.1, b_val=0.9, min_mag=5.0,
                                 max_mag=6.5, bin_width=0.1)
# page 14
SET1_CASE10_HYPOCENTER_DEPTH = 5.0

# page A-15
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
