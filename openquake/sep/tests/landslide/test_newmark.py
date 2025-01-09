import unittest

import numpy as np

from openquake.sep.landslide.common import static_factor_of_safety

from openquake.sep.landslide.newmark import (
    newmark_critical_accel,
    newmark_displ_from_pga_M,
    prob_failure_given_displacement,
    Cho_Rathje_2022_PGV,
    Fotopoulou_Pitilakis_2015_PGV_M,
    Fotopoulou_Pitilakis_2015_PGA_M,
    Fotopoulou_Pitilakis_2015_PGA_M_b,
    Fotopoulou_Pitilakis_2015_PGV_PGA,
    Saygili_Rathje_2008,
    Rathje_Saygili_2009_PGA_M,
    
)


class jibson_landslide_test(unittest.TestCase):
    """
    Tests the Newmark landslide functions given by Jibson with calibrations
    from his work on the Northridge earthquake.
    """

    def setUp(self):
        self.slopes = np.array([0.0, 3.0, 10.0, 25.0, 50.0, 70.0])
        self.fs = static_factor_of_safety(
            self.slopes,
            cohesion=20e3,
            friction_angle=32.0,
            saturation_coeff=0.0,
            slab_thickness=2.5,
            soil_dry_density=1500.0,
        )

    def test_newmark_critical_accel(self):
        ca = newmark_critical_accel(self.fs, self.slopes)
        ca_ = np.array(
            [11.46329996, 10.94148504, 9.66668506, 6.74308623, 1.75870504, 0.0]
        )
        np.testing.assert_allclose(ca, ca_)

    def test_newmark_displ_from_pga_M_M65(self):
        pgas = np.linspace(0.0, 2.0, num=10)
        Dns = newmark_displ_from_pga_M(pgas, critical_accel=1.0, M=6.5)

        Dn_ = np.array(
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
        np.testing.assert_allclose(Dns, Dn_, atol=1e-9)

    def test_prob_failure_given_displacement(self):
        Dn_ = np.array(
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

        pf = prob_failure_given_displacement(Dn_)

        pf_ = np.array(
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                5.368313e-06,
                2.328222e-04,
                1.222611e-03,
                3.483592e-03,
                7.407753e-03,
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)


class cho_rathje_landslide_test(unittest.TestCase):

    def test_Cho_Rathje_2022_PGV(self):
  
        PGV_ =  np.array(
            [1.40E+01, 1.40E+01])
        Tslope_ =  np.array(
            [1.2, 1.2])
        crit_accel_= np.array(
            [0.02, 0.02])
        H_ratio_ = np.array(
            [0.4, 0.4])

        pf = Cho_Rathje_2022_PGV(PGV_, Tslope_, crit_accel_, H_ratio_)

        pf_ = np.array(
            [
            6.25910347E-02, 6.25910347E-02
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)
        
class Fotopoulou_Pitilakis_PGV_M_landslide_test(unittest.TestCase):

    def test_Fotopoulou_Pitilakis_PGV_M(self):
  
        PGV =  1.40E+01
        M = 6.5
        crit_accel = 0.02
                

        pf = Fotopoulou_Pitilakis_2015_PGV_M(PGV, M, crit_accel)
        print(pf)

        pf_ = np.array(
            [
            4.0162336E-02
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)
        
        
        
class Fotopoulou_Pitilakis_PGA_M_landslide_test(unittest.TestCase):

    def test_Fotopoulou_Pitilakis_PGA_M(self):

        PGA = 2.84E-01
        M = 6.5
        crit_accel = 0.02
        
        pf = Fotopoulou_Pitilakis_2015_PGA_M(PGA, M, crit_accel)

        pf_ = np.array(
            [
            0.100601584210005
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)


class Fotopoulou_Pitilakis_PGA_M_b_landslide_test(unittest.TestCase):

    def test_Fotopoulou_Pitilakis_PGA_M_b(self):
 
        PGA = 2.84E-01
        M = 6.5
        crit_accel = 0.02


        pf = Fotopoulou_Pitilakis_2015_PGA_M_b(PGA, M, crit_accel)

        pf_ = np.array(
            [
            0.910418270987024
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)


        
class Fotopoulou_Pitilakis_PGV_PGA_landslide_test(unittest.TestCase):

    def test_Fotopoulou_Pitilakis_PGV_PGA(self):
        
        PGV = 1.40E+01
        PGA = 2.84E-01
        crit_accel = 0.02

        pf = Fotopoulou_Pitilakis_2015_PGV_PGA(PGV, PGA, crit_accel)

        pf_ = np.array(
            [
            0.073120196833772
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)
        
        
class Saygili_Rathje_2008_landslide_test(unittest.TestCase):
    
    '''

    Computation of earthquake-induced displacements of landslides by eq. 6 from Sayigili & Rathje (2008)

    Disp is the displacements in cm but then converted in m
    PGA is the peak ground acceleration in g
    crit_accel is the critical acceleration of the landslide in g
    PGV is the peak ground velocity in cm/s


    '''
    
    def test_Saygili_Rathje_2008_landslide_test(self):
    
        PGA = 2.84E-01
        PGV = 1.40E+01
        crit_accel = 0.02
                
        pf = Saygili_Rathje_2008(PGA, PGV, crit_accel)

        pf_ = np.array(
            [
            0.186370166332798
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)
        

class Rathje_Saygili_2009_PGA_M_test_landslide(unittest.TestCase):

    '''

    Computation of earthquake-induced displacements of landlsides by eq.8 from Sayigili & Rathje (2009)
    ls_disp is in cm but then converted in m
    crit_accel is the critical acceleration of the landslide in g
    PGA is the peak ground acceleration in g
    M is the moment magnitude

    '''

    def test_Rathje_Saygili_2009_PGA_M_landslide_test(self):
      
        PGA = 2.84E-01
        M = 6.5
        crit_accel = 0.02

        pf = Rathje_Saygili_2009_PGA_M(PGA, M, crit_accel)

        pf_ = np.array(
            [
            0.548088621109107
            ]
        )

        np.testing.assert_allclose(pf, pf_, atol=1e-9)    