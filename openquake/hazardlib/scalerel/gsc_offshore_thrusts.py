"""
Module :mod:`openquake.hazardlib.scalerel.gsc_offshore_thrusts` implements :class:`GSCOffshoreThrusts`.
"""
from openquake.hazardlib.scalerel.base import BaseMSR
from numpy import sin, radians


"""
Rupture scaling models as used for the 2015 Seismic Hazard Model
of Canada, as described in Adams, J., S. Halchuk, T. Allen, and 
G. Rogers (2015). Canada's 5th Generation seismic hazard model, 
as prepared for the 2015 National Building Code of Canada, 11th 
Canadian Conference on Earthquake Engineering, Victoria, Canada, 
Paper 93775.
"""
class GSCCascadia(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the Juan de Fuca segment 
    of the Cascadia subduction zone.
    
    :param seis_wid:
        hirdwired seismogenic width of the CIS source (125 km)
    
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse
        seis_width = 125.
        return (10.0 ** (3.01 + 0.001 * mag)) * seis_width
        

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01

class GSCEISO(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the outboard estimate of 
    rupture (16 km depth) for the Explorer segment of the Cascadia subduction 
    zone with an upper seismogenitc depth of 5 km and a dip of 18 degrees.
    
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
         
        # thrust/reverse
        seis_width = (16. - 5.) / sin(radians(18.))
        return (10.0 ** (1.90 + 0.001 * mag)) * seis_width
        

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01

class GSCEISB(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for best estimate landward 
    extent of rupture (22 km depth) for the Explorer segment of the Cascadia
    subduction zone with an upper seismogenitc depth of 5 km and a dip of 18 
    degrees.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
         
        # thrust/reverse
        seis_width = (22. - 5.) / sin(radians(18.))
        return (10.0 ** (1.90 + 0.001 * mag)) * seis_width
        

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01

class GSCEISI(BaseMSRSigma):
    """
    Implements magnitude-area scaling relationship for the inboard estimate of 
    rupture (28 km depth) for the Explorer segment of the Cascadia subduction 
    zone with an upper seismogenitc depth of 5 km and a dip of 18 degrees.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
         
        # thrust/reverse
        seis_width = (28. - 5.) / sin(radians(18.))
        return (10.0 ** (1.90 + 0.001 * mag)) * seis_width
        

    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCCascadia. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.01

class GSCOffshoreThrustsWIN(BaseMSR):
    """
    Implements magnitude-area scaling relationship for the Winona segment of 
    the Jan de Fuca subduction zone that is approximately scaled to give a 
    rupture length of 300 km for a MW 8 earthquake and fit the rupture length 
    of the M7.8 2012 Haida Gwaii earthquake.  Ruptures assume an upper and lower
    seismogenitc depth of 2 km and 5 km respectively, with a dip of 15 degrees.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse for WIN
        seis_width = (5. - 2.) / sin(radians(15.))
        return (10.0 ** (-2.943 + 0.677 * mag)) * seis_width
        
    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCOffshoreThrustsWIN. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.2
        
class GSCOffshoreThrustsHGT(BaseMSR):
    """
    Implements magnitude-area scaling relationship that is approximately scaled 
    to give a rupture length of 300 km for a MW 8 earthquake and fit the rupture 
    length of the M7.8 2012 Haida Gwaii earthquake. Ruptures assume an upper and 
    lower seismogenitc depth of 3 km and 22 km, respectively, with a dip of 25 
    degrees.
    """
    def get_median_area(self, mag, rake):
        """
        The values are a function of magnitude.
        """
        # thrust/reverse for HGT
        seis_width = (22. - 3.) / sin(radians(25.))
        return (10.0 ** (-2.943 + 0.677 * mag)) * seis_width  
    
    def get_std_dev_area(self, mag, rake):
        """
        Standard deviation for GSCOffshoreThrustsHGT. Magnitude is ignored.
        """
        # thrust/reverse
        return 0.2