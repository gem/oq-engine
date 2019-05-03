# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import functools
import multiprocessing
import numpy

from openquake.baselib.general import DictArray
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import correlation, stats, calc
from openquake.hazardlib import valid, InvalidFile
from openquake.commonlib import logictree, util
from openquake.risklib.riskmodels import get_risk_files

GROUND_MOTION_CORRELATION_MODELS = ['JB2009', 'HM2018']
TWO16 = 2 ** 16  # 65536
TWO32 = 2 ** 32
U16 = numpy.uint16
U32 = numpy.uint32
U64 = numpy.uint64
F32 = numpy.float32
F64 = numpy.float64


class OqParam(valid.ParamSet):
    siteparam = dict(
        vs30measured='reference_vs30_type',
        vs30='reference_vs30_value',
        z1pt0='reference_depth_to_1pt0km_per_sec',
        z2pt5='reference_depth_to_2pt5km_per_sec',
        siteclass='reference_siteclass',
        backarc='reference_backarc')
    aggregate_by = valid.Param(valid.namelist, [])
    asset_loss_table = valid.Param(valid.boolean, False)
    area_source_discretization = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    asset_correlation = valid.Param(valid.NoneOr(valid.FloatRange(0, 1)), 0)
    asset_life_expectancy = valid.Param(valid.positivefloat)
    assets_per_site_limit = valid.Param(valid.positivefloat, 1000)
    avg_losses = valid.Param(valid.boolean, True)
    base_path = valid.Param(valid.utf8, '.')
    calculation_mode = valid.Param(valid.Choice(), '')  # -> get_oqparam
    coordinate_bin_width = valid.Param(valid.positivefloat)
    compare_with_classical = valid.Param(valid.boolean, False)
    concurrent_tasks = valid.Param(
        valid.positiveint, multiprocessing.cpu_count() * 3)  # by M. Simionato
    conditional_loss_poes = valid.Param(valid.probabilities, [])
    continuous_fragility_discretization = valid.Param(valid.positiveint, 20)
    cross_correlation = valid.Param(valid.Choice('yes', 'no', 'full'), 'yes')
    description = valid.Param(valid.utf8_not_empty)
    disagg_by_src = valid.Param(valid.boolean, False)
    disagg_outputs = valid.Param(valid.disagg_outputs, None)
    discard_assets = valid.Param(valid.boolean, False)
    distance_bin_width = valid.Param(valid.positivefloat)
    mag_bin_width = valid.Param(valid.positivefloat)
    ebrisk_maxweight = valid.Param(valid.positivefloat, 5E10)
    export_dir = valid.Param(valid.utf8, '.')
    export_multi_curves = valid.Param(valid.boolean, False)
    exports = valid.Param(valid.export_formats, ())
    filter_distance = valid.Param(valid.Choice('rjb', 'rrup'), None)
    ground_motion_correlation_model = valid.Param(
        valid.NoneOr(valid.Choice(*GROUND_MOTION_CORRELATION_MODELS)), None)
    ground_motion_correlation_params = valid.Param(valid.dictionary)
    ground_motion_fields = valid.Param(valid.boolean, True)
    gsim = valid.Param(valid.utf8, '[FromFile]')
    hazard_calculation_id = valid.Param(valid.NoneOr(valid.positiveint), None)
    hazard_curves_from_gmfs = valid.Param(valid.boolean, False)
    hazard_output_id = valid.Param(valid.NoneOr(valid.positiveint))
    hazard_maps = valid.Param(valid.boolean, False)
    hypocenter = valid.Param(valid.point3d)
    ignore_missing_costs = valid.Param(valid.namelist, [])
    ignore_covs = valid.Param(valid.boolean, False)
    iml_disagg = valid.Param(valid.floatdict, {})  # IMT -> IML
    individual_curves = valid.Param(valid.boolean, False)
    inputs = valid.Param(dict, {})
    # insured_losses = valid.Param(valid.boolean, False)
    multi_peril = valid.Param(valid.namelist, [])
    ash_wet_amplification_factor = valid.Param(valid.positivefloat, 1.0)
    intensity_measure_types = valid.Param(valid.intensity_measure_types, None)
    intensity_measure_types_and_levels = valid.Param(
        valid.intensity_measure_types_and_levels, None)
    interest_rate = valid.Param(valid.positivefloat)
    investigation_time = valid.Param(valid.positivefloat, None)
    lrem_steps_per_interval = valid.Param(valid.positiveint, 0)
    steps_per_interval = valid.Param(valid.positiveint, 1)
    master_seed = valid.Param(valid.positiveint, 0)
    maximum_distance = valid.Param(valid.maximum_distance)  # km
    asset_hazard_distance = valid.Param(valid.floatdict, {'default': 15})  # km
    max_hazard_curves = valid.Param(valid.boolean, False)
    max_potential_paths = valid.Param(valid.positiveint, 100)
    mean_hazard_curves = mean = valid.Param(valid.boolean, True)
    std_hazard_curves = valid.Param(valid.boolean, False)
    minimum_intensity = valid.Param(valid.floatdict, {})  # IMT -> minIML
    minimum_magnitude = valid.Param(valid.floatdict, {'default': 0})
    modal_damage_state = valid.Param(valid.boolean, False)
    number_of_ground_motion_fields = valid.Param(valid.positiveint)
    number_of_logic_tree_samples = valid.Param(valid.positiveint, 0)
    num_epsilon_bins = valid.Param(valid.positiveint)
    poes = valid.Param(valid.probabilities, [])
    poes_disagg = valid.Param(valid.probabilities, [])
    quantile_hazard_curves = quantiles = valid.Param(valid.probabilities, [])
    random_seed = valid.Param(valid.positiveint, 42)
    reference_depth_to_1pt0km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_depth_to_2pt5km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_vs30_type = valid.Param(
        valid.Choice('measured', 'inferred'), 'measured')
    reference_vs30_value = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_siteclass = valid.Param(valid.Choice('A', 'B', 'C', 'D'), 'D')
    reference_backarc = valid.Param(valid.boolean, False)
    region = valid.Param(valid.wkt_polygon, None)
    region_grid_spacing = valid.Param(valid.positivefloat, None)
    optimize_same_id_sources = valid.Param(valid.boolean, False)
    risk_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    risk_investigation_time = valid.Param(valid.positivefloat, None)
    rupture_mesh_spacing = valid.Param(valid.positivefloat)
    complex_fault_mesh_spacing = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    return_periods = valid.Param(valid.positiveints, None)
    ruptures_per_block = valid.Param(valid.positiveint, 50000)
    ses_per_logic_tree_path = valid.Param(
        valid.compose(valid.nonzero, valid.positiveint), 1)
    ses_seed = valid.Param(valid.positiveint, 42)
    shakemap_id = valid.Param(valid.nice_string, None)
    site_effects = valid.Param(valid.boolean, True)  # shakemap amplification
    sites = valid.Param(valid.NoneOr(valid.coordinates), None)
    sites_disagg = valid.Param(valid.NoneOr(valid.coordinates), [])
    sites_slice = valid.Param(valid.simple_slice, (None, None))
    sm_lt_path = valid.Param(valid.logic_tree_path, None)
    source_id = valid.Param(valid.source_id, None)
    spatial_correlation = valid.Param(valid.Choice('yes', 'no', 'full'), 'yes')
    specific_assets = valid.Param(valid.namelist, [])
    pointsource_distance = valid.Param(valid.maximum_distance, {})
    taxonomies_from_model = valid.Param(valid.boolean, False)
    time_event = valid.Param(str, None)
    truncation_level = valid.Param(valid.NoneOr(valid.positivefloat), None)
    uniform_hazard_spectra = valid.Param(valid.boolean, False)
    width_of_mfd_bin = valid.Param(valid.positivefloat, None)

    @property
    def risk_files(self):
        try:
            return self._risk_files
        except AttributeError:
            self._risk_files = get_risk_files(self.inputs)
            return self._risk_files

    @property
    def input_dir(self):
        """
        :returns: absolute path to where the job.ini is
        """
        return os.path.abspath(os.path.dirname(self.inputs['job_ini']))

    def get_reqv(self):
        """
        :returns: an instance of class:`RjbEquivalent` if reqv_hdf5 is set
        """
        if 'reqv' not in self.inputs:
            return
        return {key: valid.RjbEquivalent(value)
                for key, value in self.inputs['reqv'].items()}

    def __init__(self, **names_vals):
        for name in list(names_vals):
            if name == 'quantile_hazard_curves':
                names_vals['quantiles'] = names_vals.pop(name)
        super().__init__(**names_vals)
        job_ini = self.inputs['job_ini']
        if 'calculation_mode' not in names_vals:
            raise InvalidFile('Missing calculation_mode in %s' % job_ini)
        if 'region_constraint' in names_vals:
            if 'region' in names_vals:
                raise InvalidFile('You cannot have both region and '
                                  'region_constraint in %s' % job_ini)
            logging.warning(
                'region_constraint is obsolete, use region instead')
            self.region = valid.wkt_polygon(
                names_vals.pop('region_constraint'))
        self.risk_investigation_time = (
            self.risk_investigation_time or self.investigation_time)
        if ('intensity_measure_types_and_levels' in names_vals and
                'intensity_measure_types' in names_vals):
            logging.warning('Ignoring intensity_measure_types since '
                            'intensity_measure_types_and_levels is set')
        if 'iml_disagg' in names_vals:
            self.iml_disagg.pop('default')
            # normalize things like SA(0.10) -> SA(0.1)
            self.iml_disagg = {str(from_string(imt)): val
                               for imt, val in self.iml_disagg.items()}
            self.hazard_imtls = self.iml_disagg
            if 'intensity_measure_types_and_levels' in names_vals:
                raise InvalidFile(
                    'Please remove the intensity_measure_types_and_levels '
                    'from %s: they will be inferred from the iml_disagg '
                    'dictionary' % job_ini)
        elif 'intensity_measure_types_and_levels' in names_vals:
            self.hazard_imtls = self.intensity_measure_types_and_levels
            delattr(self, 'intensity_measure_types_and_levels')
        elif 'intensity_measure_types' in names_vals:
            self.hazard_imtls = dict.fromkeys(self.intensity_measure_types)
            delattr(self, 'intensity_measure_types')
        self._risk_files = get_risk_files(self.inputs)

        self.check_source_model()
        if (self.hazard_calculation_id and
                self.calculation_mode == 'ucerf_risk'):
            raise ValueError('You cannot use the --hc option with ucerf_risk')
        if self.hazard_precomputed() and self.job_type == 'risk':
            self.check_missing('site_model', 'debug')
            self.check_missing('gsim_logic_tree', 'debug')
            self.check_missing('source_model_logic_tree', 'debug')

        # check the gsim_logic_tree
        if self.inputs.get('gsim_logic_tree'):
            if self.gsim != '[FromFile]':
                raise InvalidFile('%s: if `gsim_logic_tree_file` is set, there'
                                  ' must be no `gsim` key' % job_ini)
            path = os.path.join(
                self.base_path, self.inputs['gsim_logic_tree'])
            gsim_lt = logictree.GsimLogicTree(path, ['*'])

            # check the number of branchsets
            branchsets = len(gsim_lt._ltnode)
            if 'scenario' in self.calculation_mode and branchsets > 1:
                raise InvalidFile(
                    '%s: %s for a scenario calculation must contain a single '
                    'branchset, found %d!' % (job_ini, path, branchsets))

            # check the IMTs vs the GSIMs
            self._gsims_by_trt = gsim_lt.values
            for gsims in self._gsims_by_trt.values():
                self.check_gsims(gsims)
        elif self.gsim is not None:
            self.check_gsims([valid.gsim(self.gsim)])

        # checks for disaggregation
        if self.calculation_mode == 'disaggregation':
            if not self.poes_disagg and not self.iml_disagg:
                raise InvalidFile('poes_disagg or iml_disagg must be set '
                                  'in %(job_ini)s' % self.inputs)
            elif self.poes_disagg and self.iml_disagg:
                raise InvalidFile(
                    '%s: iml_disagg and poes_disagg cannot be set '
                    'at the same time' % job_ini)
            for k in ('mag_bin_width', 'distance_bin_width',
                      'coordinate_bin_width', 'num_epsilon_bins'):
                if k not in vars(self):
                    raise InvalidFile('%s must be set in %s' % (k, job_ini))

        # checks for classical_damage
        if self.calculation_mode == 'classical_damage':
            if self.conditional_loss_poes:
                raise InvalidFile(
                    '%s: conditional_loss_poes are not defined '
                    'for classical_damage calculations' % job_ini)

        # checks for event_based_risk
        if (self.calculation_mode == 'event_based_risk' and
                self.asset_correlation not in (0, 1)):
            raise ValueError('asset_correlation != {0, 1} is no longer'
                             ' supported')

        # checks for ebrisk
        if self.calculation_mode == 'ebrisk':
            pass
            # elif self.number_of_logic_tree_samples == 0:
            #    logging.warning('ebrisk is not meant for full enumeration')

        # check for GMFs from file
        if (self.inputs.get('gmfs', '').endswith('.csv') and not self.sites and
                'sites' not in self.inputs):
            raise InvalidFile('%s: You forgot sites|sites_csv' % job_ini)
        elif (self.inputs.get('gmfs', '').endswith('.xml') and
                'sites' in self.inputs):
            raise InvalidFile('%s: You cannot have both sites_csv and '
                              'gmfs_file' % job_ini)

        # checks for event_based
        if 'event_based' in self.calculation_mode:
            if self.ses_per_logic_tree_path >= TWO32:
                raise ValueError('ses_per_logic_tree_path too big: %d' %
                                 self.ses_per_logic_tree_path)
            if self.number_of_logic_tree_samples >= TWO16:
                raise ValueError('number_of_logic_tree_samples too big: %d' %
                                 self.number_of_logic_tree_samples)

        # check grid + sites
        if (self.region_grid_spacing and 'site_model' in self.inputs
                and 'exposure' in self.inputs):
            logging.warning(
                'You are specifying a grid, a site model and an exposure at '
                'the same time: consider using `oq prepare_site_model`')

    def check_gsims(self, gsims):
        """
        :param gsims: a sequence of GSIM instances
        """
        imts = set(from_string(imt).name for imt in self.imtls)
        for gsim in gsims:
            restrict_imts = gsim.DEFINED_FOR_INTENSITY_MEASURE_TYPES
            if restrict_imts:
                names = set(cls.__name__ for cls in restrict_imts)
                invalid_imts = ', '.join(imts - names)
                if invalid_imts:
                    raise ValueError(
                        'The IMT %s is not accepted by the GSIM %s' %
                        (invalid_imts, gsim))

            if 'site_model' not in self.inputs:
                # look at the required sites parameters: they must have
                # a valid value; the other parameters can keep a NaN
                # value since they are not used by the calculator
                for param in gsim.REQUIRES_SITES_PARAMETERS:
                    if param in ('lon', 'lat'):  # no check
                        continue
                    param_name = self.siteparam[param]
                    param_value = getattr(self, param_name)
                    if (isinstance(param_value, float) and
                            numpy.isnan(param_value)):
                        raise ValueError(
                            'Please set a value for %r, this is required by '
                            'the GSIM %s' % (param_name, gsim))

    @property
    def tses(self):
        """
        Return the total time as investigation_time * ses_per_logic_tree_path *
        (number_of_logic_tree_samples or 1)
        """
        return (self.investigation_time * self.ses_per_logic_tree_path *
                (self.number_of_logic_tree_samples or 1))

    @property
    def ses_ratio(self):
        """
        The ratio

        risk_investigation_time / investigation_time / ses_per_logic_tree_path
        """
        if self.investigation_time is None:
            raise ValueError('Missing investigation_time in the .ini file')
        return (self.risk_investigation_time or self.investigation_time) / (
            self.investigation_time * self.ses_per_logic_tree_path)

    @property
    def imtls(self):
        """
        Returns a DictArray with the risk intensity measure types and
        levels, if given, or the hazard ones.
        """
        imtls = getattr(self, 'hazard_imtls', None) or self.risk_imtls
        return DictArray(imtls)

    @property
    def all_cost_types(self):
        """
        Return the cost types of the computation (including `occupants`
        if it is there) in order.
        """
        # rt has the form 'vulnerability/structural', 'fragility/...', ...
        costtypes = sorted(rt.rsplit('/')[1] for rt in self.risk_files)
        if not costtypes and self.hazard_calculation_id:
            with util.read(self.hazard_calculation_id) as ds:
                parent = ds['oqparam']
            self._risk_files = get_risk_files(parent.inputs)
            costtypes = sorted(rt.rsplit('/')[1] for rt in self.risk_files)
        return costtypes

    @property
    def min_iml(self):
        """
        :returns: a numpy array of intensities, one per IMT
        """
        mini = self.minimum_intensity
        if mini:
            for imt in self.imtls:
                try:
                    mini[imt] = calc.filters.getdefault(mini, imt)
                except KeyError:
                    raise ValueError(
                        'The parameter `minimum_intensity` in the job.ini '
                        'file is missing the IMT %r' % imt)
        if 'default' in mini:
            del mini['default']
        return F32([mini.get(imt, 0) for imt in self.imtls])

    def set_risk_imtls(self, risk_models):
        """
        :param risk_models:
            a dictionary taxonomy -> loss_type -> risk_function

        Set the attribute risk_imtls.
        """
        # NB: different loss types may have different IMLs for the same IMT
        # in that case we merge the IMLs
        imtls = {}
        for taxonomy, risk_functions in risk_models.items():
            for risk_type, rf in risk_functions.items():
                imt = rf.imt
                from_string(imt)  # make sure it is a valid IMT
                imls = list(rf.imls)
                if imt in imtls and imtls[imt] != imls:
                    logging.debug(
                        'Different levels for IMT %s: got %s, expected %s',
                        imt, imls, imtls[imt])
                    imtls[imt] = sorted(set(imls + imtls[imt]))
                else:
                    imtls[imt] = imls
        self.risk_imtls = imtls
        if self.uniform_hazard_spectra:
            self.check_uniform_hazard_spectra()

    def hmap_dt(self):  # used for CSV export
        """
        :returns: a composite dtype (imt, poe)
        """
        return numpy.dtype([('%s-%s' % (imt, poe), F32)
                            for imt in self.imtls for poe in self.poes])

    def uhs_dt(self):  # used for CSV and NPZ export
        """
        :returns: a composity dtype (poe, imt)
        """
        imts_dt = numpy.dtype([(imt, F32) for imt in self.imtls
                               if imt.startswith(('PGA', 'SA'))])
        return numpy.dtype([(str(poe), imts_dt) for poe in self.poes])

    def imt_periods(self):
        """
        :returns: the IMTs with a period, as objects
        """
        imts = []
        for im in self.imtls:
            imt = from_string(im)
            if hasattr(imt, 'period'):
                imts.append(imt)
        return imts

    def imt_dt(self, dtype=F64):
        """
        :returns: a numpy dtype {imt: float}
        """
        return numpy.dtype([(imt, dtype) for imt in self.imtls])

    @property
    def lti(self):
        """
        Dictionary extended_loss_type -> extended_loss_type index
        """
        return {lt: i for i, (lt, dt) in enumerate(self.loss_dt_list())}

    def loss_dt(self, dtype=F32):
        """
        Return a composite dtype based on the loss types, including occupants
        """
        return numpy.dtype(self.loss_dt_list(dtype))

    def loss_dt_list(self, dtype=F32):
        """
        Return a data type list [(loss_name, dtype), ...]
        """
        loss_types = self.all_cost_types
        dts = [(str(lt), dtype) for lt in loss_types]
        return dts

    def loss_maps_dt(self, dtype=F32):
        """
        Return a composite data type for loss maps
        """
        ltypes = self.loss_dt(dtype).names
        lst = [('poe-%s' % poe, dtype) for poe in self.conditional_loss_poes]
        return numpy.dtype([(lt, lst) for lt in ltypes])

    def gmf_data_dt(self):
        """
        Return a composite data type for the GMFs
        """
        return numpy.dtype(
            [('rlzi', U16), ('sid', U32),
             ('eid', U64), ('gmv', (F32, (len(self.imtls),)))])

    def no_imls(self):
        """
        Return True if there are no intensity measure levels
        """
        return all(numpy.isnan(ls).any() for ls in self.imtls.values())

    @property
    def correl_model(self):
        """
        Return a correlation object. See :mod:`openquake.hazardlib.correlation`
        for more info.
        """
        correl_name = self.ground_motion_correlation_model
        if correl_name is None:  # no correlation model
            return
        correl_model_cls = getattr(
            correlation, '%sCorrelationModel' % correl_name)
        return correl_model_cls(**self.ground_motion_correlation_params)

    def get_kinds(self, kind, R):
        """
        Yield 'rlz-000', 'rlz-001', ...', 'mean', 'quantile-0.1', ...
        """
        stats = self.hazard_stats()
        if kind == 'stats':
            yield from stats
            return
        elif kind == 'rlzs':
            for r in range(R):
                yield 'rlz-%d' % r
            return
        elif kind:
            yield kind
            return
        # default: yield stats (and realizations if required)
        if R > 1 and self.individual_curves or not stats:
            for r in range(R):
                yield 'rlz-%03d' % r
        yield from stats

    def hazard_stats(self):
        """
        Return a list of item with the statistical functions defined for the
        hazard calculation
        """
        names = []  # name of statistical functions
        funcs = []  # statistical functions of kind func(values, weights)
        if self.mean_hazard_curves:
            names.append('mean')
            funcs.append(stats.mean_curve)
        if self.std_hazard_curves:
            names.append('std')
            funcs.append(stats.std_curve)
        for q in self.quantiles:
            names.append('quantile-%s' % q)
            funcs.append(functools.partial(stats.quantile_curve, q))
        if self.max_hazard_curves:
            names.append('max')
            funcs.append(stats.max_curve)
        return dict(zip(names, funcs))

    @property
    def job_type(self):
        """
        'hazard' or 'risk'
        """
        return 'risk' if ('risk' in self.calculation_mode or
                          'damage' in self.calculation_mode or
                          'bcr' in self.calculation_mode) else 'hazard'

    def is_event_based(self):
        """
        The calculation mode is event_based, event_based_risk or ebrisk
        """
        return self.calculation_mode in 'event_based_risk ebrisk'

    def is_valid_shakemap(self):
        """
        hazard_calculation_id must be set if shakemap_id is set
        """
        return self.hazard_calculation_id if self.shakemap_id else True

    def is_valid_truncation_level_disaggregation(self):
        """
        Truncation level must be set for disaggregation calculations
        """
        if self.calculation_mode == 'disaggregation':
            return self.truncation_level is not None
        else:
            return True

    def is_valid_geometry(self):
        """
        It is possible to infer the geometry only if exactly
        one of sites, sites_csv, hazard_curves_csv, gmfs_csv,
        region is set. You did set more than one, or nothing.
        """
        has_sites = (self.sites is not None or 'sites' in self.inputs
                     or 'site_model' in self.inputs)
        if not has_sites and not self.ground_motion_fields:
            # when generating only the ruptures you do not need the sites
            return True
        if ('gmfs' in self.inputs and not has_sites and
                not self.inputs['gmfs'].endswith('.xml')):
            raise ValueError('Missing sites or sites_csv in the .ini file')
        elif ('risk' in self.calculation_mode or
                'damage' in self.calculation_mode or
                'bcr' in self.calculation_mode):
            return True  # no check on the sites for risk
        flags = dict(
            sites=bool(self.sites),
            sites_csv=self.inputs.get('sites', 0),
            hazard_curves_csv=self.inputs.get('hazard_curves', 0),
            gmfs_csv=self.inputs.get('gmfs', 0),
            region=bool(self.region and self.region_grid_spacing))
        # NB: below we check that all the flags
        # are mutually exclusive
        return sum(bool(v) for v in flags.values()) == 1 or self.inputs.get(
            'exposure') or self.inputs.get('site_model')

    def is_valid_poes(self):
        """
        When computing hazard maps and/or uniform hazard spectra,
        the poes list must be non-empty.
        """
        if self.hazard_maps or self.uniform_hazard_spectra:
            return bool(self.poes)
        else:
            return True

    def is_valid_maximum_distance(self):
        """
        Invalid maximum_distance={maximum_distance}: {error}
        """
        if 'gsim_logic_tree' not in self.inputs:
            return True  # don't apply validation
        gsim_lt = self.inputs['gsim_logic_tree']
        trts = set(self.maximum_distance)
        unknown = ', '.join(trts - set(self._gsims_by_trt) - set(['default']))
        if unknown:
            self.error = ('setting the maximum_distance for %s which is '
                          'not in %s' % (unknown, gsim_lt))
            return False
        for trt, val in self.maximum_distance.items():
            if val <= 0:
                self.error = '%s=%r < 0' % (trt, val)
                return False
            elif trt not in self._gsims_by_trt and trt != 'default':
                self.error = 'tectonic region %r not in %s' % (trt, gsim_lt)
                return False
        if 'default' not in trts and trts < set(self._gsims_by_trt):
            missing = ', '.join(set(self._gsims_by_trt) - trts)
            self.error = 'missing distance for %s and no default' % missing
            return False
        return True

    def is_valid_intensity_measure_types(self):
        """
        If the IMTs and levels are extracted from the risk models,
        they must not be set directly. Moreover, if
        `intensity_measure_types_and_levels` is set directly,
        `intensity_measure_types` must not be set.
        """
        if self.ground_motion_correlation_model:
            for imt in self.imtls:
                if not (imt.startswith('SA') or imt == 'PGA'):
                    raise ValueError(
                        'Correlation model %s does not accept IMT=%s' % (
                            self.ground_motion_correlation_model, imt))
        if self.risk_files:  # IMTLs extracted from the risk files
            return (self.intensity_measure_types is None and
                    self.intensity_measure_types_and_levels is None)
        elif not hasattr(self, 'hazard_imtls') and not hasattr(
                self, 'risk_imtls'):
            return False
        return True

    def is_valid_intensity_measure_levels(self):
        """
        In order to compute hazard curves, `intensity_measure_types_and_levels`
        must be set or extracted from the risk models.
        """
        invalid = self.no_imls() and not self.risk_files and (
            self.hazard_curves_from_gmfs or self.calculation_mode in
            ('classical', 'disaggregation'))
        return not invalid

    def is_valid_sites_disagg(self):
        """
        The option `sites_disagg` (when given) requires `specific_assets` to
        be set.
        """
        if self.sites_disagg:
            return self.specific_assets or 'specific_assets' in self.inputs
        return True  # a missing sites_disagg is valid

    def is_valid_specific_assets(self):
        """
        Read the special assets from the parameters `specific_assets` or
        `specific_assets_csv`, if present. You cannot have both. The
        concept is meaninful only for risk calculators.
        """
        if self.specific_assets and 'specific_assets' in self.inputs:
            return False
        else:
            return True

    def is_valid_export_dir(self):
        """
        export_dir={export_dir} must refer to a directory,
        and the user must have the permission to write on it.
        """
        if self.export_dir and not os.path.isabs(self.export_dir):
            self.export_dir = os.path.normpath(
                os.path.join(self.input_dir, self.export_dir))
        if not self.export_dir:
            self.export_dir = os.path.expanduser('~')  # home directory
            logging.warning('export_dir not specified. Using export_dir=%s'
                            % self.export_dir)
            return True
        elif not os.path.exists(self.export_dir):
            try:
                os.makedirs(self.export_dir)
            except PermissionError:
                return False
            return True
        return os.path.isdir(self.export_dir) and os.access(
            self.export_dir, os.W_OK)

    def is_valid_sites(self):
        """
        The sites are overdetermined
        """
        if 'site_model' in self.inputs and 'sites' in self.inputs:
            return False
        elif 'site_model' in self.inputs and self.sites:
            return False
        elif 'sites' in self.inputs and self.sites:
            return False
        elif self.sites and self.region and self.region_grid_spacing:
            return False
        else:
            return True

    def is_valid_complex_fault_mesh_spacing(self):
        """
        The `complex_fault_mesh_spacing` parameter can be None only if
        `rupture_mesh_spacing` is set. In that case it is identified with it.
        """
        rms = getattr(self, 'rupture_mesh_spacing', None)
        if rms and not getattr(self, 'complex_fault_mesh_spacing', None):
            self.complex_fault_mesh_spacing = self.rupture_mesh_spacing
        return True

    def is_valid_optimize_same_id_sources(self):
        """
        The `optimize_same_id_sources` can be true only in the classical
        calculators.
        """
        if (self.optimize_same_id_sources and
                'classical' in self.calculation_mode or
                'disagg' in self.calculation_mode):
            return True
        elif self.optimize_same_id_sources:
            return False
        else:
            return True

    def check_uniform_hazard_spectra(self):
        ok_imts = [imt for imt in self.imtls if imt == 'PGA' or
                   imt.startswith('SA')]
        if not ok_imts:
            raise ValueError('The `uniform_hazard_spectra` can be True only '
                             'if the IMT set contains SA(...) or PGA, got %s'
                             % list(self.imtls))
        elif len(ok_imts) == 1:
            logging.warning(
                'There is a single IMT, the uniform_hazard_spectra plot will '
                'contain a single point')

    def check_source_model(self):
        if ('hazard_curves' in self.inputs or 'gmfs' in self.inputs or
            'multi_peril' in self.inputs or self.calculation_mode.startswith(
                'scenario')):
            return
        if ('source_model_logic_tree' not in self.inputs and
                not self.hazard_calculation_id):
            raise ValueError('Missing source_model_logic_tree in %s '
                             'or missing --hc option' %
                             self.inputs.get('job_ini', 'job_ini'))

    def check_missing(self, param, action):
        """
        Make sure the given parameter is missing in the job.ini file
        """
        assert action in ('debug', 'info', 'warn', 'error'), action
        if self.inputs.get(param):
            msg = '%s_file in %s is ignored in %s' % (
                param, self.inputs['job_ini'], self.calculation_mode)
            if action == 'error':
                raise InvalidFile(msg)
            else:
                getattr(logging, action)(msg)

    def hazard_precomputed(self):
        """
        :returns: True if the hazard is precomputed
        """
        if 'gmfs' in self.inputs or 'hazard_curves' in self.inputs:
            return True
        elif self.hazard_calculation_id:
            parent = list(util.read(self.hazard_calculation_id))
            return 'gmf_data' in parent or 'poes' in parent
