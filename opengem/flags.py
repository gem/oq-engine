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
MEANS_IML = 'means-iml'
COMPUTATION_TYPE = 'comp-type'
HAZARD_CURVES = 'hazard-curves'

MANDATORY_PARAMETERS = (POPULATION_EXPOSURE, COUNTRIES_EXPOSURE, FROM, TO)

DEFINE_string(POPULATION_EXPOSURE, None, 'Path of the ESRI binary file containing the population exposure [MANDATORY]')
DEFINE_string(COUNTRIES_EXPOSURE, None, 'Path of the ESRI binary file containing the countries exposure [MANDATORY]')

# TODO Ask review about the format
DEFINE_string(FROM, None, 'Upper left corner of the region, in this format longitude,latitude (for example --from=1.0,2.0) [MANDATORY]')
DEFINE_string(TO, None, 'Lower right corner of the region, in this format longitude,latitude (for example --to=1.0,2.0) [MANDATORY]')

DEFINE_float(CELL_SIZE, 0.00833333333333, 'Cell size of the region')
DEFINE_float(FIXED_COV_IML, 0.001, 'Fixed COV for hazard IML to use')
DEFINE_float(FIXED_MEAN_IML, 6.5, 'Fixed MEAN for hazard IML to use')
DEFINE_float(LOSS_MAPS_PROBABILITY, 0.1, 'Probability to use when computing the loss maps (LOSSMAP)')
DEFINE_string(MEANS_IML, None, 'Path of the hazard means iml file')
DEFINE_enum(COMPUTATION_TYPE, 'LOSSRATIO', ['LOSSRATIO' ,'LOSS', 'LOSSRATIOSTD', 'LOSSSTD', 'LOSSCURVE', 'MEANLOSS', 'LOSSMAP'], 'Computation type')
DEFINE_string(HAZARD_CURVES, None, 'Path of the hazard curves file')

def check_mandatory_parameters():
    """Checks if the mandatory parameters have been specified from the command line."""
    
    if not FLAGS[POPULATION_EXPOSURE].present or not FLAGS[COUNTRIES_EXPOSURE].present or not FLAGS[FROM].present or not FLAGS[TO].present:
        raise FlagsError('You need to specify all the mandatory parameters, ie. ' + str(MANDATORY_PARAMETERS))

def check_mandatory_parameters_for_probabilistic_scenario():
    """Checks the mandatory parameters if the probabilistic scenario is specified."""
    
    if FLAGS[COMPUTATION_TYPE].value in ('LOSSCURVE', 'MEANLOSS', 'LOSSMAP') and not FLAGS[HAZARD_CURVES].present:
        raise FlagsError('You need to specify the hazard curves file parameter when computing the probabilistic scenario.')