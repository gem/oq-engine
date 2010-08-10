from gflags import *

# arguments name definition
POPULATION_EXPOSURE = 'population-exposure'
COUNTRIES_EXPOSURE = 'countries-exposure'
FROM = 'from'
TO = 'to'
CELL_SIZE = 'cell-size'
FIXED_COV_IML = 'cov-iml'
FIXED_MEAN_IML = 'mean-iml'
LOSS_MAPS_PROBABILITY = 'lmap-probability'

DEFINE_string(POPULATION_EXPOSURE, None, 'Path of the ESRI binary file containing the population exposure [MANDATORY]')
DEFINE_string(COUNTRIES_EXPOSURE, None, 'Path of the ESRI binary file containing the countries exposure [MANDATORY]')

# TODO Ask review about the format
DEFINE_string(FROM, None, 'Upper left corner of the region, in this format longitude,latitude (for example --from=1.0,2.0) [MANDATORY]')
DEFINE_string(TO, None, 'Lower right corner of the region, in this format longitude,latitude (for example --from=1.0,2.0) [MANDATORY]')

DEFINE_float(CELL_SIZE, 0.00833333333333, 'Cell size of the region')
DEFINE_float(FIXED_COV_IML, 0.001, 'Fixed COV for hazard IML to use')
DEFINE_float(FIXED_MEAN_IML, 6.5, 'Fixed MEAN for hazard IML to use')
DEFINE_float(LOSS_MAPS_PROBABILITY, 0.1, 'Probability to use when computing the loss maps (LMAP)')

def check_mandatory_parameters():
    """Checks if the mandatory parameters have been specified from the command line."""
    
    if not FLAGS[POPULATION_EXPOSURE].present or not FLAGS[COUNTRIES_EXPOSURE].present or not FLAGS[FROM].present or not FLAGS[TO].present:
        raise FlagsError('You need to specify all the mandatory parameters.')
