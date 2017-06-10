# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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
import numpy

from openquake.baselib import parallel
from openquake.baselib.general import DictArray
from openquake.hazardlib.imt import from_string
from openquake.hazardlib import correlation, stats
from openquake.hazardlib import valid, InvalidFile
from openquake.commonlib import logictree
from openquake.commonlib.riskmodels import get_risk_files

GROUND_MOTION_CORRELATION_MODELS = ['JB2009']
TWO16 = 2 ** 16  # 65536


class OqParam(valid.ParamSet):
    siteparam = dict(
        vs30measured='reference_vs30_type',
        vs30='reference_vs30_value',
        z1pt0='reference_depth_to_1pt0km_per_sec',
        z2pt5='reference_depth_to_2pt5km_per_sec',
        backarc='reference_backarc',
    )
    asset_loss_table = valid.Param(valid.boolean, False)
    area_source_discretization = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    asset_correlation = valid.Param(valid.NoneOr(valid.FloatRange(0, 1)), 0)
    asset_life_expectancy = valid.Param(valid.positivefloat)
    avg_losses = valid.Param(valid.boolean, False)
    base_path = valid.Param(valid.utf8, '.')
    calculation_mode = valid.Param(valid.Choice(), '')  # -> get_oqparam
    coordinate_bin_width = valid.Param(valid.positivefloat)
    compare_with_classical = valid.Param(valid.boolean, False)
    concurrent_tasks = valid.Param(
        valid.positiveint, parallel.executor.num_tasks_hint)
    conditional_loss_poes = valid.Param(valid.probabilities, [])
    continuous_fragility_discretization = valid.Param(valid.positiveint, 20)
    description = valid.Param(valid.utf8_not_empty)
    disagg_outputs = valid.Param(valid.disagg_outputs, None)
    distance_bin_width = valid.Param(valid.positivefloat)
    mag_bin_width = valid.Param(valid.positivefloat)
    export_dir = valid.Param(valid.utf8, '.')
    export_multi_curves = valid.Param(valid.boolean, False)
    exports = valid.Param(valid.export_formats, ())
    ground_motion_correlation_model = valid.Param(
        valid.NoneOr(valid.Choice(*GROUND_MOTION_CORRELATION_MODELS)), None)
    ground_motion_correlation_params = valid.Param(valid.dictionary)
    ground_motion_fields = valid.Param(valid.boolean, False)
    gsim = valid.Param(valid.gsim, None)
    hazard_calculation_id = valid.Param(valid.NoneOr(valid.positiveint), None)
    hazard_curves_from_gmfs = valid.Param(valid.boolean, False)
    hazard_output_id = valid.Param(valid.NoneOr(valid.positiveint))
    hazard_maps = valid.Param(valid.boolean, False)
    hypocenter = valid.Param(valid.point3d)
    ignore_missing_costs = valid.Param(valid.namelist, [])
    ignore_covs = valid.Param(valid.boolean, False)
    iml_disagg = valid.Param(valid.floatdict, {})  # IMT -> IML
    inputs = valid.Param(dict, {})
    insured_losses = valid.Param(valid.boolean, False)
    intensity_measure_types = valid.Param(valid.intensity_measure_types, None)
    intensity_measure_types_and_levels = valid.Param(
        valid.intensity_measure_types_and_levels, None)
    interest_rate = valid.Param(valid.positivefloat)
    investigation_time = valid.Param(valid.positivefloat, None)
    loss_curve_resolution = valid.Param(valid.positiveint, 50)
    loss_ratios = valid.Param(valid.loss_ratios, ())
    lrem_steps_per_interval = valid.Param(valid.positiveint, 0)
    steps_per_interval = valid.Param(valid.positiveint, 1)
    master_seed = valid.Param(valid.positiveint, 0)
    maximum_distance = valid.Param(valid.maximum_distance)  # km
    asset_hazard_distance = valid.Param(valid.positivefloat, 5)  # km
    max_hazard_curves = valid.Param(valid.boolean, False)
    mean_hazard_curves = valid.Param(valid.boolean, True)
    max_loss_curves = valid.Param(valid.boolean, False)
    mean_loss_curves = valid.Param(valid.boolean, True)
    minimum_intensity = valid.Param(valid.floatdict, {})  # IMT -> minIML
    number_of_ground_motion_fields = valid.Param(valid.positiveint)
    number_of_logic_tree_samples = valid.Param(valid.positiveint, 0)
    num_epsilon_bins = valid.Param(valid.positiveint)
    poes = valid.Param(valid.probabilities, [])
    poes_disagg = valid.Param(valid.probabilities, [])
    quantile_hazard_curves = valid.Param(valid.probabilities, [])
    quantile_loss_curves = valid.Param(valid.probabilities, [])
    random_seed = valid.Param(valid.positiveint, 42)
    reference_depth_to_1pt0km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_depth_to_2pt5km_per_sec = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_vs30_type = valid.Param(
        valid.Choice('measured', 'inferred'), 'measured')
    reference_vs30_value = valid.Param(
        valid.positivefloat, numpy.nan)
    reference_backarc = valid.Param(valid.boolean, False)
    region = valid.Param(valid.coordinates, None)
    region_constraint = valid.Param(valid.wkt_polygon, None)
    region_grid_spacing = valid.Param(valid.positivefloat, None)
    risk_imtls = valid.Param(valid.intensity_measure_types_and_levels, {})
    risk_investigation_time = valid.Param(valid.positivefloat, None)
    rupture_mesh_spacing = valid.Param(valid.positivefloat)
    ruptures_per_block = valid.Param(valid.positiveint, 1000)
    complex_fault_mesh_spacing = valid.Param(
        valid.NoneOr(valid.positivefloat), None)
    save_ruptures = valid.Param(valid.boolean, True)
    ses_per_logic_tree_path = valid.Param(valid.positiveint, 1)
    ses_seed = valid.Param(valid.positiveint, 42)
    max_site_model_distance = valid.Param(valid.positivefloat, 5)  # by Graeme
    sites = valid.Param(valid.NoneOr(valid.coordinates), None)
    sites_disagg = valid.Param(valid.NoneOr(valid.coordinates), [])
    sites_per_tile = valid.Param(valid.positiveint, 20000)
    sites_slice = valid.Param(valid.simple_slice, (None, None))
    specific_assets = valid.Param(valid.namelist, [])
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
            self._file_type, self._risk_files = get_risk_files(self.inputs)
            return self._risk_files

    @property
    def file_type(self):
        try:
            return self._file_type
        except AttributeError:
            self._file_type, self._risk_files = get_risk_files(self.inputs)
            return self._file_type

    def __init__(self, **names_vals):
        super(OqParam, self).__init__(**names_vals)
        if 'calculation_mode' not in names_vals:
            raise ValueError('Missing calculation_mode in the .ini file!')
        self.risk_investigation_time = (
            self.risk_investigation_time or self.investigation_time)
        if ('intensity_measure_types_and_levels' in names_vals and
                'intensity_measure_types' in names_vals):
            logging.warn('Ignoring intensity_measure_types since '
                         'intensity_measure_types_and_levels is set')
        if 'intensity_measure_types_and_levels' in names_vals:
            self.hazard_imtls = self.intensity_measure_types_and_levels
            delattr(self, 'intensity_measure_types_and_levels')
        elif 'intensity_measure_types' in names_vals:
            self.hazard_imtls = dict.fromkeys(self.intensity_measure_types)
            delattr(self, 'intensity_measure_types')
        self._file_type, self._risk_files = get_risk_files(self.inputs)

        # check the gsim_logic_tree
        if 'gsim_logic_tree' in self.inputs:
            if self.gsim:
                raise ValueError('If `gsim_logic_tree_file` is set, there '
                                 'must be no `gsim` key')
            path = os.path.join(
                self.base_path, self.inputs['gsim_logic_tree'])
            gsim_lt = logictree.GsimLogicTree(path, ['*'])

            # check the number of branchsets
            branchsets = len(gsim_lt._ltnode)
            if 'scenario' in self.calculation_mode and branchsets > 1:
                raise InvalidFile(
                    '%s for a scenario calculation must contain a single '
                    'branchset, found %d!' % (path, branchsets))

            # check the IMTs vs the GSIMs
            self._gsims_by_trt = gsim_lt.values
            for gsims in self._gsims_by_trt.values():
                self.check_gsims(gsims)
        elif self.gsim is not None:
            self.check_gsims([self.gsim])

        # checks for disaggregation
        if self.calculation_mode == 'disaggregation':
            if not self.poes_disagg and not self.iml_disagg:
                raise ValueError('poes_disagg or iml_disagg must be set '
                                 'in the job.ini file')
            elif self.poes_disagg and self.iml_disagg:
                logging.warn(
                    'iml_disagg=%s will not be computed from poes_disagg=%s',
                    str(self.iml_disagg), self.poes_disagg)

        # checks for classical_damage
        if self.calculation_mode == 'classical_damage':
            if self.quantile_loss_curves:
                raise ValueError('quantile_loss_curves are not defined '
                                 'for classical_damage calculations: '
                                 'remove them for the .ini file')
            if self.conditional_loss_poes:
                raise ValueError('conditional_loss_poes are not defined '
                                 'for classical_damage calculations: '
                                 'remove them for the .ini file')
        
        # checks for event_based_risk
        if (self.calculation_mode == 'event_based_risk'
                and self.asset_correlation not in (0, 1)):
            raise ValueError('asset_correlation != {0, 1} is no longer'
                             ' supported')

        # checks for ucerf
        if 'ucerf' in self.calculation_mode:
            if self.ses_per_logic_tree_path >= TWO16:
                raise ValueError('ses_per_logic_tree_path too big: %d' %
                                 self.ses_per_logic_tree_path)
            if self.number_of_logic_tree_samples >= TWO16:
                raise ValueError('number_of_logic_tree_samples too big: %d' %
                                 self.number_of_logic_tree_samples)

    def check_gsims(self, gsims):
        """
        :param gsims: a sequence of GSIM instances
        """
        imts = set('SA' if imt.startswith('SA') else imt for imt in self.imtls)
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
                    if param in ('lons', 'lats'):  # no check
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
        assert self.investigation_time, 'investigation_time = 0!'
        return (self.risk_investigation_time or self.investigation_time) / (
            self.investigation_time * self.ses_per_logic_tree_path)

    @property
    def imtls(self):
        """
        Returns an OrderedDict with the risk intensity measure types and
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
        return sorted(self.risk_files)

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
            for loss_type, rf in risk_functions.items():
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

    def loss_dt(self, dtype=numpy.float32):
        """
        Return a composite dtype based on the loss types, including occupants
        """
        return numpy.dtype(self.loss_dt_list(dtype))

    def loss_dt_list(self, dtype=numpy.float32):
        """
        Return a data type list [(loss_name, dtype), ...]
        """
        loss_types = self.all_cost_types
        dts = [(str(lt), dtype) for lt in loss_types]
        if self.insured_losses:
            for lt in loss_types:
                dts.append((str(lt) + '_ins', dtype))
        return dts

    def no_imls(self):
        """
        Return True if there are no intensity measure levels
        """
        return all(numpy.isnan(ls).any() for ls in self.imtls.values())

    def get_correl_model(self):
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
        for q in self.quantile_hazard_curves:
            names.append('quantile-%s' % q)
            funcs.append(functools.partial(stats.quantile_curve, q))
        if self.max_hazard_curves:
            names.append('max')
            funcs.append(stats.max_curve)
        return list(zip(names, funcs))

    def risk_stats(self):
        """
        Return a list of items with the statistical functions defined for the
        risk calculation
        """
        names = []  # name of statistical functions
        funcs = []  # statistical functions of kind func(values, weights)
        if self.mean_loss_curves:
            names.append('mean')
            funcs.append(stats.mean_curve)
        for q in self.quantile_loss_curves:
            names.append('quantile-%s' % q)
            funcs.append(functools.partial(stats.quantile_curve, q))
        if self.max_loss_curves:
            names.append('max')
            funcs.append(stats.max_curve)
        return list(zip(names, funcs))

    @property
    def job_type(self):
        """
        'hazard' or 'risk'
        """
        return 'risk' if ('risk' in self.calculation_mode or
                          'damage' in self.calculation_mode or
                          'bcr' in self.calculation_mode) else 'hazard'

    def is_valid_truncation_level_disaggregation(self):
        """
        Truncation level must be set for disaggregation calculations
        """
        if self.calculation_mode == 'disaggregation':
            return self.truncation_level is not None
        else:
            return True

    def is_valid_region(self):
        """
        If there is a region a region_grid_spacing must be given
        """
        return self.region_grid_spacing if self.region else True

    def is_valid_geometry(self):
        """
        It is possible to infer the geometry only if exactly
        one of sites, sites_csv, hazard_curves_csv, gmfs_csv,
        region and exposure_file is set. You did set more than
        one, or nothing.
        """
        if ('risk' in self.calculation_mode or
                'damage' in self.calculation_mode or
                'bcr' in self.calculation_mode):
            return True  # no check on the sites for risk
        flags = dict(
            sites=bool(self.sites),
            sites_csv=self.inputs.get('sites', 0),
            hazard_curves_csv=self.inputs.get('hazard_curves', 0),
            gmfs_csv=self.inputs.get('gmvs', 0),
            region=bool(self.region),
            exposure=self.inputs.get('exposure', 0))
        # NB: below we check that all the flags
        # are mutually exclusive
        return sum(bool(v) for v in flags.values()) == 1 or self.inputs.get(
            'site_model')

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
        if 'source_model_logic_tree' not in self.inputs:
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
        The `export_dir` parameter must refer to a directory,
        and the user must have the permission to write on it.
        """
        if not self.export_dir:
            self.export_dir = os.path.expanduser('~')  # home directory
            logging.warn('export_dir not specified. Using export_dir=%s'
                         % self.export_dir)
            return True
        elif not os.path.exists(self.export_dir):
            # check that we can write on the parent directory
            pdir = os.path.dirname(self.export_dir)
            can_write = os.path.exists(pdir) and os.access(pdir, os.W_OK)
            if can_write:
                os.mkdir(self.export_dir)
            return can_write
        return os.path.isdir(self.export_dir) and os.access(
            self.export_dir, os.W_OK)

    def is_valid_inputs(self):
        """
        Invalid calculation_mode="{calculation_mode}" or missing
        fragility_file/vulnerability_file in the .ini file.
        """
        if 'damage' in self.calculation_mode:
            return any(key.endswith('_fragility') for key in self.inputs)
        elif 'risk' in self.calculation_mode:
            return any(key.endswith('_vulnerability') for key in self.inputs)
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

    def check_uniform_hazard_spectra(self):
        ok_imts = [imt for imt in self.imtls if imt == 'PGA' or
                   imt.startswith('SA')]
        if not ok_imts:
            raise ValueError('The `uniform_hazard_spectra` can be True only '
                             'if the IMT set contains SA(...) or PGA, got %s'
                             % list(self.imtls))
