# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2017, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (openquake.hmtk) provided herein
# is released as a prototype implementation on behalf of
# scientists and engineers working within the GEM Foundation (Global
# Earthquake Model).
#
# It is distributed for the purpose of open collaboration and in the
# hope that it will be useful to the scientific, engineering, disaster
# risk and software design communities.
#
# The software is NOT distributed as part of GEM's OpenQuake suite
# (http://www.globalquakemodel.org/openquake) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
:class:`openquake.hmtk.strain.shift.Shift` implements the Seismic Hazard
Inferred from Tectonics (SHIFT) methodology (Bird & Liu, 2007;
Bird et al. 2010) for calculating seismic moment rate from Geodetic Strain
'''

import numpy as np
from math import fabs
import yaml
from openquake.hmtk.strain.strain_utils import (
    moment_function, calculate_taper_function)


RADIAN_CONV = np.pi / 180.
SECS_PER_YEAR = 365.25 * 24. * 60. * 60.
EARTH_RADIUS = 6371000.0

CRB_PARAMS = {'CMT_EVENTS': 285.9, 'CMT_moment': 1.13E17,
              'beta': 0.65, 'corner_mag': 7.64, 'tGR_moment_rate': 1.67E12,
              'length': 18126., 'velocity': 18.95, 'assumed_dip': 55.,
              'assumed_mu': 27.7, 'line_integral': 5.5E8,
              'coupled_thickness': 3.0, 'lithosphere': 6.,
              'coupling': 0.50, 'adjustment_factor': 1.001, 'area': None}

CTF_PARAMS = {'CMT_EVENTS': 198.5, 'CMT_moment': 3.5E17,
              'beta': 0.65, 'corner_mag': 8.01, 'tGR_moment_rate': 3.8E12,
              'length': 19375., 'velocity': 21.54, 'assumed_dip': 73.,
              'assumed_mu': 27.7, 'line_integral': 4.4E8,
              'coupled_thickness': 8.6, 'lithosphere': 12.,
              'coupling': 0.72, 'adjustment_factor': 1.001, 'area': None}

CCB_PARAMS = {'CMT_EVENTS': 259.4, 'CMT_moment': 3.5E17,
              'beta': 0.62, 'corner_mag': 8.46, 'tGR_moment_rate': 1.06E13,
              'length': 12516., 'velocity': 18.16, 'assumed_dip': 20.,
              'assumed_mu': 27.7, 'line_integral': 6.0E8,
              'coupled_thickness': 18., 'lithosphere': 13.,
              'coupling': 1.0, 'adjustment_factor': 1.001, 'area': None}

OSRnor_PARAMS = {'CMT_EVENTS': 424.3, 'CMT_moment': 1.13E17,
                 'beta': 0.92, 'corner_mag': 5.86, 'tGR_moment_rate': 6.7E11,
                 'length': 61807., 'velocity': 46.40, 'assumed_dip': 55.,
                 'assumed_mu': 25.7, 'line_integral': 5.0E9,
                 'coupled_thickness': 0.13, 'lithosphere': 8.,
                 'coupling': 0.01, 'adjustment_factor': 1.619, 'area': None}

OSRoth_PARAMS = {'CMT_EVENTS': 77.0, 'CMT_moment': 1.13E17,
                 'beta': 0.82, 'corner_mag': 7.39, 'tGR_moment_rate': 1.9E11,
                 'length': 61807., 'velocity': 7.58, 'assumed_dip': 55.,
                 'assumed_mu': 25.7, 'line_integral': 4.7E8,
                 'coupled_thickness': 0.40, 'lithosphere': 8.,
                 'coupling': 0.05, 'adjustment_factor': 1.619, 'area': None}

OTFslo_PARAMS = {'CMT_EVENTS': 398.0, 'CMT_moment': 2.0E17,
                 'beta': 0.64, 'corner_mag': 8.14, 'tGR_moment_rate': 6.7E12,
                 'length': 27220., 'velocity': 20.68, 'assumed_dip': 73.,
                 'assumed_mu': 25.7, 'line_integral': 5.2E8,
                 'coupled_thickness': 13., 'lithosphere': 14.,
                 'coupling': 0.93, 'adjustment_factor': 1.619, 'area': None}

OTFmed_PARAMS = {'CMT_EVENTS': 406.9, 'CMT_moment': 2.0E17,
                 'beta': 0.65, 'corner_mag': 6.55, 'tGR_moment_rate': 9.4E11,
                 'length': 10351., 'velocity': 57.53, 'assumed_dip': 73.,
                 'assumed_mu': 25.7, 'line_integral': 5.3E8,
                 'coupled_thickness': 1.8, 'lithosphere': 14.,
                 'coupling': 0.13, 'adjustment_factor': 1.619, 'area': None}

OTFfas_PARAMS = {'CMT_EVENTS': 376.6, 'CMT_moment': 2.0E17,
                 'beta': 0.73, 'corner_mag': 6.63, 'tGR_moment_rate': 9.0E11,
                 'length': 6331., 'velocity': 97.11, 'assumed_dip': 73.,
                 'assumed_mu': 25.7, 'line_integral': 5.5E8,
                 'coupled_thickness': 1.6, 'lithosphere': 14.,
                 'coupling': 0.11, 'adjustment_factor': 1.619, 'area': None}

OCB_PARAMS = {'CMT_EVENTS': 117.7, 'CMT_moment': 3.5E17,
              'beta': 0.53, 'corner_mag': 8.04, 'tGR_moment_rate': 4.6E12,
              'length': 13236., 'velocity': 19.22, 'assumed_dip': 20.,
              'assumed_mu': 49., 'line_integral': 1.2E9,
              'coupled_thickness': 3.8, 'lithosphere': 14.,
              'coupling': 0.27, 'adjustment_factor': 2.000, 'area': None}

SUB_PARAMS = {'CMT_EVENTS': 2052.8, 'CMT_moment': 3.5E17,
              'beta': 0.64, 'corner_mag': 9.58, 'tGR_moment_rate': 2.85E14,
              'length': 38990., 'velocity': 61.48, 'assumed_dip': 14.,
              'assumed_mu': 49., 'line_integral': 1.58E10,
              'coupled_thickness': 18., 'lithosphere': 26.,
              'coupling': 0.69, 'adjustment_factor': 3.434, 'area': None}

IPL_PARAMS = {'CMT_EVENTS': 189.0, 'CMT_moment': 3.47E17,
              'beta': 0.63, 'corner_mag': 9.0, 'tGR_moment_rate': None,
              'length': None, 'velocity': None, 'area': 4.3536E14,
              'assumed_dip': 14., 'assumed_mu': None, 'line_integral': None,
              'coupled_thickness': None, 'lithosphere': None, 'coupling': None,
              'adjustment_factor': 1.619,
              'CMT_duration': 32.25 * SECS_PER_YEAR}

BIRD_GLOBAL_PARAMETERS = {'CRB': CRB_PARAMS,
                          'CTF': CTF_PARAMS,
                          'CCB': CCB_PARAMS,
                          'OSRnor': OSRnor_PARAMS,
                          'OSRoth': OSRoth_PARAMS,
                          'OTFslo': OTFslo_PARAMS,
                          'OTFmed': OTFmed_PARAMS,
                          'OTFfas': OTFfas_PARAMS,
                          'OCB': OCB_PARAMS,
                          'SUB': SUB_PARAMS,
                          'IPL': IPL_PARAMS}

# This value of 25.7474 is taken from Bird's analysis -

# TODO this needs to be generalised if integrating w/Modeller
CMT_DURATION_S = 25.7474 * SECS_PER_YEAR


# Apply SI conversion adjustments from Bird (2007)'s code
# TODO This is ugly - reconsider this (maybe require only inputs in SI)
for reg_type in BIRD_GLOBAL_PARAMETERS:
    reg = BIRD_GLOBAL_PARAMETERS[reg_type]

    reg['corner_moment'] = moment_function(reg['corner_mag'])
    if reg_type is not 'IPL':
        reg['CMT_pure_event_rate'] = reg['CMT_EVENTS'] / CMT_DURATION_S
        reg['length'] = 1000.0 * reg['length']
        reg['velocity'] = (reg['velocity'] * 0.001) / SECS_PER_YEAR
        reg['assumed_dip'] = reg['assumed_dip'] * RADIAN_CONV
        reg['assumed_mu'] = reg['assumed_mu'] * 1.0E9
        reg['coupled_thickness'] = reg['coupled_thickness'] * 1000.
        reg['lithosphere'] = reg['lithosphere'] * 1000.
    else:
        reg['CMT_pure_event_rate'] = reg['CMT_EVENTS'] / reg['CMT_duration']
    BIRD_GLOBAL_PARAMETERS[reg_type] = reg


STRAIN_VARIABLES = ['exx', 'eyy', 'exy', 'e1h', 'e2h', 'err', '2nd_inv',
                    'dilatation']


class Shift(object):
    '''
    :class:`openquake.hmtk.strain.shift.Shift` implements the main Seismic
    Hazard Inferred from Tectonics (SHIFT) methodology for calculating
    activity rates (Bird & Liu, 2007; Bird et al. 2010)

    :param strain:
        Strain model as instance of :class:
        openquake.hmtk.strain.geodetic_strain.GeodeticStrain

    :param float/list/array target_magnitudes:
        Magnitude of list of target magnitudes for calculation of the activity
        rates

    :param int number_magnitudes:
        Number of magnitudes considered for activity rates

    :param np.array threshold_moment:
        The scalar moment corresponding to the threshold magnitudes

    :param list regionalisation:
        List of dictionaries containing the required region-specific attributes
        required for calculation

    :param np.ndarray base_rates:
        Minimum (background) rates for each corresponding target magnitude
    '''
    def __init__(self, minimum_magnitude, base_params=None,
                 region_parameter_file=None):
        '''
        Instantiate the class, retreive minimum moments, base rates and
        regionalisation informaton

        :param float/list/np.ndarray minimum_magnitude:
            Target magnitudes for calculating the activity rates

        :param dict base_params:
            Regionalisation parameters for the background region type (in this
            case the Bird et al. Intraplate class

        :param str region_parameter_file:
            To overwrite the default Bird et al (2007) classifcations the
            regionalisation can be defined in a separate Yaml file
        '''
        base_params = base_params or IPL_PARAMS
        self.strain = None
        if isinstance(minimum_magnitude, float):
            self.target_magnitudes = np.array([minimum_magnitude], dtype=float)
        elif isinstance(minimum_magnitude, list):
            self.target_magnitudes = np.array(minimum_magnitude, dtype=float)
        elif isinstance(minimum_magnitude, np.ndarray):
            self.target_magnitudes = minimum_magnitude
        else:
            raise ValueError('Minimum magnitudes must be float, list or array')

        self.number_magnitudes = len(self.target_magnitudes)
        self.threshold_moment = moment_function(self.target_magnitudes)
        # Get the base rate from the input parameters
        self.base_rate = self._get_base_rates(base_params)
        # If a regionalisation parameter file is defined then read
        # regionalisation from there - otherwise use Bird regionalisation
        if region_parameter_file:
            self.regionalisation = yaml.load(open(region_parameter_file, 'rt'))
        else:
            self.regionalisation = BIRD_GLOBAL_PARAMETERS

    def _get_base_rates(self, base_params):
        '''
        Defines the base moment rate that should be assigned to places of
        zero strain (i.e. Intraplate regions). In Bird et al (2010) this is
        taken as basic rate of Intraplate events in GCMT catalogue above the
        threshold magnitude

        :param dict base_params:
            Parameters needed for calculating the base rate. Requires:
                'CMT_EVENTS': The number of CMT events
                'area': Total area (km ^ 2) of the region class
                'CMT_duration': Duration of reference catalogue
                'CMT_moment': Moment rate from CMT catalogue
                'corner_mag': Corner magnitude of Tapered G-R for region
                'beta': Beta value of tapered G-R for distribution
        '''
        base_ipl_rate = base_params['CMT_EVENTS'] / (
            base_params['area'] * base_params['CMT_duration'])
        base_rate = np.zeros(self.number_magnitudes, dtype=float)

        for iloc in range(0, self.number_magnitudes):
            base_rate[iloc] = base_ipl_rate * calculate_taper_function(
                base_params['CMT_moment'],
                self.threshold_moment[iloc],
                moment_function(base_params['corner_mag']),
                base_params['beta'])
        return base_rate

    def calculate_activity_rate(self, strain_data, cumulative=False,
                                in_seconds=False):
        '''
        Main function to calculate the activity rate (for each of the
        magnitudes in target_magnitudes) for all of the cells specified in
        the input strain model file

        :param strain_data:
            Strain model as an instance of :class:
            openquake.hmtk.strain.geodetic_strain.GeodeticStrain

        :param bool cumulative:
            Set to true if the cumulative rate is required, False for
            incremental

        :param bool in_seconds:
            Returns the activity rate in seconds (True) or else as an annual
            activity rate
        '''
        self.strain = strain_data
        self.strain.target_magnitudes = self.target_magnitudes
        # Adjust strain rates from annual to seconds (SI)
        for key in STRAIN_VARIABLES:
            self.strain.data[key] = self.strain.data[key] / SECS_PER_YEAR

        if 'region' not in self.strain.data:
            raise ValueError('Cannot implment  SHIFT methodology without '
                             'definition of regionalisation')
        else:
            self._reclassify_Bird_regions_with_data()

        # Initially all seismicity rates assigned to background rate
        self.strain.seismicity_rate = np.tile(
            self.base_rate,
            [self.strain.get_number_observations(), 1])

        regionalisation_zones = (
            np.unique(self.strain.data['region'])).tolist()

        for region in regionalisation_zones:
            id0 = self.strain.data['region'] == region
            if b'IPL' in region:
                # For intra-plate seismicity everything is refered to
                # the background rate
                continue

            elif b'OSR_special_1' in region:
                # Special case 1 - normal and transform faulting
                calculated_rate = self.get_rate_osr_normal_transform(
                    self.threshold_moment, id0)

            elif b'OSR_special_2' in region:
                # Special case 2 - convergent and transform faulting
                calculated_rate = self.get_rate_osr_convergent_transform(
                    self.threshold_moment, id0)
            else:
                region = region.decode('utf-8')
                calculated_rate = \
                    self.regionalisation[region]['adjustment_factor'] * \
                    self.continuum_seismicity(self.threshold_moment,
                                              self.strain.data['e1h'][id0],
                                              self.strain.data['e2h'][id0],
                                              self.strain.data['err'][id0],
                                              self.regionalisation[region])

            for jloc, iloc in enumerate(np.where(id0)[0]):
                # Where the calculated rate exceeds the base rate then becomes
                # calculated rate. In this version the magnitudes are treated
                # independently (i.e. if Rate(M < 7) > Base Rate (M < 7) but
                # Rate (M > 7) < Base Rate (M > 7) then returned Rate (M < 7)
                # = Rate (M < 7) and returned Rate (M > 7) = Base Rate (M > 7)
                id1 = calculated_rate[jloc] > self.base_rate
                self.strain.seismicity_rate[iloc, id1] = calculated_rate[jloc,
                                                                         id1]

        if not cumulative and self.number_magnitudes > 1:
            # Seismicity rates are currently cumulative - need to turn them
            # into discrete
            for iloc in range(0, self.number_magnitudes - 1):
                self.strain.seismicity_rate[:, iloc] = \
                    self.strain.seismicity_rate[:, iloc] -\
                    self.strain.seismicity_rate[:, iloc + 1]

        if not in_seconds:
            self.strain.seismicity_rate = self.strain.seismicity_rate * \
                SECS_PER_YEAR

            for key in STRAIN_VARIABLES:
                self.strain.data[key] = self.strain.data[key] * SECS_PER_YEAR

    def get_rate_osr_normal_transform(self, threshold_moment, id0):
        '''
        Gets seismicity rate for special case of the ridge condition with
        spreading and transform component

        :param float threshold_moment:
            Moment required for calculating activity rate

        :param np.ndarray id0:
            Logical vector indicating the cells to which this condition applies

        :returns:
            Activity rates for cells corresponding to the hybrid ocean
            spreading ridge and oceanic transform condition

        '''
        # Get normal component
        e1h_ridge = np.zeros(np.sum(id0), dtype=float)
        e2h_ridge = self.strain.data['e1h'][id0] + self.strain.data['e2h'][id0]
        err_ridge = -(e1h_ridge + e2h_ridge)

        calculated_rate_ridge = self.continuum_seismicity(
            threshold_moment,
            e1h_ridge,
            e2h_ridge,
            err_ridge,
            self.regionalisation['OSRnor'])

        # Get transform
        e1h_trans = self.strain.data['e1h'][id0]
        e2h_trans = -e1h_trans
        err_trans = np.zeros(np.sum(id0), dtype=float)

        calculated_rate_transform = self.continuum_seismicity(
            threshold_moment,
            e1h_trans,
            e2h_trans,
            err_trans,
            self.regionalisation['OTFmed'])

        return (
            self.regionalisation['OSRnor']['adjustment_factor'] *
            (calculated_rate_ridge + calculated_rate_transform))

    def get_rate_osr_convergent_transform(self, threshold_moment, id0):
        '''
        Calculates seismicity rate for special case of the ridge condition
        with convergence and transform

        :param float threshold_moment:
            Moment required for calculating activity rate

        :param np.ndarray id0:
            Logical vector indicating the cells to which this condition applies

        :returns:
            Activity rates for cells corresponding to the hybrid ocean
            convergent boundary and oceanic transform condition
        '''
        # Get convergent component
        e1h_ocb = self.strain.data['e1h'][id0] + self.strain.data['e2h'][id0]
        e2h_ocb = np.zeros(np.sum(id0), dtype=float)
        err_ocb = -(e1h_ocb + e2h_ocb)

        calculated_rate_ocb = self.continuum_seismicity(
            threshold_moment,
            e1h_ocb,
            e2h_ocb,
            err_ocb,
            self.regionalisation['OCB'])

        # Get transform
        e2h_trans = self.strain.data['e2h'][id0]
        e1h_trans = -e2h_trans
        err_trans = np.zeros(np.sum(id0), dtype=float)

        calculated_rate_transform = self.continuum_seismicity(
            threshold_moment,
            e1h_trans,
            e2h_trans,
            err_trans,
            self.regionalisation['OTFmed'])

        return (self.regionalisation['OSRnor']['adjustment_factor'] *
                (calculated_rate_ocb + calculated_rate_transform))

    def continuum_seismicity(self, threshold_moment, e1h, e2h, err,
                             region_params):
        '''
        Function to implement the continuum seismicity calculation given
        vectors of input rates e1h, e2h [np.ndarray] and a dictionary of
        the corresponding regionalisation params
        returns a vector of the corresponding seismicity rates
        Python implementation of the CONTINUUM_SEISMICITY subroutine of
        SHIFT_GSRM.f90

        :param float threshold_moment:
            Target moment for calculation of activity rate

        :param np.ndarray e1h:
            First principal strain rate

        :param np.ndarray e1h:
            Second principal strain rate

        :param np.ndarray err:
            Vertical strain rate

        :param dict region_params:
            Activity rate parameters specific to the tectonic region under
            consideration

        :returns:
            Cumulative seismicity rate greater than or equal to the
            threshold magnitude
        '''

        strain_values = np.column_stack([e1h, e2h, err])
        e1_rate = np.amin(strain_values, axis=1)
        e3_rate = np.amax(strain_values, axis=1)
        e2_rate = 0. - e1_rate - e3_rate
        # Pre-allocate seismicity rate with zeros
        seismicity_rate = np.zeros(
            [np.shape(strain_values)[0], len(threshold_moment)],
            dtype=float)
        # Calculate moment rate per unit area
        temp_e_rate = 2.0 * (-e1_rate)
        id0 = np.where(e2_rate < 0.0)[0]
        temp_e_rate[id0] = 2.0 * e3_rate[id0]
        M_persec_per_m2 = (
            region_params['assumed_mu'] * temp_e_rate *
            region_params['coupled_thickness'])

        # Calculate seismicity rate at the threshold moment of the CMT
        # catalogue - Eq 6 in Bird et al (2010)
        seismicity_at_cmt_threshold = region_params['CMT_pure_event_rate'] * \
            (M_persec_per_m2 / region_params['tGR_moment_rate'])
        # Adjust forecast rate to desired rate using tapered G-R model
        # Taken from Eq 7 (Bird et al. 2010) and Eq 9 (Bird & Kagan, 2004)
        for iloc, moment_thresh in enumerate(threshold_moment):
            g_function = calculate_taper_function(
                region_params['CMT_moment'],
                moment_thresh,
                region_params['corner_moment'],
                region_params['beta'])
            seismicity_rate[:, iloc] = g_function * seismicity_at_cmt_threshold
        return seismicity_rate

    def _reclassify_Bird_regions_with_data(self):
        '''
        The SHIFT regionalisation defines only 'C','R','S','O' - need to
        use strain data to reclassify to sub-categories according to the
        definition in Bird & Liu (2007)
        '''
        # Treat trivial cases of subduction zones and oceanic types
        self.strain.data['region'][
            self.strain.data['region'] == b'IPL'] = ['IPL']
        self.strain.data['region'][
            self.strain.data['region'] == b'S'] = ['SUB']
        self.strain.data['region'][
            self.strain.data['region'] == b'O'] = ['OCB']

        # Continental types
        id0 = self.strain.data['region'] == b'C'
        self.strain.data['region'][id0] = ['CTF']
        id0_pos_err = np.logical_and(
            self.strain.data['err'] > 0.,
            self.strain.data['err'] > (0.364 * self.strain.data['e2h']))

        id0_neg_err = np.logical_and(
            self.strain.data['err'] < 0.,
            self.strain.data['err'] <= (0.364 * self.strain.data['e1h']))

        self.strain.data['region'][np.logical_and(id0, id0_pos_err)] = 'CCB'
        self.strain.data['region'][np.logical_and(id0, id0_neg_err)] = 'CRB'

        # Ridge Types
        id0 = self.strain.data['region'] == b'R'
        for iloc in np.where(id0)[0]:
            cond = (self.strain.data['e1h'][iloc] > 0.0 and
                    self.strain.data['e2h'][iloc] > 0.0)
            if cond:
                self.strain.data['region'][iloc] = 'OSRnor'
            # Effective == 0.0
            elif fabs(self.strain.data['e1h'][iloc]) < 1E-99:
                self.strain.data['region'][iloc] = 'OSRnor'
            elif ((self.strain.data['e1h'][iloc] *
                   self.strain.data['e2h'][iloc]) < 0.0) and\
                 ((self.strain.data['e1h'][iloc] +
                   self.strain.data['e2h'][iloc]) >= 0.):
                self.strain.data['region'][iloc] = 'OSR_special_1'
            elif ((self.strain.data['e1h'][iloc] *
                   self.strain.data['e2h'][iloc]) < 0.) and\
                 ((self.strain.data['e1h'][iloc] +
                   self.strain.data['e2h'][iloc]) < 0.):
                self.strain.data['region'][iloc] = 'OSR_special_2'
            else:
                self.strain.data['region'][iloc] = 'OCB'
