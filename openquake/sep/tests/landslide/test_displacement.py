import numpy as np
from openquake.sep.landslide.static_safety_factor import infinite_slope_fs
from openquake.sep.landslide.probability import jibson_etal_2000_probability
from openquake.sep.landslide.displacement import (
    critical_accel,
    jibson_2007_model_a,
    jibson_2007_model_b,
    cho_rathje_2022,
    fotopoulou_pitilakis_2015_model_a,
    fotopoulou_pitilakis_2015_model_b,
    fotopoulou_pitilakis_2015_model_c,
    fotopoulou_pitilakis_2015_model_d,
    saygili_rathje_2008,
    rathje_saygili_2009,
    jibson_etal_2000,
)

def arr(scalar, n=1):
    return np.full(n, scalar)


def test_critical_accel():
    slopes = np.array([0.0, 0.052408, 0.176327, 0.466308, 1.191754, 2.747477])
    fs = infinite_slope_fs(
        slopes,
        cohesion=20e3,
        friction_angle=32.0,
        saturation_coeff=0.0,
        slab_thickness=2.5,
        soil_dry_density=1500.0,
    )
    ca = critical_accel(fs, slopes)
    ca_ = np.array(
        [1.16852228e+00, 1.11533974e+00, 9.85390913e-01, 6.87368298e-01,
       1.79276574e-01, 1.00000000e-04]
    )
    np.testing.assert_allclose(ca, ca_)


def test_jibson_2007_a_landslide():
    pgas = np.linspace(0.0, 2.0, num=10)
    Disp = jibson_2007_model_a(pgas, crit_accel=arr(1.0, 10))
    Disp_ = np.array(
        [
            0.00000000e00,
            0.00000000e00,
            0.00000000e00,
            0.00000000e00,
            0.00000000e00,
            8.70561128e-05,
            9.66583692e-04,
            2.78057386e-03,
            5.41818012e-03,
            8.77344007e-03,
        ]
    )
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_jibson_2007_b_landslide():
    pgas = np.linspace(0.0, 2.0, num=10)
    Disp = jibson_2007_model_b(pgas, crit_accel=arr(1.0, 10), mag=6.5)
    Disp_ = np.array(
        [
            0.000000e00,
            0.000000e00,
            0.000000e00,
            0.000000e00,
            0.000000e00,
            6.006612e-05,
            6.681122e-04,
            1.929713e-03,
            3.775745e-03,
            6.137864e-03,
        ]
    )
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_cho_rathje_2022():
    pgv_ = np.array([1.40e01, 1.40e01])
    tslope_ = np.array([1.2, 1.2])
    crit_accel_ = np.array([0.02, 0.02])
    hratio_ = np.array([0.4, 0.4])
    Disp = cho_rathje_2022(pgv_, tslope_, crit_accel_, hratio_)
    Disp_ = np.array([6.25910347e-02, 6.25910347e-02])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_fotopoulou_pitilakis_2015_a():
    pgv = arr(1.40e01)
    mag = 6.5
    crit_accel = arr(0.02)
    Disp = fotopoulou_pitilakis_2015_model_a(pgv, mag, crit_accel)
    Disp_ = np.array([4.0162336e-02])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_fotopoulou_pitilakis_2015_b():
    pga = arr(2.84e-01)
    mag = 6.5
    crit_accel = arr(0.02)
    Disp = fotopoulou_pitilakis_2015_model_b(pga, mag, crit_accel)
    Disp_ = np.array([0.100601584210005])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_fotopoulou_pitilakis_2015_c():
    pga = arr(2.84e-01)
    mag = 6.5
    crit_accel = arr(0.02)
    Disp = fotopoulou_pitilakis_2015_model_c(pga, mag, crit_accel)
    Disp_ = np.array([0.910418270987024])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_fotopoulou_pitilakis_2015_d():
    pgv = arr(1.40e01)
    pga = arr(2.84e-01)
    crit_accel = arr(0.02)
    Disp = fotopoulou_pitilakis_2015_model_d(pgv, pga, crit_accel)
    Disp_ = np.array([0.073120196833772])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_saygili_rathje_2008_landslide():
    pga = arr(2.84e-01)
    pgv = arr(1.40e01)
    crit_accel = arr(0.02)
    Disp = saygili_rathje_2008(pga, pgv, crit_accel)
    Disp_ = np.array([0.186370166332798])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_rathje_saygili_2009_landslide():
    pga = arr(2.84e-01)
    mag = 6.5
    crit_accel = arr(0.02)
    Disp = rathje_saygili_2009(pga, mag, crit_accel)
    Disp_ = np.array([0.548088621109107])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_jibson_etal_2000_landslide():
    ia = arr(1.90e00)
    crit_accel = arr(0.02)
    Disp = jibson_etal_2000(ia, crit_accel)
    Disp_ = np.array([1.8366713252543503])
    np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


def test_jibson_etal_2000_landslide_probability():
    Disp_ = np.array([1.8366713252543503])
    Prob = jibson_etal_2000_probability(Disp_)
    Prob_ = np.array([0.335])
    np.testing.assert_allclose(Prob, Prob_, atol=1e-9)
