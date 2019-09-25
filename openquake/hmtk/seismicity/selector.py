# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2019 GEM Foundation, G. Weatherill, M. Pagani,
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
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM's OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.

'''
Class to implement set of functionalities for selecting events from
and earthquake catalogue

'''

import numpy as np
from datetime import datetime
from copy import deepcopy
from openquake.hazardlib.geo.point import Point
from openquake.hazardlib.geo.mesh import Mesh
from openquake.hmtk.seismicity.catalogue import Catalogue
from openquake.hmtk.seismicity.utils import decimal_time


def _check_depth_limits(input_dict):
    '''Returns the default upper and lower depth values if not in dictionary

    :param input_dict:
        Dictionary corresponding to the kwargs dictionary of calling function

    :returns:
        'upper_depth': Upper seismogenic depth (float)
        'lower_depth': Lower seismogenic depth (float)
    '''
    if ('upper_depth' in input_dict.keys()) and input_dict['upper_depth']:
        if input_dict['upper_depth'] < 0.:
            raise ValueError('Upper seismogenic depth must be positive')
        else:
            upper_depth = input_dict['upper_depth']
    else:
        upper_depth = 0.0

    if ('lower_depth' in input_dict.keys()) and input_dict['lower_depth']:
        if input_dict['lower_depth'] < upper_depth:
            raise ValueError('Lower depth must take a greater value than'
                             ' upper depth!')
        else:
            lower_depth = input_dict['lower_depth']
    else:
        lower_depth = np.inf
    return upper_depth, lower_depth


def _get_decimal_from_datetime(time):
    '''
    As the decimal time function requires inputs in the form of numpy
    arrays need to convert each value in the datetime object  to a single
    numpy array
    '''

    # Get decimal seconds from seconds + microseconds
    temp_seconds = np.float(time.second) + (np.float(time.microsecond) / 1.0E6)
    return decimal_time(np.array([time.year], dtype=int),
                        np.array([time.month], dtype=int),
                        np.array([time.day], dtype=int),
                        np.array([time.hour], dtype=int),
                        np.array([time.minute], dtype=int),
                        np.array([temp_seconds], dtype=int))


class CatalogueSelector(object):
    '''
    Class to implement methods for selecting subsets of the catalogue
    according to various attribute criteria.

    :attr catalogue: The catalogue to which the selection is applied as
                     instance of openquake.hmtk.seismicity.catalogue.Catalogue

    :attr create_copy: Boolean to indicate whether to create copy of the
                       original catalogue before selecting {default = True}
    '''

    def __init__(self, master_catalogue, create_copy=True):
        '''
        Instantiate
        :param master_catalogue:
            Instance of openquake.hmtk.seismicity.catalogue.Catalogue class

        :param bool create_copy: Option to create copy of te class before
                                 selecting (i.e. preserving original class)
        '''
        self.catalogue = master_catalogue
        self.copycat = create_copy

    def select_catalogue(self, valid_id):
        '''
        Method to post-process the catalogue based on the selection options

        :param numpy.ndarray valid_id:
            Boolean vector indicating whether each event is selected (True)
            or not (False)

        :returns:
            Catalogue of selected events as instance of
            openquake.hmtk.seismicity.catalogue.Catalogue class
        '''
        if not np.any(valid_id):
            # No events selected - create clean instance of class
            output = Catalogue()
            output.processes = self.catalogue.processes

        elif np.all(valid_id):
            if self.copycat:
                output = deepcopy(self.catalogue)
            else:
                output = self.catalogue
        else:
            if self.copycat:
                output = deepcopy(self.catalogue)
            else:
                output = self.catalogue
            output.purge_catalogue(valid_id)
        return output

    def within_polygon(self, polygon, distance=None, **kwargs):
        '''
        Select earthquakes within polygon

        :param polygon:
            Centre point as instance of nhlib.geo.polygon.Polygon class

        :param float distance:
            Buffer distance (km) (can take negative values)

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            containing only selected events
        '''

        if distance:
            # If a distance is specified then dilate the polyon by distance
            zone_polygon = polygon.dilate(distance)
        else:
            zone_polygon = polygon

        # Make valid all events inside depth range
        upper_depth, lower_depth = _check_depth_limits(kwargs)
        valid_depth = np.logical_and(
            self.catalogue.data['depth'] >= upper_depth,
            self.catalogue.data['depth'] < lower_depth)

        # Events outside polygon returned to invalid assignment
        catalogue_mesh = Mesh(self.catalogue.data['longitude'],
                              self.catalogue.data['latitude'],
                              self.catalogue.data['depth'])
        valid_id = np.logical_and(valid_depth,
                                  zone_polygon.intersects(catalogue_mesh))

        return self.select_catalogue(valid_id)

    def circular_distance_from_point(self, point, distance, **kwargs):
        '''
        Select earthquakes within a distance from a Point

        :param point:
            Centre point as instance of nhlib.geo.point.Point class

        :param float distance:
            Distance (km)

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            containing only selected events
        '''

        if kwargs['distance_type'] is 'epicentral':
            locations = Mesh(
                self.catalogue.data['longitude'],
                self.catalogue.data['latitude'],
                np.zeros(len(self.catalogue.data['longitude']), dtype=float))
            point = Point(point.longitude, point.latitude, 0.0)
        else:
            locations = self.catalogue.hypocentres_as_mesh()

        is_close = point.closer_than(locations, distance)

        return self.select_catalogue(is_close)

    def cartesian_square_centred_on_point(self, point, distance, **kwargs):
        '''
        Select earthquakes from within a square centered on a point

        :param point:
            Centre point as instance of nhlib.geo.point.Point class

        :param distance:
            Distance (km)

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            class containing only selected events
        '''
        point_surface = Point(point.longitude, point.latitude, 0.)
        # As distance is
        north_point = point_surface.point_at(distance, 0., 0.)
        east_point = point_surface.point_at(distance, 0., 90.)
        south_point = point_surface.point_at(distance, 0., 180.)
        west_point = point_surface.point_at(distance, 0., 270.)
        is_long = np.logical_and(
            self.catalogue.data['longitude'] >= west_point.longitude,
            self.catalogue.data['longitude'] < east_point.longitude)
        is_surface = np.logical_and(
            is_long,
            self.catalogue.data['latitude'] >= south_point.latitude,
            self.catalogue.data['latitude'] < north_point.latitude)

        upper_depth, lower_depth = _check_depth_limits(kwargs)
        is_valid = np.logical_and(
            is_surface,
            self.catalogue.data['depth'] >= upper_depth,
            self.catalogue.data['depth'] < lower_depth)

        return self.select_catalogue(is_valid)

    def within_joyner_boore_distance(self, surface, distance, **kwargs):
        '''
        Select events within a Joyner-Boore distance of a fault

        :param surface:
            Fault surface as instance of
            nhlib.geo.surface.base.SimpleFaultSurface  or as instance of
            nhlib.geo.surface.ComplexFaultSurface

        :param float distance:
            Rupture distance (km)

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            containing only selected events
        '''

        upper_depth, lower_depth = _check_depth_limits(kwargs)

        rjb = surface.get_joyner_boore_distance(
            self.catalogue.hypocentres_as_mesh())
        is_valid = np.logical_and(
            rjb <= distance,
            np.logical_and(self.catalogue.data['depth'] >= upper_depth,
                           self.catalogue.data['depth'] < lower_depth))
        return self.select_catalogue(is_valid)

    def within_rupture_distance(self, surface, distance,  **kwargs):
        '''
        Select events within a rupture distance from a fault surface

        :param surface:
            Fault surface as instance of nhlib.geo.surface.base.BaseSurface

        :param float distance:
            Rupture distance (km)

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            containing only selected events
        '''
        # Check for upper and lower depths
        upper_depth, lower_depth = _check_depth_limits(kwargs)

        rrupt = surface.get_min_distance(self.catalogue.hypocentres_as_mesh())
        is_valid = np.logical_and(
            rrupt <= distance,
            np.logical_and(self.catalogue.data['depth'] >= upper_depth,
                           self.catalogue.data['depth'] < lower_depth))

        return self.select_catalogue(is_valid)

    def within_time_period(self, start_time=None, end_time=None):
        '''
        Select earthquakes occurring within a given time period

        :param start_time:
            Earliest time (as datetime.datetime object)

        :param end_time:
            Latest time (as datetime.datetime object)

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            containing only selected events
        '''
        time_value = self.catalogue.get_decimal_time()
        if not start_time:
            if not end_time:
                # No times input, therefore skip everything and return catalog
                return self.catalogue
            else:
                start_time = np.min(self.catalogue.data['year'])
        else:
            start_time = _get_decimal_from_datetime(start_time)

        if not end_time:
            end_time = _get_decimal_from_datetime(datetime.now())
        else:
            end_time = _get_decimal_from_datetime(end_time)

        # Get decimal time values
        time_value = self.catalogue.get_decimal_time()

        is_valid = np.logical_and(time_value >= start_time,
                                  time_value < end_time)

        return self.select_catalogue(is_valid)

    def within_depth_range(self, lower_depth=None, upper_depth=None):
        '''
        Selects events within a specified depth range

        :param float lower_depth:
            Lower depth for consideration

        :param float upper_depth:
            Upper depth for consideration

        :returns:
            Instance of :class:`openquake.hmtk.seismicity.catalogue.Catalogue`
            containing only selected events
        '''
        if not lower_depth:
            if not upper_depth:
                # No limiting depths defined - so return entire catalogue!
                return self.catalogue
            else:
                lower_depth = np.inf

        if not upper_depth:
            upper_depth = 0.0

        is_valid = np.logical_and(self.catalogue.data['depth'] >= upper_depth,
                                  self.catalogue.data['depth'] < lower_depth)
        return self.select_catalogue(is_valid)

    def within_magnitude_range(self, lower_mag=None, upper_mag=None):
        '''
        :param float lower_mag:
            Lower magnitude for consideration

        :param float upper_mag:
            Upper magnitude for consideration

        :returns:
            Instance of openquake.hmtk.seismicity.catalogue.Catalogue class containing
            only selected events
        '''
        if not lower_mag:
            if not upper_mag:
                # No limiting magnitudes defined - return entire catalogue!
                return self.catalogue
            else:
                lower_mag = -np.inf

        if not upper_mag:
            upper_mag = np.inf

        is_valid = np.logical_and(
            self.catalogue.data['magnitude'] >= lower_mag,
            self.catalogue.data['magnitude'] < upper_mag)

        return self.select_catalogue(is_valid)

    def create_cluster_set(self, vcl):
        """
        For a given catalogue and list of cluster IDs this function splits
        the catalogue into a dictionary containing an individual catalogue
        of events within each cluster

        :param numpy.ndarray vcl:
            Cluster ID list
        :returns:
            Dictionary of instances of the :class:
            openquake.hmtk.seismicity.catalogue.Catalogue, where each instance
            if the catalogue of each cluster
        """
        num_clust = np.max(vcl)
        cluster_set = []
        for clid in range(0, num_clust + 1):
            idx = np.where(vcl == clid)[0]
            cluster_cat = deepcopy(self.catalogue)
            cluster_cat.select_catalogue_events(idx)
            cluster_set.append((clid, cluster_cat))
        return dict(cluster_set)

    def within_bounding_box(self, limits):
        """
        Selects the earthquakes within a bounding box.

        :parameter limits:
            A list or a numpy array with four elements in the following order:
                - min x (longitude)
                - min y (latitude)
                - max x (longitude)
                - max y (latitude)
        :returns:
            Returns a :class:htmk.seismicity.catalogue.Catalogue` instance
        """
        is_valid = np.logical_and(
            self.catalogue.data['longitude'] >= limits[0],
            np.logical_and(self.catalogue.data['longitude'] <= limits[2],
                           np.logical_and(
                               self.catalogue.data['latitude'] >= limits[1],
                               self.catalogue.data['latitude'] <= limits[3])))
        return self.select_catalogue(is_valid)
