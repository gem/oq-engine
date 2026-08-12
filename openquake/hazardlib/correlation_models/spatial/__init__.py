"""Same-IMT spatial correlation models."""

from openquake.hazardlib.correlation_models.spatial.heresi_miranda_2018 import (
    HeresiMiranda2018, heresi_miranda_2018)
from openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009 import (
    JayaramBaker2009, jayaram_baker_2009)

__all__ = [
    'HeresiMiranda2018', 'JayaramBaker2009',
    'heresi_miranda_2018', 'jayaram_baker_2009']
