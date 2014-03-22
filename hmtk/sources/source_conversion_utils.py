#!/usr/bin/env/python
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
import abc
from decimal import Decimal
from openquake.nrmllib import models
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.geo.nodalplane import NodalPlane
from openquake.hazardlib import mfd
from openquake.hazardlib.scalerel import get_available_scalerel
from openquake.hazardlib.scalerel.base import BaseMSR
from openquake.hazardlib.scalerel.wc1994 import WC1994

SCALE_RELS = get_available_scalerel()


class MFDConverter(object):
    '''
    Abstract base class for converting the mfd between the openquake.hazardlib
    implementation and the openquake.nrmllib implementation
    '''
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def convert(self, mag_freq_dist):
        '''
        Converts the input magnitude frequency distribution in the
        openquake.hazardlib format to the openquake.nrmllib.models format

        :param mag_freq_dist:
            Magnitude frequency distribution as either instance of the :class:
            openquake.hazardlib.mfd

        :returns:
            Truncated Gutenberg-Richter distribution as an instance of the
            :class: openquake.nrmllib.models

        '''
        raise NotImplementedError

    @abc.abstractmethod
    def to_hazardlib(self, mag_freq_dist):
        """
        Converts the input MFD from the openquake.nrmllib.models format
        to openquake.hazardlib format
        """
        raise NotImplementedError


class ConvertTruncGR(MFDConverter):
    '''
     Converts the :class: openquake.hazardlib.mfd.truncated_gr to
     the class openquake.nrmllib.models.TGRMFD
    '''
    def convert(self, mag_freq_dist):
        '''
        Converts the input truncated Gutenberg-Richter magnitude frequency
        distribution to the required openquake.nrmlib implementation

        :param mag_freq_dist:
            Magnitude frequency distribution as either instance of the :class:
            openquake.hazardlib.mfd.truncated_gr.TruncatedGRMFD

        :returns:
            Truncated Gutenberg-Richter distribution as an instance of the
            :class: openquake.nrmllib.models.TGRMFD

        '''
        assert isinstance(mag_freq_dist, mfd.truncated_gr.TruncatedGRMFD)
        return models.TGRMFD(a_val=mag_freq_dist.a_val,
                             b_val=mag_freq_dist.b_val,
                             min_mag=mag_freq_dist.min_mag,
                             max_mag=mag_freq_dist.max_mag)

    def to_hazardlib(self, mag_freq_dist):
        """

        """
        assert isinstance(mag_freq_dist, models.TGRMFD)
        return mfd.truncated_gr.TruncatedGRMFD(
            a_val = mag_freq_dist.a_val,
            b_val = mag_freq_dist.b_val,
            min_mag = mag_freq_dist.min_mag,
            max_mag = mag_freq_dist.max_mag,
            bin_width=0.1)




class ConvertIncremental(MFDConverter):
    '''
     Converts an evenly discretized incremental magnitude frequency
     distribution in the form of either
     :class: openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretized or
     the :class: openquake.nrmllib.models.IncrementalMFD
    '''
    def convert(self, mag_freq_dist):
        '''
        :param mag_freq_dist:
            Magnitude frequency distribution as instance of the :class:
            openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretized

        :returns:
            Evenly discretized magnitude frequency distribution as an instance
            of the :class: openquake.nrmllib.models.IncrementalMFD

        '''
        assert isinstance(mag_freq_dist,
                          mfd.evenly_discretized.EvenlyDiscretizedMFD)
        return models.IncrementalMFD(
            min_mag=mag_freq_dist.min_mag,
            bin_width=mag_freq_dist.bin_width,
            occur_rates=mag_freq_dist.occurrence_rates)

    def to_hazardlib(self, mag_freq_dist):
        """

        """
        assert isinstance(mag_freq_dist, models.IncrementalMFD):
        return mfd.evenly_discretized.EvenlyDiscretizedMFD(
            min_mag=mag_freq_dist.min_mag,
            bin_width=mag_freq_dist.bin_width,
            occurrence_rates=mag_freq_dist.occur_rates)


MFD_MAP = {'TruncatedGRMFD': ConvertTruncGR(),
           'EvenlyDiscretizedMFD': ConvertIncremental()}

# Accepted MFD name lists
ACCEPTED_MFD = ['TGRMFD', 'IncrementalMFD']


def render_mfd(mag_freq_dist):
    '''
    Render the magnitude frequency distribution
    '''

    mfd_name = mag_freq_dist.__class__.__name__
    if mfd_name in ACCEPTED_MFD:
        # Class is already an instance of a oq.nrmllib.models mfd class
        return mag_freq_dist

    if not mfd_name in MFD_MAP.keys():
        raise ValueError('Magnitude frequency distribution %s not supported',
                         mfd_name)
    return MFD_MAP[mfd_name].convert(mag_freq_dist)


def mfd_to_hazardlib(mag_freq_dist):
    """

    """
    if isinstance(mag_freq_dist, BaseMFD):
        return mag_freq_dist
    elif isinstance(mag_freq_dist, models.

def render_aspect_ratio(aspect_ratio, use_default=False):
    '''
    Returns the aspect ratio if one is defined for the source, otherwise
    if defaults are accepted a default value of 1.0 is returned or else
    a ValueError is raised

    :param float aspect_ratio:
        Ratio of along strike-length to down-dip width of the rupture

    :param bool use_default:
        If true, when aspect_ratio is undefined will return default value of
        1.0, otherwise will raise an error.
    '''
    if aspect_ratio:
        assert aspect_ratio > 0.
        return aspect_ratio
    else:
        if use_default:
            return 1.0
        else:
            raise ValueError('Rupture aspect ratio not defined!')


def render_mag_scale_rel(mag_scale_rel, use_default=False):
    '''
    Returns the class string of the Magnitude Scaling relation class
    or returns the string for 'WC1994' otherwise

    :param mag_scale_rel:
        Instance of the :class: openquake.hazardlib.scalerel.base.Base

    :param bool use_default:
        Boolean flag to opt to use defaults (True) or not. If set to False
        then ValueError will be raised if information is missing

    :returns:
        String code of scaling relation class
    '''
    if isinstance(mag_scale_rel, str):
        return mag_scale_rel

    if mag_scale_rel:
        return mag_scale_rel.__class__.__name__
    else:
        if use_default:
            # Returns the Wells and Coppersmith string
            return 'WC1994'
        else:
            raise ValueError('Magnitude Scaling Relation Not Defined!')

def mag_scale_rel_to_hazardlib(mag_scale_rel, use_default=False):
    """

    """
    if isinstance(mag_scale_rel, BaseMSR):
        return mag_scale_rel
    elif isinstance(mag_scale_rel, str):
        if not mag_scale_rel in SCALE_RELS.keys():
            raise ValueError('Magnitude scaling relation %s not supported!'
                             % mag_scale_rel)
        else:
            return SCALE_RELS[mag_scale_rel]
    else:
        if use_default:
            # Returns the Wells and Coppersmith string
            return WC1994()
        else:
            raise ValueError('Magnitude Scaling Relation Not Defined!')


def render_npd(nodal_plane_dist, use_default=False):
    '''
    Checks to see if nodal plane distribution exists and renders to
    an instances of the class openquake.nrmllib.models.NodalPlane

    :param nodal_plane_dist:
        Nodal plane distribution of a source as either an instance of
        :class: openquake.nrmllib.models.NodalPlane or
        :class: openquake.hazardlib.pmf.PMF

    :param bool use_default:
        Boolean flag to opt to use defaults (True) or not. If set to False
        then ValueError will be raised if information is missing

    :returns:
        List of instances of openquake.nrmllib.models.NodalPlane
    '''
    if isinstance(nodal_plane_dist, list):
        for npd in nodal_plane_dist:
            assert isinstance(npd, models.NodalPlane)
        return nodal_plane_dist

    elif isinstance(nodal_plane_dist, PMF):
        # Create an instance of openquak.nrmllib.models.NodalPlane
        prob_sum = Decimal('0.0')
        output_npd = []
        for (prob, value) in nodal_plane_dist.data:
            prob_sum += Decimal(str(prob))
            if not isinstance(value, NodalPlane):
                raise ValueError('Nodal Planes incorrectly formatted!')

            output_npd.append(models.NodalPlane(Decimal(str(prob)),
                                                strike=value.strike,
                                                dip=value.dip,
                                                rake=value.rake))
        if not prob_sum == Decimal('1.0'):
            raise ValueError('Nodal Plane probabilities do not sum to 1.0')

        return output_npd
    else:
        if use_default:
            # Use a default nodal plane with strike 0, dip 90 and rake 0.
            return [models.NodalPlane(Decimal('1.0'), strike=0., dip=90.,
                                      rake=0.)]
        else:
            raise ValueError('Nodal Plane distribution not defined')

def npd_to_pmf(nodal_plane_dist, use_default=False):
    """
    Returns the nodal plane distribution as an instance of the PMF class
    """
    if isinstance(nodal_plane_dist, PMF):
        # Aready in PMF format - return
        return nodal_plane_dist
    elif isinstance(nodal_plane_dist, list):
        npd_list = []
        for npd in nodal_plane_dist:
            assert isinstance(npd, models.NodalPlane):
            npd_list.append((npd.probability,
                             NodalPlane(npd.strike, npd.dip, npd.rake)))
        return PMF(npd_list)
    else:
        if use_default:
            return PMF([(1.0, NodalPlane(0.0, 90.0, 0.0))])
        else:
            raise ValueError('Nodal Plane distribution not defined')

def render_hdd(hypo_depth_dist, use_default=False):
    '''
    Check to see if hypocentral depth distribution exists. If it
    is already defined as an instance of
    openquake.nrmllib.HypocentralDepth then returns. If it is an instance
    of openquake.hazardlib.pmf.PMF then convert to nrmllib version
    '''
    if isinstance(hypo_depth_dist, list):
        for hdd in hypo_depth_dist:
            assert isinstance(hdd, models.HypocentralDepth)

        return hypo_depth_dist
    elif isinstance(hypo_depth_dist, PMF):
        prob_sum = Decimal('0.0')
        output_hdd = []
        for (prob, value) in hypo_depth_dist.data:
            prob_sum += Decimal(str(prob))
            output_hdd.append(models.HypocentralDepth(prob, value))

        if not prob_sum == Decimal('1.0'):
            raise ValueError('Hypocentral depth disribution probabilities '
                             'do not sum to 1.0')
        return output_hdd
    else:
        if use_default:
            # Default to a single hypocentral dwpth of 1.0
            return [models.HypocentralDepth(Decimal('1.0'), 10.)]
        else:
            raise ValueError('Hypocentral depth distribution not defined!')

def hdd_to_pmf(hypo_depth_dist, use_default=False):
    """
    Returns the hypocentral depth distribtuion as an instance of the :class:
    openquake.hazardlib.pmf. 
    """
    if isinstance(hypo_depth_dist, PMF):
        # Is already instance of PMF
        return hypo_depth_dist
    elif isinstance(hypo_depth_dist, list):
        # Convert from :class: openquake.nrmllib.models.HypocentralDepth
        hdd_list = []
        for hdd in hypo_depth_dist:
            assert isinstance(hdd, models.HypocentralDepth)
            hdd_list.append((hdd.probability, hdd.depth))
        return PMF(hdd_list)
    else:
        if use_default:
            # Default value of 10 km accepted
            return PMF([(1.0, 10.0)])
        else:
            # Out of options - raise error!
            raise ValueError('Hypocentral depth distribution not defined!')

def simple_trace_to_wkt_linestring(trace):
    '''
    Coverts a simple fault trace to well-known text format

    :param trace:
        Fault trace as instance of :class: openquake.hazardlib.geo.line.Line

    :returns:
        Well-known text (WKT) Linstring representation of the trace
    '''
    trace_str = ""
    for point in trace:
        trace_str += ' %s %s,' % (point.longitude, point.latitude)
    trace_str = trace_str.lstrip(' ')
    return 'LINESTRING (' + trace_str.rstrip(',') + ')'


def simple_edge_to_wkt_linestring(edge):
    '''
    Coverts a simple fault trace to well-known text format

    :param trace:
        Fault trace as instance of :class: openquake.hazardlib.geo.line.Line

    :returns:
        Well-known text (WKT) Linstring representation of the trace
    '''
    trace_str = ""
    for point in edge:
        trace_str += ' %s %s %s,' % (point.longitude, point.latitude,
                                     point.depth)
    trace_str = trace_str.lstrip(' ')
    return 'LINESTRING (' + trace_str.rstrip(',') + ')'


def complex_trace_to_wkt_linestring(edges):
    '''
    Converts a set of complex fault edges to an instance of the :class:
    openquake.nrmllib.models.ComplexFaultGeometry

    :param list edges:
        Edges of the fault as a list of instances of the :class:
        openquake.hazardlib.geo.line.Line

    :returns:
        Complex fault geometry as instance of the :class:
        openquake.nrmllib.models.ComplexFaultGeometry

    '''
    int_edges = []
    for iloc, edge in enumerate(edges):
        if iloc == 0:
            top_edge = simple_edge_to_wkt_linestring(edge)
        elif iloc == len(edges) - 1:
            bottom_edge = simple_edge_to_wkt_linestring(edge)
        else:
            int_edges.append(simple_edge_to_wkt_linestring(edge))
    if len(int_edges) == 0:
        int_edges = None
    return models.ComplexFaultGeometry(top_edge, bottom_edge, int_edges)
