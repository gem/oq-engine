# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (C) 2010-2025 GEM Foundation, G. Weatherill, M. Pagani,
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
# The software is NOT distributed as part of GEM’s OpenQuake suite
# (https://www.globalquakemodel.org/tools-products) and must be considered as a
# separate entity. The software provided herein is designed and implemented
# by scientific staff. It is not developed to the design standards, nor
# subject to same level of critical review by professional software
# developers, as GEM’s OpenQuake software suite.
#
# Feedback and contribution to the software is welcome, and can be
# directed to the hazard scientific staff of the GEM Model Facility
# (hazard@globalquakemodel.org).
#
# The Hazard Modeller's Toolkit (openquake.hmtk) is therefore distributed
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
# for more details.
#
# The GEM Foundation, and the authors of the software, assume no
# liability for use of the software.


"""
Parser for moment tensor catalogue in GCMT format into a set of GCMT classes
"""
import re
import datetime
import numpy as np
from math import floor, fabs
from linecache import getlines

import openquake.hmtk.seismicity.gcmt_utils as utils
from openquake.hmtk.seismicity.gcmt_catalogue import (
    GCMTHypocentre,
    GCMTCentroid,
    GCMTPrincipalAxes,
    GCMTNodalPlanes,
    GCMTMomentTensor,
    GCMTEvent,
    GCMTCatalogue,
)


def _read_date_from_string(str1):
    """
    Reads the date from a string in the format YYYY/MM/DD and returns
    :class: datetime.date
    """
    full_date = [int(x) for x in str1.split("/")]
    return datetime.date(full_date[0], full_date[1], full_date[2])


def _read_time_from_string(str1):
    """
    Reads the time from a string in the format HH:MM:SS.S and returns
    :class: datetime.time
    """
    full_time = [float(x) for x in str1.split(":")]
    hour = int(full_time[0])
    minute = int(full_time[1])
    if full_time[2] > 59.99:
        minute += 1
        second = 0
    else:
        second = int(full_time[2])
    microseconds = int((full_time[2] - floor(full_time[2])) * 1000000)
    return datetime.time(hour, minute, second, microseconds)


def _read_moment_tensor_from_ndk_string(ndk_string, system="USE"):
    """
    Reads the moment tensor from the ndk_string representation
    ndk_string = [Mrr, sigMrr, Mtt, sigMtt, Mpp, sigMpp, Mrt, sigMrt, Mrp,
                  sigMrp, Mtp, sigMtp]
    Output tensors should be of format:
        expected = [[Mtt, Mtp, Mtr],
                    [Mtp, Mpp, Mpr],
                    [Mtr, Mpr, Mrr]]
        sigma = [[sigMtt, sigMtp, sigMtr],
                 [sigMtp, sigMpp, sigMpr],
                 [sigMtr, sigMpr, sigMrr]]
    Exponent returned in Nm

    :param str ndk_string:
        String of data in ndk format (line 4 of event)
    :param str system:
        Reference frame of tensor Up, South, East {USE} or North, East, Down
        (NED)
    """
    exponent = float(ndk_string[0:2]) - 7.0
    mkr = np.array([2, 9, 15], dtype=int)
    vector = []
    for i in range(0, 6):
        vector.extend(
            [
                float(ndk_string[mkr[0] : mkr[1]]),
                float(ndk_string[mkr[1] : mkr[2]]),
            ]
        )
        mkr = mkr + 13
    vector = np.array(vector)
    mrr, mtt, mpp, mrt, mrp, mtp = tuple(vector[np.arange(0, 12, 2)])
    sig_mrr, sig_mtt, sig_mpp, sig_mrt, sig_mrp, sig_mtp = tuple(
        vector[np.arange(1, 13, 2)]
    )

    tensor = utils.COORD_SYSTEM[system](mrr, mtt, mpp, mrt, mrp, mtp)
    tensor = (10.0**exponent) * tensor

    sigma = utils.COORD_SYSTEM[system](
        sig_mrr, sig_mtt, sig_mpp, sig_mrt, sig_mrp, sig_mtp
    )
    sigma = (10.0**exponent) * sigma

    return tensor, sigma, exponent


class ParseNDKtoGCMT(object):
    """
    Implements the parser to read a file in ndk format to the GCMT catalogue
    """

    def __init__(self, filename):
        """
        :param str filename:
            Name of the catalogue file in ndk format
        """
        self.filename = filename
        self.catalogue = GCMTCatalogue()

    def read_file(self, start_year=None, end_year=None, use_centroid=False):
        """
        Reads the file
        """
        raw_data = getlines(self.filename)
        num_lines = len(raw_data)
        if ((float(num_lines) / 5.0) - float(num_lines / 5)) > 1e-9:
            raise IOError(
                "GCMT represented by 5 lines - number in file not"
                " a multiple of 5!"
            )
        self.catalogue.number_gcmts = num_lines // 5
        self.catalogue.gcmts = [None] * self.catalogue.number_gcmts
        # Pre-allocates list
        id0 = 0
        print("Parsing catalogue ...")
        for iloc in range(0, self.catalogue.number_gcmts):
            self.catalogue.gcmts[iloc] = self.read_ndk_event(raw_data, id0)
            id0 += 5
        print(
            "complete. Contains %s moment tensors"
            % self.catalogue.get_number_tensors()
        )
        if not start_year:
            min_years = []
            min_years = [
                cent.centroid.date.year for cent in self.catalogue.gcmts
            ]
            self.catalogue.start_year = np.min(min_years)

        if not end_year:
            max_years = []
            max_years = [
                cent.centroid.date.year for cent in self.catalogue.gcmts
            ]
            self.catalogue.end_year = np.max(max_years)
        self.to_hmtk(use_centroid)
        return self.catalogue

    def read_ndk_event(self, raw_data, id0):
        """
        Reads a 5-line batch of data into a set of GCMTs
        """
        gcmt = GCMTEvent()
        # Get hypocentre
        ndkstring = raw_data[id0].rstrip("\n")
        gcmt.hypocentre = self._read_hypocentre_from_ndk_string(ndkstring)

        # GCMT metadata
        ndkstring = raw_data[id0 + 1].rstrip("\n")
        gcmt = self._get_metadata_from_ndk_string(gcmt, ndkstring)

        # Get Centroid
        ndkstring = raw_data[id0 + 2].rstrip("\n")
        gcmt.centroid = self._read_centroid_from_ndk_string(
            ndkstring, gcmt.hypocentre
        )

        # Get Moment Tensor
        ndkstring = raw_data[id0 + 3].rstrip("\n")
        gcmt.moment_tensor = self._get_moment_tensor_from_ndk_string(ndkstring)

        # Get principal axes
        ndkstring = raw_data[id0 + 4].rstrip("\n")
        gcmt.principal_axes = self._get_principal_axes_from_ndk_string(
            ndkstring[3:48], exponent=gcmt.moment_tensor.exponent
        )

        # Get Nodal Planes
        gcmt.nodal_planes = self._get_nodal_planes_from_ndk_string(
            ndkstring[57:]
        )

        # Get Moment and Magnitude
        (
            gcmt.moment,
            gcmt.version,
            gcmt.magnitude,
        ) = self._get_moment_from_ndk_string(
            ndkstring, gcmt.moment_tensor.exponent
        )
        return gcmt

    def to_hmtk(self, use_centroid=True):
        """
        Convert the content of the GCMT catalogue to a HMTK
        catalogue.
        """
        self._preallocate_data_dict()
        for iloc, gcmt in enumerate(self.catalogue.gcmts):
            self.catalogue.data["eventID"][iloc] = iloc
            if use_centroid:
                self.catalogue.data["year"][iloc] = gcmt.centroid.date.year
                self.catalogue.data["month"][iloc] = gcmt.centroid.date.month
                self.catalogue.data["day"][iloc] = gcmt.centroid.date.day
                self.catalogue.data["hour"][iloc] = gcmt.centroid.time.hour
                self.catalogue.data["minute"][iloc] = gcmt.centroid.time.minute
                self.catalogue.data["second"][iloc] = gcmt.centroid.time.second
                self.catalogue.data["longitude"][
                    iloc
                ] = gcmt.centroid.longitude
                self.catalogue.data["latitude"][iloc] = gcmt.centroid.latitude
                self.catalogue.data["depth"][iloc] = gcmt.centroid.depth
            else:
                self.catalogue.data["year"][iloc] = gcmt.hypocentre.date.year
                self.catalogue.data["month"][iloc] = gcmt.hypocentre.date.month
                self.catalogue.data["day"][iloc] = gcmt.hypocentre.date.day
                self.catalogue.data["hour"][iloc] = gcmt.hypocentre.time.hour
                self.catalogue.data["minute"][
                    iloc
                ] = gcmt.hypocentre.time.minute
                self.catalogue.data["second"][
                    iloc
                ] = gcmt.hypocentre.time.second
                self.catalogue.data["longitude"][
                    iloc
                ] = gcmt.hypocentre.longitude
                self.catalogue.data["latitude"][
                    iloc
                ] = gcmt.hypocentre.latitude
                self.catalogue.data["depth"][iloc] = gcmt.hypocentre.depth
            # Moment, magnitude and relative errors
            self.catalogue.data["moment"][iloc] = gcmt.moment
            self.catalogue.data["magnitude"][iloc] = gcmt.magnitude
            self.catalogue.data["f_clvd"][iloc] = gcmt.f_clvd
            self.catalogue.data["e_rel"][iloc] = gcmt.e_rel
            self.catalogue.data["centroidID"][iloc] = gcmt.identifier
            # Nodal planes
            self.catalogue.data["strike1"][
                iloc
            ] = gcmt.nodal_planes.nodal_plane_1["strike"]
            self.catalogue.data["dip1"][
                iloc
            ] = gcmt.nodal_planes.nodal_plane_1["dip"]
            self.catalogue.data["rake1"][
                iloc
            ] = gcmt.nodal_planes.nodal_plane_1["rake"]
            self.catalogue.data["strike2"][
                iloc
            ] = gcmt.nodal_planes.nodal_plane_2["strike"]
            self.catalogue.data["dip2"][
                iloc
            ] = gcmt.nodal_planes.nodal_plane_2["dip"]
            self.catalogue.data["rake2"][
                iloc
            ] = gcmt.nodal_planes.nodal_plane_2["rake"]
            # Principal axes
            self.catalogue.data["eigenvalue_b"][
                iloc
            ] = gcmt.principal_axes.b_axis["eigenvalue"]
            self.catalogue.data["azimuth_b"][
                iloc
            ] = gcmt.principal_axes.b_axis["azimuth"]
            self.catalogue.data["plunge_b"][iloc] = gcmt.principal_axes.b_axis[
                "plunge"
            ]
            self.catalogue.data["eigenvalue_p"][
                iloc
            ] = gcmt.principal_axes.p_axis["eigenvalue"]
            self.catalogue.data["azimuth_p"][
                iloc
            ] = gcmt.principal_axes.p_axis["azimuth"]
            self.catalogue.data["plunge_p"][iloc] = gcmt.principal_axes.p_axis[
                "plunge"
            ]
            self.catalogue.data["eigenvalue_t"][
                iloc
            ] = gcmt.principal_axes.t_axis["eigenvalue"]
            self.catalogue.data["azimuth_t"][
                iloc
            ] = gcmt.principal_axes.t_axis["azimuth"]
            self.catalogue.data["plunge_t"][iloc] = gcmt.principal_axes.t_axis[
                "plunge"
            ]
        return self.catalogue

    def _preallocate_data_dict(self):
        """ """
        nvals = self.catalogue.get_number_tensors()
        for key in self.catalogue.TOTAL_ATTRIBUTE_LIST:
            if key in self.catalogue.STRING_ATTRIBUTE_LIST:
                self.catalogue.data[key] = [None for i in range(0, nvals)]
            elif key in self.catalogue.INT_ATTRIBUTE_LIST:
                self.catalogue.data[key] = np.zeros(nvals, dtype=int)
            else:
                self.catalogue.data[key] = np.zeros(nvals, dtype=float)

    def _read_hypocentre_from_ndk_string(self, linestring):
        """
        Reads the hypocentre data from the ndk string to return an
        instance of the GCMTHypocentre class
        """
        hypo = GCMTHypocentre()
        hypo.source = linestring[0:4]
        hypo.date = _read_date_from_string(linestring[5:15])
        hypo.time = _read_time_from_string(linestring[16:26])
        hypo.latitude = float(linestring[27:33])
        hypo.longitude = float(linestring[34:41])
        hypo.depth = float(linestring[42:47])
        magnitudes = [float(x) for x in linestring[48:55].split(" ")]
        if magnitudes[0] > 0.0:
            hypo.m_b = magnitudes[0]
        if magnitudes[1] > 0.0:
            hypo.m_s = magnitudes[1]
        hypo.location = linestring[56:]
        return hypo

    def _get_metadata_from_ndk_string(self, gcmt, ndk_string):
        """
        Reads the GCMT metadata from line 2 of the ndk batch
        """
        gcmt.identifier = ndk_string[:16]
        inversion_data = re.split("[A-Z:]+", ndk_string[17:61])
        gcmt.metadata["BODY"] = [float(x) for x in inversion_data[1].split()]
        gcmt.metadata["SURFACE"] = [
            float(x) for x in inversion_data[2].split()
        ]
        gcmt.metadata["MANTLE"] = [float(x) for x in inversion_data[3].split()]
        further_meta = re.split("[: ]+", ndk_string[62:])
        gcmt.metadata["CMT"] = int(further_meta[1])
        gcmt.metadata["FUNCTION"] = {
            "TYPE": further_meta[2],
            "DURATION": float(further_meta[3]),
        }
        return gcmt

    def _read_centroid_from_ndk_string(self, ndk_string, hypocentre):
        """
        Reads the centroid data from the ndk string to return an
        instance of the GCMTCentroid class
        :param str ndk_string:
            String of data (line 3 of ndk format)
        :param hypocentre:
            Instance of the GCMTHypocentre class
        """
        centroid = GCMTCentroid(hypocentre.date, hypocentre.time)
        centroid.centroid_type = ndk_string[0:8]
        time_diff = float(ndk_string[10:18])
        if fabs(time_diff) > 1e-6:
            centroid._get_centroid_time(time_diff)
        centroid.time_error = float(ndk_string[19:22])
        centroid.latitude = float(ndk_string[22:29])
        centroid.latitude_error = float(ndk_string[31:34])
        centroid.longitude = float(ndk_string[35:42])
        centroid.latitude_error = float(ndk_string[44:47])
        centroid.depth = float(ndk_string[48:53])
        centroid.depth_error = float(ndk_string[54:58])
        centroid.depth_type = ndk_string[59:63]
        centroid.centroid_id = ndk_string[64:]
        return centroid

    def _get_moment_tensor_from_ndk_string(self, ndk_string):
        """
        Reads the moment tensor from the ndk_string and returns an instance of
        the GCMTMomentTensor class.
        By default the ndk format uses the Up, South, East (USE) reference
        system.
        """
        moment_tensor = GCMTMomentTensor("USE")
        tensor_data = _read_moment_tensor_from_ndk_string(ndk_string, "USE")
        moment_tensor.tensor = tensor_data[0]
        moment_tensor.tensor_sigma = tensor_data[1]
        moment_tensor.exponent = tensor_data[2]
        return moment_tensor

    def _get_principal_axes_from_ndk_string(self, ndk_string, exponent):
        """
        Gets the principal axes from the ndk string and returns an instance
        of the GCMTPrincipalAxes class
        """
        axes = GCMTPrincipalAxes()
        # The principal axes is defined in characters 3:48 of the 5th line
        exponent = 10.0**exponent
        axes.t_axis = {
            "eigenvalue": exponent * float(ndk_string[0:8]),
            "plunge": float(ndk_string[8:11]),
            "azimuth": float(ndk_string[11:15]),
        }

        axes.b_axis = {
            "eigenvalue": exponent * float(ndk_string[15:23]),
            "plunge": float(ndk_string[23:26]),
            "azimuth": float(ndk_string[26:30]),
        }

        axes.p_axis = {
            "eigenvalue": exponent * float(ndk_string[30:38]),
            "plunge": float(ndk_string[38:41]),
            "azimuth": float(ndk_string[41:]),
        }
        return axes

    def _get_nodal_planes_from_ndk_string(self, ndk_string):
        """
        Reads the nodal plane information (represented by 5th line [57:] of the
        tensor representation) and returns an instance of the GCMTNodalPlanes
        class
        """
        planes = GCMTNodalPlanes()
        planes.nodal_plane_1 = {
            "strike": float(ndk_string[0:3]),
            "dip": float(ndk_string[3:6]),
            "rake": float(ndk_string[6:11]),
        }
        planes.nodal_plane_2 = {
            "strike": float(ndk_string[11:15]),
            "dip": float(ndk_string[15:18]),
            "rake": float(ndk_string[18:]),
        }
        return planes

    def _get_moment_from_ndk_string(self, ndk_string, exponent):
        """
        Returns the moment and the moment magnitude
        """
        moment = float(ndk_string[49:56]) * (10.0**exponent)
        version = ndk_string[:3]
        magnitude = utils.moment_magnitude_scalar(moment)
        return moment, version, magnitude
