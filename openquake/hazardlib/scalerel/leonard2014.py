"""
Module :mod:`openquake.hazardlib.scalerel.leonard_2014` implements 
:class:`Leonard2014_SCR`
:class:`Leonard2014_Active`
"""
from numpy import power, log10
from openquake.hazardlib.scalerel.base import BaseMSRSigma, BaseASRSigma

class Leonard2014_SCR(BaseMSRSigma, BaseASRSigma):
    """
    Leonard, M., 2014. Self-consistent earthquake fault-scaling relations: 
    Update and extension to stable continental strike-slip faults.
    Bulletin of the Seismological Society of America, 104(6), pp 2953-2965.
    
    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude.
        """
        if rake is None:
            # Return average of strike-slip and dip-slip curves
            return power(10,(mag - 4.185))
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike-slip
            return power(10,(mag - 4.18))
        else:
            # Dip-slip (thrust or normal), and undefined rake
            return power(10,(mag - 4.19))

    def get_std_dev_area(self, mag, rake):
        """
        Returns None for now
        """
        return None

    def get_median_mag(self, area, rake):
        """
        Returns magnitude for a given fault area
        """
        if rake is None:
            # Return average of strike-slip and dip-slip curves
            return log10(area) + 4.185
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return log10(area) + 4.18
        else:
            # Dip slip (thrust or normal), and undefined rake
            return log10(area) + 4.19

    def get_std_dev_mag(self, area, rake):
        """
        Returns None for now
        """
        return None

class Leonard2014_Interplate(BaseMSRSigma, BaseASRSigma):
    """
    Leonard, M., 2014. Self-consistent earthquake fault-scaling relations: 
    Update and extension to stable continental strike-slip faults.
    Bulletin of the Seismological Society of America, 104(6), pp 2953-2965.

    Implements both magnitude-area and area-magnitude scaling relationships.
    """
    def get_median_area(self, mag, rake):
        """
        Calculates median fault area from magnitude. 
        """
        if rake is None:
            # Return average of strike-slip and dip-slip curves
            return power(10,(mag - 3.995))
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return power(10,(mag - 3.99))
        else:
            # Dip slip (thrust or normal), and undefined rake
            return power(10,(mag - 4.00))

    def get_std_dev_area(self, mag, rake):
        """
        Returns None for now
        """
        return None

    def get_median_mag(self, area, rake):
        """
        Calculates median magnitude from fault area. 
        """
        if rake is None:
            # Return average of strike-slip and dip-slip curves
            return log10(area) + 3.995
        elif (-45 <= rake <= 45) or (rake >= 135) or (rake <= -135):
            # strike slip
            return log10(area) + 3.99
        else:
            # Dip slip (thrust or normal), and undefined rake
            return log10(area) + 4.00

    def get_std_dev_mag(self, area, rake):
        """
        Returns None for now
        """
        return None
