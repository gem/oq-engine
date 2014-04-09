#!/usr/bin/env/python

"""
Implements sets of classes for mapping components of the focal mechanism
"""
import csv
import datetime
from math import fabs, floor, sqrt, pi
import numpy as np
import gcmt_utils as utils
from hmtk.seismicity.catalogue import Catalogue


def cmp_mat(a, b):
    """
    Sorts two matrices returning a positive or zero value
    """
    c = 0
    for x,y in zip(a.flat, b.flat):
        c = cmp(abs(x),abs(y))
        if c != 0: return c
    return c


class GCMTHypocentre(object):
    """
    Simple representation of the hypocentre
    """
    def __init__(self):
        """
        """
        self.source = None
        self.date = None
        self.time = None
        self.longitude = None
        self.latitude = None
        self.depth = None
        self.m_b = None
        self.m_s = None
        self.location = None


class GCMTCentroid(object):
    """
    Representation of a GCMT centroid
    """
    def __init__(self, reference_date, reference_time):
        """
        :param reference_date:
            Date of hypocentre as instance of :class: datetime.datetime.date
        :param reference_time:
            Time of hypocentre as instance of :class: datetime.datetime.time

        """
        self.centroid_type = None
        self.source = None
        self.time = reference_time
        self.time_error = None
        self.date = reference_date
        self.longitude = None
        self.longitude_error = None
        self.latitude = None
        self.latitude_error = None
        self.depth = None
        self.depth_error = None
        self.depth_type = None
        self.centroid_id = None

    def _get_centroid_time(self, time_diff):
        """
        Calculates the time difference between the date-time classes
        """
        source_time = datetime.datetime.combine(self.date, self.time)
        second_diff = floor(fabs(time_diff))
        microsecond_diff = int(1000. * (time_diff - second_diff))
        if time_diff < 0.:
            source_time = source_time - datetime.timedelta(
                seconds=int(second_diff), microseconds=microsecond_diff)
        else:
            source_time = source_time + datetime.timedelta(
                seconds=int(second_diff), microseconds=microsecond_diff)
        self.time = source_time.time()
        self.date = source_time.date()


class GCMTPrincipalAxes(object):
    """
    Class to represent the eigensystem of the tensor in terms of  T-, B- and P-
    plunge and azimuth
    """
    def __init__(self):
        """
        """
        self.t_axis = None
        self.b_axis = None
        self.p_axis = None
        
    def get_moment_tensor_from_principal_axes(self):
        """
        Retreives the moment tensor from the prinicpal axes
        """
        raise NotImplementedError('Moment tensor from principal axes not yet '
                                  'implemented!')


    def get_azimuthal_projection(self, height=1.0):
        """
        Returns the azimuthal projection of the tensor according to the
        method of Frohlich (2001)
        """
        raise NotImplementedError('Get azimuthal projection not yet '
                                  'implemented!')
        

class GCMTNodalPlanes(object):
    """
    Class to represent the nodal plane distribution of the tensor
    Each nodal plane is represented as a dictionary of the form:
    {'strike':, 'dip':, 'rake':}
    """
    def __init__(self):
        """
        """
        self.nodal_plane_1 = None
        self.nodal_plane_2 = None


class GCMTMomentTensor(object):
    """
    Class to represent a moment tensor and its associated methods
    """
    def __init__(self, reference_frame=None):
        """
        """
        self.tensor = None
        self.tensor_sigma = None
        self.exponent = None
        self.eigenvalues = None
        self.eigenvectors = None
        if reference_frame:
            self.ref_frame = reference_frame
        else:
            # Default to USE
            self.ref_frame = 'USE'

    def normalise_tensor(self):
        """
        Normalise the tensor by dividing it by its norm, defined such that
        np.sqrt(X:X)
        """
        self.tensor, tensor_norm = utils.normalise_tensor(self.tensor)
        return self.tensor / tensor_norm, tensor_norm

    def _to_ned(self):
        """
        Switches the reference frame to NED
        """
        if self.ref_frame is 'USE':
            # Rotate
            return utils.use_to_ned(self.tensor), \
                   utils.use_to_ned(self.tensor_sigma)
        elif self.ref_frame is 'NED':
            # Alreadt NED
            return self.tensor, self.tensor_sigma
        else:
            raise ValueError('Reference frame %s not recognised - cannot '
                             'transform to NED!' % self.ref_frame)

    def _to_use(self):
        """
        Returns a tensor in the USE reference frame
        """
        if self.ref_frame is 'NED':
            # Rotate
            return utils.ned_to_use(self.tensor), \
                   utils.ned_to_use(self.tensor_sigma)
        elif self.ref_frame is 'USE':
            # Already USE
            return self.tensor, self.tensor_sigma
        else:
            raise ValueError('Reference frame %s not recognised - cannot '
                             'transform to USE!' % self.ref_frame)

    def _to_6component(self):
        """
        Returns the unique 6-components of the tensor in USE format
        [Mrr, Mtt, Mpp, Mrt, Mrp, Mtp]
        """
        return utils.tensor_to_6component(self.tensor, self.ref_frame)

    def eigendecompose(self, normalise=False):
        """
        Performs and eigendecomposition of the tensor and orders into 
        descending eigenvalues
        """
        self.eigenvalues, self.eigenvectors = utils.eigendecompose(self.tensor,
                                                                   normalise)
        return self.eigenvalues, self.eigenvectors
    
    def get_nodal_planes(self):
        """
        Returns the nodal planes by eigendecomposition of the moment tensor
        """
        # Convert reference frame to NED
        self.tensor, self.tensor_sigma = self._to_ned()
        self.ref_frame = 'NED'
        # Eigenvalue decomposition
        # Tensor
        _, evect = utils.eigendecompose(self.tensor)
        # Rotation matrix
        _, rot_vec = utils.eigendecompose(np.matrix([[0., 0., -1],
                                                    [0., 0., 0.],
                                                    [-1., 0., 0.]]))
        rotation_matrix = (np.matrix(evect * rot_vec.T)).T
        if  np.linalg.det(rotation_matrix) < 0.:
            rotation_matrix *= -1.
        flip_dc = np.matrix([[0., 0., -1.], 
                             [0., -1., 0.],
                             [-1., 0., 0.]])
        rotation_matrices = sorted(
            [rotation_matrix, flip_dc * rotation_matrix],
            cmp=cmp_mat)
        nodal_planes = GCMTNodalPlanes()
        dip, strike, rake = [(180. / pi) * angle 
            for angle in utils.matrix_to_euler(rotation_matrices[0])]
        # 1st Nodal Plane
        nodal_planes.nodal_plane_1 = {'strike': strike % 360,
                                      'dip': dip,
                                      'rake': -rake}

        # 2nd Nodal Plane
        dip, strike, rake = [(180. / pi) * angle 
            for angle in utils.matrix_to_euler(rotation_matrices[1])]
        nodal_planes.nodal_plane_2 = {'strike': strike % 360.,
                                      'dip': dip,
                                      'rake': -rake}
        return nodal_planes

    def get_principal_axes(self):
        """
        Uses the eigendecomposition to extract the principal axes from the 
        moment tensor - returning an instance of the GCMTPrincipalAxes class
        """
        # Perform eigendecomposition - returns in order P, B, T
        _ = self.eigendecompose(normalise=True)
        principal_axes = GCMTPrincipalAxes()
        # Eigenvalues
        principal_axes.p_axis = {'eigenvalue': self.eigenvalues[0]}
        principal_axes.b_axis = {'eigenvalue': self.eigenvalues[1]}
        principal_axes.t_axis = {'eigenvalue': self.eigenvalues[2]}
        # Eigen vectors
        # 1) P axis
        azim, plun = utils.get_azimuth_plunge(self.eigenvectors[:, 0], True)
        principal_axes.p_axis['azimuth'] = azim
        principal_axes.p_axis['plunge'] = plun
        # 2) B axis
        azim, plun = utils.get_azimuth_plunge(self.eigenvectors[:, 1], True)
        principal_axes.b_axis['azimuth'] = azim
        principal_axes.b_axis['plunge'] = plun
        # 3) T axis
        azim, plun = utils.get_azimuth_plunge(self.eigenvectors[:, 2], True)
        principal_axes.t_axis['azimuth'] = azim
        principal_axes.t_axis['plunge'] = plun
        return principal_axes

class GCMTEvent(object):
    """
    Class to represent full GCMT moment tensor in ndk format
    """
    def __init__(self):
        """
        """
        self.identifier = None
        self.hypocentre = None
        self.centroid = None
        self.magnitude = None
        self.moment = None
        self.metadata = {}
        self.moment_tensor = None
        self.nodal_planes = None
        self.principal_axes = None
        self.f_clvd = None
        self.e_rel = None

    def get_f_clvd(self):
        """
        Returns the statistic f_clvd: the signed ratio of the sizes of the 
        intermediate and largest principal moments

        f_clvd = -b_axis_eigenvalue / 
                  max(|t_axis_eigenvalue|,|p_axis_eigenvalue|)
        """
        if not self.principal_axes:
            # Principal axes not yet defined for moment tensor - raises error
            raise ValueError('Principal Axes not defined!')
        
        denominator = np.max(np.array([
            fabs(self.principal_axes.t_axis['eigenvalue']),
            fabs(self.principal_axes.p_axis['eigenvalue'])
            ]))
        self.f_clvd = -self.principal_axes.b_axis['eigenvalue'] / denominator
        return self.f_clvd

    def get_relative_error(self):
        """
        Returns the relative error statistic (e_rel), defined by Frohlich &
        Davis (1999):
            e_rel = sqrt((U:U) / (M:M)) 
        where M is the moment tensor, U is the uncertainty tensor and : is the
        tensor dot product
        """
        if not self.moment_tensor:
            raise ValueError('Moment tensor not defined!')

        numer = np.tensordot(self.moment_tensor.tensor_sigma, 
                             self.moment_tensor.tensor_sigma)

        denom = np.tensordot(self.moment_tensor.tensor, 
                             self.moment_tensor.tensor)
        self.e_rel = sqrt(numer / denom)
        return self.e_rel
        
    def get_mechanism_similarity(self, mechanisms):
        """
        Returns the mechanism similarity
        """
        raise NotImplementedError('Not implemented yet!')

class GCMTCatalogue(Catalogue):
    """
    Class to hold a catalogue of moment tensors
    """
    FLOAT_ATTRIBUTE_LIST = ['second', 'timeError', 'longitude', 'latitude',
                            'SemiMajor90', 'SemiMinor90', 'ErrorStrike',
                            'depth', 'depthError', 'magnitude',
                            'sigmaMagnitude', 'moment', 'strike1', 'rake1',
                            'dip1', 'strike2', 'rake2', 'dip2',
                            'eigenvalue_b', 'azimuth_b', 'plunge_b',
                            'eigenvalue_p', 'azimuth_p', 'plunge_p',
                            'eigenvalue_t', 'azimuth_t', 'plunge_t',
                            'f_clvd', 'e_rel']

    INT_ATTRIBUTE_LIST = ['eventID', 'year', 'month', 'day', 'hour', 'minute',
                          'flag']

    STRING_ATTRIBUTE_LIST = ['Agency', 'magnitudeType', 'comment',
                             'centroidID']

    TOTAL_ATTRIBUTE_LIST = list(
        (set(FLOAT_ATTRIBUTE_LIST).union(
                set(INT_ATTRIBUTE_LIST))).union(
                    set(STRING_ATTRIBUTE_LIST)))
        
    def __init__(self, start_year=None, end_year=None):
        """
        Instantiate catalogue class
        """
        super(GCMTCatalogue, self).__init__()

        self.gcmts = []
        self.number_gcmts = None
        self.start_year = start_year
        self.end_year = end_year

        for attribute in self.TOTAL_ATTRIBUTE_LIST:
            if attribute in self.FLOAT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=float)
            elif attribute in self.INT_ATTRIBUTE_LIST:
                self.data[attribute] = np.array([], dtype=int)

    def get_number_tensors(self):
        """
        Returns number of CMTs
        """
        return len(self.gcmts)


    def select_catalogue_events(self, id0):
        '''
        Orders the events in the catalogue according to an indexing vector
        :param np.ndarray id0:
            Pointer array indicating the locations of selected events
        '''
        for key in self.data.keys():
            if isinstance(
                    self.data[key], np.ndarray) and len(self.data[key]) > 0:
                # Dictionary element is numpy array - use logical indexing
                self.data[key] = self.data[key][id0]
            elif isinstance(
                    self.data[key], list) and len(self.data[key]) > 0:
                # Dictionary element is list
                self.data[key] = [self.data[key][iloc] for iloc in id0]
            else:
                continue

        if len(self.gcmts) > 0:
            self.gcmts = [self.gcmts[iloc] for iloc in id0] 
            self.number_gcmts = self.get_number_tensors()

   
    def gcmt_to_simple_array(self, centroid_location=True):
        """
        Converts the GCMT catalogue to a simple array of 
        [ID, year, month, day, hour, minute, second, long., lat., depth, Mw,
        strike1, dip1, rake1, strike2, dip2, rake2, b-plunge, b-azimuth,
        b-eigenvalue, p-plunge, p-azimuth, p-eigenvalue, t-plunge, t-azimuth,
        t-eigenvalue, moment, f_clvd, erel]
        """
        catalogue = np.zeros([self.get_number_tensors(), 29], dtype=float) 
        for iloc, tensor in enumerate(self.gcmts):
            catalogue[iloc, 0] = iloc
            if centroid_location:
                catalogue[iloc, 1] = float(tensor.centroid.date.year)
                catalogue[iloc, 2] = float(tensor.centroid.date.month)
                catalogue[iloc, 3] = float(tensor.centroid.date.day)
                catalogue[iloc, 4] = float(tensor.centroid.time.hour)
                catalogue[iloc, 5] = float(tensor.centroid.time.minute)
                catalogue[iloc, 6] = np.round(
                    np.float(tensor.centroid.time.second) +
                    np.float(tensor.centroid.time.microsecond) / 1000000., 2)
                catalogue[iloc, 7] = tensor.centroid.longitude
                catalogue[iloc, 8] = tensor.centroid.latitude
                catalogue[iloc, 9] = tensor.centroid.depth
            else:
                catalogue[iloc, 1] = float(tensor.hypocentre.date.year)
                catalogue[iloc, 2] = float(tensor.hypocentre.date.month)
                catalogue[iloc, 3] = float(tensor.hypocentre.date.day)
                catalogue[iloc, 4] = float(tensor.hypocentre.time.hour)
                catalogue[iloc, 5] = float(tensor.hypocentre.time.minute)
                catalogue[iloc, 6] = np.round(
                    np.float(tensor.centroid.time.second) +
                    np.float(tensor.centroid.time.microsecond) / 1000000., 2)
                catalogue[iloc, 7] = tensor.hypocentre.longitude
                catalogue[iloc, 8] = tensor.hypocentre.latitude
                catalogue[iloc, 9] = tensor.hypocentre.depth
            catalogue[iloc, 10] = tensor.magnitude
            catalogue[iloc, 11] = tensor.moment
            catalogue[iloc, 12] = tensor.f_clvd
            catalogue[iloc, 13] = tensor.e_rel
            # Nodal planes
            catalogue[iloc, 14] = tensor.nodal_planes.nodal_plane_1['strike']
            catalogue[iloc, 15] = tensor.nodal_planes.nodal_plane_1['dip']
            catalogue[iloc, 16] = tensor.nodal_planes.nodal_plane_1['rake']
            catalogue[iloc, 17] = tensor.nodal_planes.nodal_plane_2['strike']
            catalogue[iloc, 18] = tensor.nodal_planes.nodal_plane_2['dip']
            catalogue[iloc, 19] = tensor.nodal_planes.nodal_plane_2['rake']
            # Principal axes
            catalogue[iloc, 20] = tensor.principal_axes.b_axis['eigenvalue'] 
            catalogue[iloc, 21] = tensor.principal_axes.b_axis['azimuth']
            catalogue[iloc, 22] = tensor.principal_axes.b_axis['plunge']
            catalogue[iloc, 23] = tensor.principal_axes.p_axis['eigenvalue']
            catalogue[iloc, 24] = tensor.principal_axes.p_axis['azimuth']
            catalogue[iloc, 25] = tensor.principal_axes.p_axis['plunge']
            catalogue[iloc, 26] = tensor.principal_axes.t_axis['eigenvalue']
            catalogue[iloc, 27] = tensor.principal_axes.t_axis['azimuth']
            catalogue[iloc, 28] = tensor.principal_axes.t_axis['plunge']
        return catalogue


#    def get_locations(self, use_centroids=True):
#        """
#        Function to return the longitude, latitude, depth and corresponding
#        uncertainties as a simple numpy arrays
#        """
#        location = np.zeros([self.get_number_tensors(), 3], dtype=float)
#        location_uncertainty = np.zeros([self.get_number_tensors(), 3], dtype=float)
#         
#        for iloc, tensor in enumerate(self.gcmts):
#            if use_centroids:
#                # Use centroids
#                location[iloc, 0] = tensor.centroid.longitude
#                location[iloc, 1] = tensor.centroid.latitude
#                location[iloc, 2] = tensor.centroid.depth
#                location_uncertainty[iloc, 0] = \
#                    tensor.centroid.longitude_error
#                location_uncertainty[iloc, 1] = \
#                    tensor.centroid.latitude_error
#                location_uncertainty[iloc, 2] = \
#                    tensor.centroid.depth_error
#            else:
#                # Use hypocentres
#                location[iloc, 0] = tensor.hypocentre.longitude
#                location[iloc, 1] = tensor.hypocentre.latitude
#                location[iloc, 2] = tensor.hypocentre.depth
#                # Uncertainties set to zero
#
#        return location, location_uncertainty
#


#    def serialise_to_hmtk_csv(self, filename, centroid_location=True):
#        """
#        Serialise the catalogue to a simple csv format, designed for 
#        comptibility with the GEM Hazard Modeller's Toolkit
#        """
#        header_list = ['eventID', 'Agency', 'year', 'month', 'day', 'hour', 
#                   'minute', 'second', 'timeError', 'longitude', 'latitude',
#                   'SemiMajor90', 'SemiMinor90', 'ErrorStrike', 'depth', 
#                   'depthError', 'magnitude', 'sigmaMagnitude']
#        fid = open(filename, 'wt')
#        writer = csv.DictWriter(fid, fieldnames=header_list)
#        headers = dict((header, header) for header in header_list)
#        writer.writerow(headers)
#        print 'Writing to simple csv format ...'
#        for iloc, tensor in enumerate(self.gcmts):
#            # Generic Data
#            cmt_dict = {'eventID': iloc + 100000,
#                        'Agency': 'GCMT',
#                        'SemiMajor90': None,
#                        'SemiMinor90': None,
#                        'ErrorStrike': None,
#                        'magnitude': tensor.magnitude,
#                        'sigmaMagnitude': None,
#                        'depth': None,
#                        'depthError': None}
#
#            if centroid_location:
#                # Time and location come from centroid
#                cmt_dict['year'] = tensor.centroid.date.year
#                cmt_dict['month'] = tensor.centroid.date.month
#                cmt_dict['day'] = tensor.centroid.date.day
#                cmt_dict['hour'] = tensor.centroid.time.hour
#                cmt_dict['minute'] = tensor.centroid.time.minute
#                cmt_dict['second'] = np.round(
#                    np.float(tensor.centroid.time.second) +
#                    np.float(tensor.centroid.time.microsecond) / 1000000., 2)
#                cmt_dict['timeError'] = tensor.centroid.time_error
#                cmt_dict['longitude'] = tensor.centroid.longitude
#                cmt_dict['latitude'] = tensor.centroid.latitude
#                cmt_dict['depth'] = tensor.centroid.depth
#                cmt_dict['depthError'] = tensor.centroid.depth_error
#            else:
#                # Time and location come from hypocentre
#                cmt_dict['year'] = tensor.hypocentre.date.year
#                cmt_dict['month'] = tensor.hypocentre.date.month
#                cmt_dict['day'] = tensor.hypocentre.date.day
#                cmt_dict['hour'] = tensor.hypocentre.time.hour
#                cmt_dict['minute'] = tensor.hypocentre.time.minute
#                cmt_dict['second'] = np.round(
#                    np.float(tensor.hypocentre.time.second) + 
#                    np.float(tensor.hypocentre.time.microsecond) / 1000000., 2)
#                cmt_dict['timeError'] = None
#                cmt_dict['longitude'] = tensor.hypocentre.longitude
#                cmt_dict['latitude'] = tensor.hypocentre.latitude
#                cmt_dict['depth'] = tensor.hypocentre.depth
#                cmt_dict['depthError'] = None
#            writer.writerow(cmt_dict)
#        fid.close()
#        print 'done!'
#
#    def sum_tensor_set(self, selection, weight=None):
#        """
#        Function to sum a subset of moment tensors from a list of tensors
#        :param list selection:
#            Indices of selected tensors from within the list
#        """
#        if isinstance(weight, list) or isinstance(weight, np.ndarray):
#            assert len(weight) == len(selection)
#        else:
#            weight = np.ones(len(selection), dtype=float)
#
#        resultant = GCMTEvent()
#        resultant.moment_tensor = GCMTMomentTensor()
#        resultant.moment_tensor.tensor = 0.
#        resultant.centroid = GCMTCentroid(None, None)
#        for iloc, locn in enumerate(selection):
#            # Normalise input tensor
#            target = self.gcmts[locn]
#            target = weight[iloc] * \
#                (target.moment_tensor.normalise_tensor())[0]
#            # Sum tensor
#            resultant.moment_tensor.tensor += target
#
#            # Update resultant centroid
#            resultant.centroid.longitude += (target.centroid.longitude * 
#                                             weight[iloc])
#            resultant.centroid.latitude += (target.centroid.latitude * 
#                                            weight[iloc])
#            resultant.centroid.depth += (target.centroid.depth * weight[iloc])
#        return resultant
#
#    def write_to_gmt_format(self, filename, add_text=False):
#        """
#        Exports the catalogue to a GMT format (for use with the "Sc" flag).
#        :param str filename:
#            Name of file
#
#
#        "Sc" flag requires "Long, Lat, Depth, Stike, Dip, Rake, Strike, Dip,
#                            Rake, Mantissa, Exponent, LongPlot, LatPlot, Text"
#        """
#        fid = open(filename, 'wt')
#
#        for iloc, gcmt in enumerate(self.gcmts):
#            mantissa = gcmt.moment / (10. ** 
#                                      float(gcmt.moment_tensor.exponent))
#            exponent = gcmt.moment_tensor.exponent + 7.
#            if add_text:
#                print >> fid, "%9.4f %9.4f %9.4f %6.1f %6.1f %6.1f %6.1f "\
#                "%6.1f %6.1f %7.2f %5.1f %9.4f %9.4f %s" %(
#                    gcmt.centroid.longitude,
#                    gcmt.centroid.latitude,
#                    gcmt.centroid.depth,
#                    gcmt.nodal_planes.nodal_plane_1['strike'],
#                    gcmt.nodal_planes.nodal_plane_1['dip'],
#                    gcmt.nodal_planes.nodal_plane_1['rake'],
#                    gcmt.nodal_planes.nodal_plane_2['strike'],
#                    gcmt.nodal_planes.nodal_plane_2['dip'],
#                    gcmt.nodal_planes.nodal_plane_2['rake'],
#                    mantissa,
#                    exponent,
#                    gcmt.centroid.longitude,
#                    gcmt.centroid.latitude,
#                    gcmt.identifier.strip())
#            else:
#                print >> fid, "%9.4f %9.4f %9.4f %6.1f %6.1f %6.1f %6.1f"\
#                "%6.1f %6.1f %7.2f %5.1f %9.4f %9.4f" % (
#                    gcmt.centroid.longitude,
#                    gcmt.centroid.latitude,
#                    gcmt.centroid.depth,
#                    gcmt.nodal_planes.nodal_plane_1['strike'],
#                    gcmt.nodal_planes.nodal_plane_1['dip'],
#                    gcmt.nodal_planes.nodal_plane_1['rake'],
#                    gcmt.nodal_planes.nodal_plane_2['strike'],
#                    gcmt.nodal_planes.nodal_plane_2['dip'],
#                    gcmt.nodal_planes.nodal_plane_2['rake'],
#                    mantissa,
#                    exponent,
#                    gcmt.centroid.longitude,
#                    gcmt.centroid.latitude)
#        fid.close()

