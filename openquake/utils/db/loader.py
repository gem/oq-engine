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

from openquake import java, xml
from openquake.db import models
from openquake.utils import db

SRC_DATA_PKG = 'org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData'
MFD_PACKAGE = 'org.opensha.sha.magdist'

DEFAULT_GRID_SPACING = 1.0  # kilometers

# Keys: Common names for tectonic regions
# Values: A shortened version of this name to be stored in the database
# TODO: This is incomplete.
TECTONIC_REGION_MAP = {
    'Active Shallow Crust': 'active',
    'Subduction Interface': 'interface'}
TABLE_MAP = {
    'hzrdi.mfd_evd': models.MfdEvd,
    'hzrdi.mfd_tgr': models.MfdTgr,
    'hzrdi.simple_fault': models.SimpleFault,
    'hzrdi.source': models.Source,
}


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
    discretized or truncated Gutenberg-Richter), and create a dict containing
    the necessary data to insert into the hzrdi db.

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

    :returns: Dict values to be inserted into either the mfd_evd or mfd_tgr
        table. Values are keyed by column name. The dict will then be wrapped
        in another dict with two keys: 'table' and 'data'. The value of 'table'
        is a string representing the table name (including the tablespace). For
        example::

            {'table': 'hzrdi.mfd_evd',
             'data': <dict of column name/value pairs>}

        The reason we add this additional wrapper is so we can generically do
        database inserts; the table name allows retrieving the appropriate
        Django model, which can then be used to perform the insert.
    """

    mfd_type = mfd_java_obj.__javaclass__.getName()

    surface = get_fault_surface(fault)
    surface_area = surface.getSurfaceArea()

    if mfd_type == '%s.IncrementalMagFreqDist' % MFD_PACKAGE:
        # 'evenly discretized' MFD
        mfd = db.MFD_EVD.copy()

        # let the db set the default mag type
        mfd.pop('magnitude_type')

        mfd['min_val'] = mfd_java_obj.getMinX()
        mfd['max_val'] = mfd_java_obj.getMaxX()
        mfd['bin_size'] = mfd_java_obj.getDelta()

        mfd['mfd_values'] = \
            [mfd_java_obj.getY(x) for x in range(mfd_java_obj.getNum())]

        # Now we can calculate the (optional) total moment rate & total
        # cumulative rate.

        # The 'total cumulative rate' and 'total moment rate' both need to be
        # normalized by the fault surface area.
        mfd['total_cumulative_rate'] = \
            mfd_java_obj.getTotalIncrRate() / surface_area

        mfd['total_moment_rate'] = \
            mfd_java_obj.getTotalMomentRate() / surface_area

        # wrap the insert data in dict keyed by table name
        mfd_insert = {'table': '%s.mfd_evd' % db.HZRDI_TS, 'data': mfd}

    elif mfd_type == '%s.GutenbergRichterMagFreqDist' % MFD_PACKAGE:
        # 'truncated Gutenberg-Richter' MFD
        mfd = db.MFD_TGR.copy()

        # let the db set the default mag type
        mfd.pop('magnitude_type')

        mfd['min_val'] = mfd_java_obj.getMinX()
        mfd['max_val'] = mfd_java_obj.getMaxX()
        mfd['b_val'] = mfd_java_obj.get_bValue()

        # 'a_val' needs to be calculated:
        delta = mfd_java_obj.getDelta()
        min_mag = mfd_java_obj.getMinX() - (delta / 2)
        max_mag = mfd_java_obj.getMaxX() + (delta / 2)
        total_cumul_rate = mfd_java_obj.getTotCumRate()
        denominator = float(numpy.power(10, -(mfd['b_val'] * min_mag))
            - numpy.power(10, -(mfd['b_val'] * max_mag)))

        mfd['a_val'] = float(numpy.log10(total_cumul_rate / denominator))

        mfd['total_cumulative_rate'] = \
            mfd_java_obj.getTotCumRate() / surface_area

        mfd['total_moment_rate'] = \
            mfd_java_obj.getTotalMomentRate() / surface_area

        mfd_insert = {'table': '%s.mfd_tgr' % db.HZRDI_TS, 'data': mfd}

    else:
        raise ValueError("Unsupported MFD type: %s" % mfd_type)

    return mfd_insert


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

    :returns: 3-tuple of (mfd, simple_fault, source). Each item will be a dict
        with the following keys:
            * table
                name of the table to which the data should be inserted;
                includes the tablespace
            * data
                dict containing keys corresponding to column names; values are
                set to the data which is to be inserted

        Example return value::
            ({'table': 'hzrdi.mfd_evd', 'data': {
                'max_val': 6.9500000000000002,
                'total_cumulative_rate': 1.8988435199999998e-05,
                'min_val': 6.5499999999999998,
                'bin_size': 0.10000000000000009,
                'mfd_values': [
                    0.0010614989, 0.00088291626999999998,
                    0.00073437776999999999, 0.00061082879999999995,
                    0.00050806530000000003],
                'total_moment_rate': 281889786038447.25,
                'owner_id': None}},
            {'table': 'hzrdi.simple_fault', 'data': {
                'name': u'Mount Diablo Thrust',
                'upper_depth': 8.0,
                'mgf_evd_id': None,
                'mfd_tgr_id': None,
                'edge': <WKTSpatialElement at 0x107228a50; ... >,
                'lower_depth': 13.0,
                'gid': u'src01',
                'owner_id': None,
                'dip': 38.0,
                'description': None}},
            {'table': 'hzrdi.source', 'data': {
                'r_depth_distr_id': None,
                'name': u'Mount Diablo Thrust',
                'tectonic_region': 'active',
                'rake': 90.0,
                'si_type': 'simple',
                'gid': u'src01',
                'simple_fault_id': None,
                'owner_id': None,
                'hypocentral_depth': None,
                'description': None}})
    """
    def build_simple_fault_insert(fault):
        """
        Build up the simple fault dict. See the documentation for
        :py:function:`parse_simple_fault_src` for more information.
        """
        simple_fault = db.SIMPLE_FAULT.copy()
        simple_fault['name'] = fault.getName()
        simple_fault['gid'] = fault.getID()
        simple_fault['dip'] = fault.getDip()
        simple_fault['upper_depth'] = fault.getSeismDepthUpp()
        simple_fault['lower_depth'] = fault.getSeismDepthLow()

        trace = fault.getTrace()

        # coords are ordered as lon/lat/depth
        point_str_3d = lambda pt: \
            ' '.join([
                str(pt.getLongitude()),
                str(pt.getLatitude()),
                str(pt.getDepth())])

        coord_list = lambda point_list: \
            ', '.join([point_str_3d(point) for point in point_list])

        trace_coords = coord_list(trace)

        simple_fault['edge'] = 'SRID=4326;LINESTRING(%s)' % trace_coords

        surface = get_fault_surface(fault)

        location_list = surface.getSurfacePerimeterLocsList()

        formatter = java.jclass("LocationListFormatter")(location_list)

        outline_coords = formatter.format()

        simple_fault['outline'] = 'SRID=4326;POLYGON((%s))' % outline_coords

        simple_fault_insert = {
            'table': '%s.simple_fault' % db.HZRDI_TS,
            'data': simple_fault}

        return simple_fault_insert

    def build_source_insert(fault):
        """
        Build up the source dict. See the documentation for
        :py:function:`parse_simple_fault_src` for more information.
        """
        source = db.SOURCE.copy()

        # NOTE(LB): this gid will be the same as the simple_fault.gid
        # This could be horribly wrong.
        source['gid'] = fault.getID()
        source['name'] = fault.getName()
        source['si_type'] = 'simple'
        source['tectonic_region'] = \
            TECTONIC_REGION_MAP.get(fault.getTectReg().name)
        source['rake'] = fault.getRake()

        source_insert = {
            'table': '%s.source' % db.HZRDI_TS,
            'data': source}

        return source_insert

    mfd_java_obj = fault.getMfd()

    mfd_insert = parse_mfd(fault, mfd_java_obj)
    simple_fault_insert = build_simple_fault_insert(fault)
    source_insert = build_source_insert(fault)

    return mfd_insert, simple_fault_insert, source_insert


def parse_complex_fault_src(_source_data):
    """
    :param _source_data:
    :type _source_data: jpype-wrapped java object of type
        `GEMSubductionFaultSourceData`
    """
    raise NotImplementedError


def parse_area_src(_source_data):
    """
    :param _source_data:
    :type _source_data: jpype-wrapped java object of type `GEMAreaSourceData`
    """
    raise NotImplementedError


def parse_point_src(_source_data):
    """
    :param _source_data:
    :type _source_data: jpype-wrapped java object of type `GEMPointSourceData`
    """
    raise NotImplementedError


def write_simple_fault(simple_data, owner_id, input_id):
    """
    Perform an insert of the given data.

    :param simple_data: 3-tuple of insert data (mfd, simple_fault, source). See
        the documentation for :py:function:`parse_simple_fault_src` for more
        information on the structure of this input.

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
    def do_insert(insert):
        """
        Set the owner_id for the record, insert the data, and return the id of
        the new record.

        This assumes one only record insertion.

        :param insert: the data to be inserted (a dict keyed by column names)
        :type insert: dict

        :returns: primary key of the new record
        """
        assert owner_id is not None, "owner_id should not be None"
        assert isinstance(owner_id, int), "owner_id should be an integer"

        table = TABLE_MAP[insert['table']]

        data = insert['data']

        # fix owner reference
        data.pop('owner_id')
        data['owner'] = models.OqUser.objects.get(id=owner_id)

        item = table(**data)
        item.save()

        return item.id

    assert len(simple_data) == 3, \
        "Expected a 3-tuple: (mfd, simple_fault, source)"

    mfd, simple_fault, source = simple_data

    mfd_id = do_insert(mfd)

    # fix mfd references
    simple_fault['data'].pop('mgf_evd_id', None)
    simple_fault['data'].pop('mfd_tgr_id', None)

    if mfd['table'] == '%s.mfd_evd' % db.HZRDI_TS:
        simple_fault['data']['mfd_evd'] = models.MfdEvd.objects.get(id=mfd_id)
    elif mfd['table'] == '%s.mfd_tgr' % db.HZRDI_TS:
        simple_fault['data']['mfd_tgr'] = models.MfdTgr.objects.get(id=mfd_id)

    simple_id = do_insert(simple_fault)

    source['data']['simple_fault_id'] = simple_id

    # if an input_id is supplied, let's specify it
    # for the 'source' table entry
    if input_id:
        source['data']['input_id'] = input_id

    source_id = do_insert(source)

    return [
        {mfd['table']: mfd_id},
        {simple_fault['table']: simple_id},
        {source['table']: source_id}]


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
            'fn': parse_complex_fault_src},
        '%s.GEMAreaSourceData' % SRC_DATA_PKG: {
            'fn': parse_area_src},
        '%s.GEMPointSourceData' % SRC_DATA_PKG: {
            'fn': parse_point_src}}

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
        java.jvm().java.lang.System.setProperty(
            "openquake.nrml.schema", xml.nrml_schema_file())
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
                write(read(src), owner_id=self.owner_id,
                input_id=self.input_id))

        return results


class CsvModelLoader(object):
    """
        Csv Model Loader which gets data from a particular CSV source and
        "serializes" the data to the database
    """
    def __init__(self, src_model_path):
        """
            :param src_model_path: path to a source model file
            :type src_model_path: str
        """

        self.src_model_path = src_model_path
        self.csv_reader = None
        self.csv_fd = open(self.src_model_path, 'r')

    def _read_model(self):
        """
            Just initializes the csv DictReader
        """
        self.csv_reader = csv.DictReader(self.csv_fd, delimiter=',')

    def serialize(self):
        """
            Reads the model
            Writes to the db
        """
        self._read_model()
        self._write_to_db(self.csv_reader)

    # pylint: disable=R0201
    def _date_to_timestamp(self, *args):
        """
            Quick helper function to have a timestamp for the
            openquake postgres database
        """

        catalog_date = datetime.datetime(*args)
        return catalog_date.strftime('%Y-%m-%d %H:%M:%S')

    def _write_to_db(self, csv_reader):
        """
            :param csv_reader: DictReader instance
            :type csv_reader: DictReader object `csv.DictReader`
        """

        mags = ['mb_val', 'mb_val_error',
            'ml_val', 'ml_val_error',
            'ms_val', 'ms_val_error',
            'mw_val', 'mw_val_error']

        for row in csv_reader:

            timestamp = self._date_to_timestamp(int(row['year']),
                int(row['month']), int(row['day']), int(row['hour']),
                int(row['minute']), int(row['second']))

            surface = models.Surface(semi_minor=row['semi_minor'],
                semi_major=row['semi_major'],
                strike=row['strike'])
            surface.save()

            for mag in mags:
                row[mag] = row[mag].strip()

                # if m*val* are empty or a series of blank spaces, we assume
                # that the val is -999 for convention (ask Graeme if we want to
                # change this)
                if len(row[mag]) == 0:
                    row[mag] = None
                else:
                    row[mag] = float(row[mag])

            magnitude = models.Magnitude(mb_val=row['mb_val'],
                                mb_val_error=row['mb_val_error'],
                                ml_val=row['ml_val'],
                                ml_val_error=row['ml_val_error'],
                                ms_val=row['ms_val'],
                                ms_val_error=row['ms_val_error'],
                                mw_val=row['mw_val'],
                                mw_val_error=row['mw_val_error'])
            magnitude.save()

            wkt = 'SRID=4326;POINT(%s %s)' % (
                row['longitude'], row['latitude'])
            catalog = models.Catalog(owner_id=1, time=timestamp,
                surface=surface, eventid=row['eventid'],
                agency=row['agency'], identifier=row['identifier'],
                time_error=row['time_error'], depth=row['depth'],
                depth_error=row['depth_error'], magnitude=magnitude,
                point=wkt)
            catalog.save()
