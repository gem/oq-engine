import unittest

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

class critical_acceleration_landslide_test(unittest.TestCase):


    def setUp(self):
        self.slopes = np.array([0.0, 3.0, 10.0, 25.0, 50.0, 70.0])
        self.fs = infinite_slope_fs(
            self.slopes,
            cohesion=20e3,
            friction_angle=32.0,
            saturation_coeff=0.0,
            slab_thickness=2.5,
            soil_dry_density=1500.0,
        )

    def test_critical_accel(self):
        ca = critical_accel(self.fs, self.slopes)
        ca_ = np.array(
            [11.46329996, 10.94148504, 9.66668506, 6.74308623, 1.75870504, 0.0]
        )
        np.testing.assert_allclose(ca, ca_)



class jibson_2007_a_landslide_test(unittest.TestCase):


    def test_jibson_2007_a_landslide(self):
        pgas = np.linspace(0.0, 2.0, num=10)
        Disp = jibson_2007_model_a(pgas, crit_accel=1.0)

        Disp_ = np.array(
            [
                0.00000000e+00,
                0.00000000e+00,
                0.00000000e+00,
                0.00000000e+00,
                0.00000000e+00,
                8.70561128e-05,
                9.66583692e-04,
                2.78057386e-03,
                5.41818012e-03,
                8.77344007e-03,
                 
            ]
        )
        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)



class jibson_2007_b_landslide_test(unittest.TestCase):


    def test_jibson_2007_b_landslide(self):
        pgas = np.linspace(0.0, 2.0, num=10)
        Disp = jibson_2007_model_b(pgas, crit_accel=1.0, mag=6.5)

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

    

class cho_rathje_2022_landslide_test(unittest.TestCase):

    def test_cho_rathje_2022(self):
  
        pgv_ =  np.array(
            [1.40E+01, 1.40E+01])
        tslope_ =  np.array(
            [1.2, 1.2])
        crit_accel_= np.array(
            [0.02, 0.02])
        hratio_ = np.array(
            [0.4, 0.4])

        Disp = cho_rathje_2022(pgv_, tslope_, crit_accel_, hratio_)

        Disp_ = np.array(
            [
            6.25910347E-02, 6.25910347E-02
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)
        
class fotopoulou_pitilakis_2015_a_landslide_test(unittest.TestCase):

    def test_fotopoulou_pitilakis_2015_a(self):
  
        pgv =  1.40E+01
        mag = 6.5
        crit_accel = 0.02
                

        Disp = fotopoulou_pitilakis_2015_model_a(pgv, mag, crit_accel)
        print(Disp)

        Disp_ = np.array(
            [
            4.0162336E-02,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)
        
        
        
class fotopoulou_pitilakis_2015_b_landslide_test(unittest.TestCase):

    def test_fotopoulou_pitilakis_2015_b(self):

        pga = 2.84E-01
        mag = 6.5
        crit_accel = 0.02
        
        Disp = fotopoulou_pitilakis_2015_model_b(pga, mag, crit_accel)

        Disp_ = np.array(
            [
            0.100601584210005,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


class fotopoulou_pitilakis_2015_c_landslide_test(unittest.TestCase):

    def test_fotopoulou_pitilakis_2015_c(self):
 
        pga = 2.84E-01
        mag = 6.5
        crit_accel = 0.02


        Disp = fotopoulou_pitilakis_2015_model_c(pga, mag, crit_accel)

        Disp_ = np.array(
            [
            0.910418270987024,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)


        
class fotopoulou_pitilakis_2015_d_landslide_test(unittest.TestCase):

    def test_fotopoulou_pitilakis_2015_d(self):
        
        pgv = 1.40E+01
        pga = 2.84E-01
        crit_accel = 0.02

        Disp = fotopoulou_pitilakis_2015_model_d(pgv, pga, crit_accel)

        Disp_ = np.array(
            [
            0.073120196833772,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)
        
        
class saygili_rathje_2008_landslide_test(unittest.TestCase):

    
    def test_saygili_rathje_2008_landslide(self):
    
        pga = 2.84E-01
        pgv = 1.40E+01
        crit_accel = 0.02
                
        Disp = saygili_rathje_2008(pga, pgv, crit_accel)

        Disp_ = np.array(
            [
            0.186370166332798,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)
        

class rathje_saygili_2009_landslide_test(unittest.TestCase):


    def test_rathje_saygili_2009_landslide(self):
      
        pga = 2.84E-01
        mag = 6.5
        crit_accel = 0.02

        Disp = rathje_saygili_2009(pga, mag, crit_accel)

        Disp_ = np.array(
            [
            0.548088621109107,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)    
        
        
class jibson_etal_2000_test_landslide(unittest.TestCase):


    def test_jibson_etal_2000_landslide(self):
      
        ia = 1.90E+00
        crit_accel = 0.02

        Disp = jibson_etal_2000(ia, crit_accel)

        Disp_ = np.array(
            [
            1.8366713252543503,
            ]
        )

        np.testing.assert_allclose(Disp, Disp_, atol=1e-9)
        
    def test_jibson_etal_2000_landslide_probability(self):
        Disp_ = np.array(
            [
                1.8366713252543503,

            ]
        )

        Prob = jibson_etal_2000_probability(Disp_)

        Prob_ = np.array(
            [
                0.335,
            ]
        )

        np.testing.assert_allclose(Prob, Prob_, atol=1e-9)
