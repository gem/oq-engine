# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.


"""
This module contains functions and classes for reading source data from NRML
XML files and serializing the data to the OpenQuake hzrdi database.

This module contains functions and classes for reading source data from CSV
and serializing the data to the OpenQuake eqcat database.
"""


import csv
import datetime

import numpy

from openquake import java
from openquake.db import models

SRC_DATA_PKG = 'org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData'
MFD_PACKAGE = 'org.opensha.sha.magdist'

DEFAULT_GRID_SPACING = 1.0  # kilometers

# Keys: Common names for tectonic regions
# Values: A shortened version of this name to be stored in the database
# TODO: This is incomplete.
TECTONIC_REGION_MAP = {
    'Active Shallow Crust': 'active',
    'Subduction Interface': 'interface'}


def get_fault_surface(fault):
    """
    Simple and complex faults have different types of surfaces.

    The function builds the appropriate jpype java object for a given fault.

    :type fault: jpype java object of type `GEMFaultSourceData` or
        `GEMSubductionFaultSourceData` ('simple' or 'complex' faults,
        respectively)

    :returns: jpype java object of type `StirlingGriddedSurface` (for simple
        faults) or `ApproxEvenlyGriddedSurface` (for complex faults)
    """
    fault_type = fault.__javaclass__.getName()

    if fault_type == '%s.GEMFaultSourceData' % SRC_DATA_PKG:
        surface = java.jclass('StirlingGriddedSurface')(
            fault.getTrace(), fault.getDip(),
            fault.getSeismDepthUpp(), fault.getSeismDepthLow(),
            DEFAULT_GRID_SPACING)

    elif fault_type == '%s.GEMSubductionFaultSourceData' % SRC_DATA_PKG:
        surface = java.jclass('ApproxEvenlyGriddedSurface')(
            fault.getTopTrace(), fault.getBottomTrace(), DEFAULT_GRID_SPACING)

    else:
        raise ValueError("Unexpected fault type: %s" % fault_type)

    return surface


def parse_mfd(fault, mfd_java_obj):
    """
    Read a magnitude frequency distribution object, determine the type (evenly
    discretized or truncated Gutenberg-Richter), and create a Django model
    to insert into the hzrdi db.

    If the input MFD is not a supported type, a :py:exception:`ValueError` will
    be raised.

    :param fault: source data object from which we need to extract some
        information in order to properly parse the MFD object
    :type fault: jpype java object of type `GEMFaultSourceData` or
        `GEMSubductionFaultSourceData` (simple or complex fault source,
        respectively)

    :param mfd_java_obj: magnitude frequency distribution function
    :type mfd_java_obj: jpype java object of type
        `org.opensha.sha.magdist.IncrementalMagFreqDist` or
        `org.opensha.sha.magdist.GutenbergRichterMagFreqDist`

    :returns: a Django model instance for the frequency distribution
        (either :class:`openquake.db.models.MfdEvd` or
        :class:`openquake.db.models.MfdTgr`).
    """

    mfd_type = mfd_java_obj.__javaclass__.getName()

    surface = get_fault_surface(fault)
    surface_area = surface.getSurfaceArea()

    if mfd_type == '%s.IncrementalMagFreqDist' % MFD_PACKAGE:
        # 'evenly discretized' MFD
        mfd = models.MfdEvd()

        mfd.min_val = mfd_java_obj.getMinX()
        mfd.max_val = mfd_java_obj.getMaxX()
        mfd.bin_size = mfd_java_obj.getDelta()

        mfd.mfd_values = \
            [mfd_java_obj.getY(x) for x in range(mfd_java_obj.getNum())]

        # Now we can calculate the (optional) total moment rate & total
        # cumulative rate.

        # The 'total cumulative rate' and 'total moment rate' both need to be
        # normalized by the fault surface area.
        mfd.total_cumulative_rate = \
            mfd_java_obj.getTotalIncrRate() / surface_area

        mfd.total_moment_rate = \
            mfd_java_obj.getTotalMomentRate() / surface_area

    elif mfd_type == '%s.GutenbergRichterMagFreqDist' % MFD_PACKAGE:
        # 'truncated Gutenberg-Richter' MFD
        mfd = models.MfdTgr()

        mfd.min_val = mfd_java_obj.getMinX()
        mfd.max_val = mfd_java_obj.getMaxX()
        mfd.b_val = mfd_java_obj.get_bValue()

        # 'a_val' needs to be calculated:
        delta = mfd_java_obj.getDelta()
        min_mag = mfd_java_obj.getMinX() - (delta / 2)
        max_mag = mfd_java_obj.getMaxX() + (delta / 2)
        total_cumul_rate = mfd_java_obj.getTotCumRate()
        denominator = float(numpy.power(10, -(mfd.b_val * min_mag))
            - numpy.power(10, -(mfd.b_val * max_mag)))

        mfd.a_val = float(numpy.log10(total_cumul_rate / denominator))

        mfd.total_cumulative_rate = \
            mfd_java_obj.getTotCumRate() / surface_area

        mfd.total_moment_rate = \
            mfd_java_obj.getTotalMomentRate() / surface_area

    else:
        raise ValueError("Unsupported MFD type: %s" % mfd_type)

    return mfd


def parse_simple_fault_src(fault):
    """
    Given a jpype java `GEMFaultSourceData` object, parse out the necessary
    information to insert a 'simple fault' into the database.

    :param fault: simple fault object, from which we derive 3 pieces of data to
        insert into the database:
            * Magnitude Frequency Distribution
            * Simple Fault
            * Source
    :type fault: jpype java object of type `GEMFaultSourceData`

    :returns: 3-tuple of (mfd, simple_fault, source). Each item will be a
        Django model instance for the appropriate table.
    """
    def build_simple_fault_insert(fault):
        """
        Build an :class:`openquake.db.models.SimpleFault` Django
        model. See the documentation for
        :py:function:`parse_simple_fault_src` for more information.
        """
        simple_fault = models.SimpleFault()

        simple_fault.name = fault.getName()
        simple_fault.gid = fault.getID()
        simple_fault.dip = fault.getDip()
        simple_fault.upper_depth = fault.getSeismDepthUpp()
        simple_fault.lower_depth = fault.getSeismDepthLow()

        # coords are ordered as lon/lat/depth
        point_str_3d = lambda pt: \
            ' '.join([
                str(pt.getLongitude()),
                str(pt.getLatitude()),
                str(pt.getDepth())])

        coord_list = lambda point_list: \
            ', '.join([point_str_3d(point) for point in point_list])

        trace = fault.getTrace()
        trace_coords = coord_list(trace)
        simple_fault.edge = 'SRID=4326;LINESTRING(%s)' % trace_coords

        surface = get_fault_surface(fault)
        location_list = surface.getSurfacePerimeterLocsList()
        formatter = java.jclass("LocationListFormatter")(location_list)
        outline_coords = formatter.format()
        simple_fault.outline = 'SRID=4326;POLYGON((%s))' % outline_coords

        return simple_fault

    def build_source_insert(fault):
        """
        Build an :class:`openquake.db.models.Source` Django model. See
        the documentation for :py:function:`parse_simple_fault_src`
        for more information.
        """
        source = models.Source()

        # NOTE(LB): this gid will be the same as the simple_fault.gid
        # This could be horribly wrong.
        source.gid = fault.getID()
        source.name = fault.getName()
        source.si_type = 'simple'
        source.tectonic_region = \
            TECTONIC_REGION_MAP.get(fault.getTectReg().name)
        source.rake = fault.getRake()

        return source

    mfd_java_obj = fault.getMfd()

    mfd_insert = parse_mfd(fault, mfd_java_obj)
    simple_fault_insert = build_simple_fault_insert(fault)
    source_insert = build_source_insert(fault)

    return mfd_insert, simple_fault_insert, source_insert


def _table_name(model):
    """Return table name for a given model"""
    return '.'.join(model._meta.db_table.split('"."'))  # pylint: disable=W0212


def write_simple_fault(simple_data, owner_id, input_id):
    """
    Perform an insert of the given data.

    :param simple_data: 3-tuple of insert data `(mfd, simple_fault, source)`.
        Each item of the tuple is a Django model instance.

        `mfd` is an :class:`openquake.db.models.MfdEvd` or
        :class:`openquake.db.models.MfdTgr` model

        `simple_fault` is an :class:`openquake.db.models.SimpleFault` model

        `source` is an :class:`openquake.db.models.Source` model

    :param owner_id: Per the OpenQuake database standards, the tables in the
        database associated with a simple fault all have an 'owner_id' column.
        An 'owner_id' must be supplied for all new entries. (Note: The
        'owner_id' corresponds to the 'id' field of the 'admin.oq_user' table.
        We do this so we can know who created what, and also to enforce access
        restrictions on data, if necessary.
    :type owner_id: int

    :param int input_id: The database key of the uploaded input file from which
        this source was extracted. Only set (i.e. not `None`) when uploading
        via the GUI.

    :returns: List of dicts of table/record id pairs, indicating the tables and
        the primary keys of the new records. For example::
            [{'hzrdi.mfd_evd': 1},
             {'hzrdi.simple_fault': 7},
             {'hzrdi.source': 3}]
    """

    assert owner_id is not None, "owner_id should not be None"
    assert isinstance(owner_id, int), "owner_id should be an integer"
    assert len(simple_data) == 3, \
        "Expected a 3-tuple: (mfd, simple_fault, source)"

    owner = models.OqUser.objects.get(id=owner_id)
    mfd, simple_fault, source = simple_data

    mfd.owner = owner

    mfd.save()

    if isinstance(mfd, models.MfdEvd):
        simple_fault.mfd_evd = mfd
    elif isinstance(mfd, models.MfdTgr):
        simple_fault.mfd_tgr = mfd

    simple_fault.owner = owner
    simple_fault.save()

    # if an input_id is supplied, let's specify it
    # for the 'source' table entry
    if input_id:
        source.input = models.Input.objects.get(id=input_id)

    source.owner = owner
    source.simple_fault = simple_fault

    source.save()

    return [
        {_table_name(mfd): mfd.id},
        {_table_name(simple_fault): simple_fault.id},
        {_table_name(source): source.id}]


class SourceModelLoader(object):
    """
    Uses parsers (written in Java) to read a source model data from a file and
    injects the data into the appropriate database tables.
    """

    DEFAULT_MFD_BIN_WIDTH = 0.1

    # Functions for reading and transforming source model data.
    SRC_DATA_READ_FN_MAP = {
        '%s.GEMFaultSourceData' % SRC_DATA_PKG: {
            'fn': parse_simple_fault_src},
        '%s.GEMSubductionFaultSourceData' % SRC_DATA_PKG: {
            'fn': None},
        '%s.GEMAreaSourceData' % SRC_DATA_PKG: {
            'fn': None},
        '%s.GEMPointSourceData' % SRC_DATA_PKG: {
            'fn': None}}

    # Functions for writing sources to the db.
    SRC_DATA_WRITE_FN_MAP = {
        '%s.GEMFaultSourceData' % SRC_DATA_PKG: {
            'fn': write_simple_fault},
        '%s.GEMSubductionFaultSourceData' % SRC_DATA_PKG: {
            'fn': None},
        '%s.GEMAreaSourceData' % SRC_DATA_PKG: {
            'fn': None},
        '%s.GEMPointSourceData' % SRC_DATA_PKG: {
            'fn': None}}

    def __init__(self, src_model_path,
        mfd_bin_width=DEFAULT_MFD_BIN_WIDTH, owner_id=1, input_id=None):
        """
        :param src_model_path: path to a source model file
        :type src_model_path: str

        :param mfd_bin_width: Magnitude Frequency Distribution bin width
        :type mfd_bin_width: float


        :param owner_id: ID of an admin.organization entity in the database. By
            default, the default 'GEM Foundation' group will be used.
            Note(LB): This is kind of ugly and needs to be revisited later.

        :param int input_id: The database key of the uploaded input file from
            which this source was extracted. Please note that the `input_id`
            will only be supplied when uploading source model files via the
            GUI.
        """
        self.src_model_path = src_model_path
        self.mfd_bin_width = mfd_bin_width
        self.owner_id = owner_id
        self.input_id = input_id

        # Java SourceModelReader object
        self.src_reader = java.jclass('SourceModelReader')(
            self.src_model_path, self.mfd_bin_width)

    def serialize(self):
        """
        Read the source model data and serialize to the DB.
        """

        results = []

        source_data = self.src_reader.read()  # ArrayList of source data types
        for src in source_data:

            # first, figure out what type we're dealing with
            src.__javaclass__.getName()
            source_type_class = src.__javaclass__.getName()

            # now get the proper parsing function
            read = self.SRC_DATA_READ_FN_MAP[source_type_class]['fn']

            write = self.SRC_DATA_WRITE_FN_MAP[source_type_class]['fn']

            # TODO: temporary workaround, since only simple faults are
            # supported right now
            # at least one of these will be None for complex, area, and point
            # sources

            if not (read and write):
                # for now, just skip this object
                continue

            results.extend(
                write(read(src),
                      owner_id=self.owner_id,
                      input_id=self.input_id))

        return results
