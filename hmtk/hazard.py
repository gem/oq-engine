# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani,
# D. Monelli.
#
# The Hazard Modeller's Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>
#
# DISCLAIMER
#
# The software Hazard Modeller's Toolkit (hmtk) provided herein
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
# The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

# -*- coding: utf-8 -*-

"""
Simple utilities to run hazard calculations from within the toolkit
"""
import sys
import numpy as np
import multiprocessing
from collections import OrderedDict
#from openquake.hazardlib.calc.hazard_curve import hazard_curves
from openquake.hazardlib.calc import hazard_curve
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.gsim import get_available_gsims
from openquake.hazardlib.gsim.base import ContextMaker
from openquake.hazardlib.calc import filters
from openquake.hazardlib import imt
from openquake.hazardlib.geo.point import Point
from hmtk.sources.source_model import mtkSourceModel

DEFAULT_WORKERS = multiprocessing.cpu_count()
GSIM_MAP = get_available_gsims()


def _check_supported_imts(imts):
    """
    Checks that all of the IMTs in the list are supported
    """
    output_imts = []
    for imtx in imts:
        if imtx in imt.__all__:
            output_imts.append(imt.__dict__[imtx]())
        elif 'SA' in imtx:
            output_imts.append(imt.from_string(imtx))
        else:
            raise ValueError('IMT %s not supported in OpenQuake!' % imtx)
    return output_imts

def _check_imts_imls(imts, imls):
    """
    Pre-process IMTS and IMLs, returning a corresponding IMT dictionary
    """
    #imts = _check_supported_imts(imts)
    n_imts = len(imts)
    if len(imls) == 1:
        # Fixed IMLs
        imts = OrderedDict([(imt, imls[0]) for imt in imts])
    elif len(imls) == n_imts:
        # One set of IMLS per IMT
        imts = OrderedDict([(imts[iloc], imls[iloc])
                            for iloc in range(0, n_imts)])
    else:
        raise ValueError('Number of IML sets must be 1 or equal '
                         'to number of IMTs')
    return imts

def _preprocess_gmpes(source_model, gmpes):
    """
    :param dict gmpes:
        Regionalisation of GMPEs {'region_name': 'GMPE Name'}
    """
    model_regions = [src.tectonic_region_type for src in source_model]
    for key in gmpes.keys():
        #if not key in model_regions:
        #    raise ValueError('Region type %s not in source model' % key)
        if gmpes[key] in GSIM_MAP.keys():
            gmpes[key] = GSIM_MAP[gmpes[key]]()
        else:
            raise ValueError('GMPE %s not supported!' % gmpes[key])
    for region in model_regions:
        if not region in gmpes.keys():
            raise ValueError('No GMPE defined for region type %s' % region)
    return gmpes



def site_array_to_collection(site_array):
    """
    Converts a set of sites from a 2D numpy array to an instance of :class:
    openquake.hazardlib.site.SiteCollection
    :param np.ndarray site_array:
        Site parameters as [ID, Long, Lat, vs30, vs30measured, z1pt0, z2pt5,
                            backarc]
    """
    site_list = []
    n_sites, n_param = np.shape(site_array)
    if n_param != 8:
        raise ValueError('Site array incorrectly formatted!')
    for iloc in range(0, n_sites):
        site = Site(Point(site_array[iloc, 1], site_array[iloc, 2]), # Location
                    site_array[iloc, 3], # Vs30
                    site_array[iloc, 4].astype(bool), # vs30measured
                    site_array[iloc, 5], # z1pt0
                    site_array[iloc, 6], # z2pt5
                    site_array[iloc, 7].astype(bool), # Backarc
                    site_array[iloc, 0].astype(int)) # ID
        site_list.append(site)
    return SiteCollection(site_list)


class HMTKHazardCurve(object):
    """
    Base Class for calculation of hazard curves according to
    different parallelisation strategies
    :param source_model:
        Source model as list of OpenQuake sources
    :param sites:
        Sites as :class: openquake.hazardlib.site.SiteCollection
    :param gmpes:
        GMPE dictionary with params {'Region', 'GMPEName'}
    :param np.ndarray imls:
        Intensity measure levels (g for PGA, Sa; cm/s for PGV)
    :param imts:
        List of intensity measures as :class: openquake.hazardlib.imt
    :param float truncation_level:
        GMPE truncation level
    :param src_filter:
        Source distance filter
    :param rup_filter:
        Rupture distance filter
    """
    def __init__(self, source_model, sites, gmpes, imls, imts,
        truncation_level=None, source_integration_dist=None,
        rupture_integration_dist=None):
        """
        Instatiate and preprocess
        :param float source_integration_dist:
            Integration distance for sources
        :param float rupture_integration_dist:
            Integration distance for ruptures
        """
        self.source_model = source_model
        self.sites = sites
        self.gmpes = gmpes
        self.imls = imls
        self.imts = imts
        self.truncation_level = truncation_level
        if source_integration_dist:
            self.src_filter = filters.source_site_distance_filter(
                source_integration_dist)
        else:
            self.src_filter = filters.source_site_noop_filter
        if rupture_integration_dist:
            self.rup_filter = filters.rupture_site_distance_filter(
                rupture_integration_dist)
        else:
            self.rup_filter = filters.rupture_site_noop_filter

        self.preprocess_inputs()

    def preprocess_inputs(self):
        """
        Perform initial checks to ensure correct inputs to hazard calculation
        """
        if not isinstance(self.sites, SiteCollection):
            raise ValueError('Sites must be input as instance of :class: '
                             'openquake.hazardlib.site.SiteCollection')
        # Preprocess GMPEs
        self.gmpes = _preprocess_gmpes(self.source_model, self.gmpes)
        # Set up IMT dictionary
        self.imts = _check_imts_imls(self.imts, self.imls)

    def _setup_poe_set(self):
        """
        Instantiated PoE values to zeros
        """
        num_sites = self.sites.total_sites
        poe_set = OrderedDict([(imt, np.ones([num_sites, len(self.imts[imt])]))
                              for imt in self.imts])
        return poe_set

    def calculate_hazard(self, num_workers=DEFAULT_WORKERS,
            num_src_workers=1):
        """
        Calculates the hazard
        :param int num_workers:
            Number of workers for parallel calculation
        :param int num_src_workers:
            Number of elements per worker
        """
        return hazard_curve.calc_hazard_curves(self.source_model,
                                               self.sites,
                                               self.imts,
                                               self.gmpes,
                                               self.truncation_level,
                                               self.src_filter,
                                               self.rup_filter)


def get_hazard_curve_source(input_set):
    """
    From a dictionary input set returns hazard curves
    """
    try:
        cmaker = ContextMaker(
            [input_set["gsims"][key] for key in input_set["gsims"]],
            None)
        for rupture, r_sites in input_set["ruptures_sites"]:
            gsim = input_set["gsims"][rupture.tectonic_region_type]
            sctx, rctx, dctx = cmaker.make_contexts(r_sites, rupture)
            for iimt in input_set["imts"]:
                poes = gsim.get_poes(sctx, rctx, dctx, imt.from_string(iimt),
                                     input_set["imts"][iimt],
                                     input_set["truncation_level"])
                pno = rupture.get_probability_no_exceedance(poes)
                input_set["curves"][iimt] *= r_sites.expand(pno, placeholder=1)
    except Exception, err:
        pass
    for iimt in input_set["imts"]:
        input_set["curves"][iimt] = 1 - input_set["curves"][iimt]
    return input_set["curves"]


class HMTKHazardCurveParallelSource(HMTKHazardCurve):
    """
    Runs the PSHA calculation parallelising by source
    """
    def calculate_hazard(self, num_workers=DEFAULT_WORKERS,
            num_src_workers=1):
        """
        Executes the hazard calculation, parallelising by source
        """
        p = multiprocessing.Pool(processes=num_workers)
        poe_set = self._setup_poe_set()
        src_counter = 0
        input_set = []
        if len(self.source_model) < (num_workers * num_src_workers):
            gather_limit = len(self.source_model)
        else:
            gather_limit = num_workers * num_src_workers
        for source in self.source_model:
            src_counter += 1
            if src_counter < gather_limit:
                inputs = self._get_calculation_inputs(source)
                if inputs:
                    input_set.append(inputs)
            else:
                inputs = self._get_calculation_inputs(source)
                if inputs:
                    input_set.append(inputs)
                # TODO Theoretically this should use the multiprocessing
                # tools. However, after extensive testing it is shown that
                # the OpenQuake hazardlib cannot be parallelised safely with
                # pythons own multiprocessing tools. The function will be
                # kept in its present form to allow the problem to be 
                # resolved in future, but there is currently no performance
                # gain over the non-parallelised version
                poei = map(get_hazard_curve_source,
                           input_set)

                for poe in poei:
                    poe_set_keys = poe_set.keys()
                    poe_keys = poe.keys()
                    for iloc, key in enumerate(poe_set_keys):
                        poe_set[key] *= 1.0 - poe[poe_keys[iloc]]

                input_set = []
                src_counter = 0
        for key in poe_set.keys():
            poe_set[key] = 1.0 - poe_set[key]
        return poe_set

    def _get_calculation_inputs(self, source):
        """
        Returns the calculation inputs, checking if sources are missing
        """
        (s_source, s_sites) = self.src_filter(((source, self.sites)))
        if not s_source:
            return None

        inputs = {
            "imts": self.imts,
            "gsims": {source.tectonic_region_type:
                      self.gmpes[source.tectonic_region_type]},
            "truncation_level": self.truncation_level,
            "curves": OrderedDict([(imt, np.ones([len(self.sites),
                                          len(self.imts[imt])]))
                                          for imt in self.imts])}
        inputs["ruptures_sites"] = [(rupture, s_sites)
                                     for rupture in source.iter_ruptures()]
        return inputs
