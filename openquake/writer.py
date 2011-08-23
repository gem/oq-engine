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


# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base classes for the output methods of the various codecs.
"""

import logging
from os.path import basename

from openquake.db.alchemy.models import OqJob, Output

LOGGER = logging.getLogger('serializer')
LOGGER.setLevel(logging.DEBUG)


class FileWriter(object):
    """Simple output half of the codec process."""

    def __init__(self, path):
        self.path = path
        self.file = None
        self._init_file()
        self.root_node = None

    def _init_file(self):
        """Get the file handle open for writing"""
        self.file = open(self.path, "w")

    def write(self, point, value):
        """
        Write out an individual point (unimplemented).

        :param point: location associated with the data to be written
        :type point: should be a shapes.Site object
            Note(LB): Some subclasses override this behavior in their
            write() methods. Be careful.

        :param value: some value to be written to the file
        :type value: determined by concrete class implementation
        """
        raise NotImplementedError

    def close(self):
        """Close and flush the file. Send finished messages."""
        self.file.close()

    def serialize(self, iterable):
        """Wrapper for writing all items in an iterable object."""
        if isinstance(iterable, dict):
            iterable = iterable.items()
        for key, val in iterable:
            self.write(key, val)
        self.close()


class XMLFileWriter(FileWriter):
    """
    Base class for writing XML files.
    """

    def write_header(self):
        """
        Write out the file header.
        """
        raise NotImplementedError

    def write_footer(self):
        """
        Write out the file footer.
        """
        raise NotImplementedError

    def serialize(self, iterable):
        """
        Wrapper for writing all items in an iterable object.
        """
        if isinstance(iterable, dict):
            iterable = iterable.items()
        self.write_header()
        for key, val in iterable:
            self.write(key, val)
        self.write_footer()
        self.close()


class DBWriter(object):
    """
    Abstact class implementing the "serialize" interface to output an iterable
    to the database.

    Subclasses must either implement get_output_type() and insert_datum() or
    override serialize().
    """

    def __init__(self, session, nrml_path, oq_job_id):
        self.nrml_path = nrml_path
        self.oq_job_id = oq_job_id
        self.session = session
        self.output = None
        self.bulk_inserter = None

    def insert_output(self, output_type):
        """Insert an `uiapi.output` record for the job at hand."""

        assert self.output is None

        LOGGER.info("> insert_output")
        job = self.session.query(OqJob).filter(
            OqJob.id == self.oq_job_id).one()
        self.output = Output(owner=job.owner, oq_job=job,
                             display_name=basename(self.nrml_path),
                             output_type=output_type, db_backed=True)
        self.session.add(self.output)
        self.session.flush()
        LOGGER.info("output = '%s'" % self.output)
        LOGGER.info("< insert_output")

    def get_output_type(self):
        """
        The type of the output record as a string
        """
        raise NotImplementedError()

    def insert_datum(self, key, values):
        """
        Called for each item of the iterable during serialize.
        """
        raise NotImplementedError()

    def serialize(self, iterable):
        """
        Implementation of the "serialize" interface.

        An Output record with type get_output_type() will be created, then
        each item of the iterable will be serialized in turn to the database.
        """
        LOGGER.info("> serialize")
        LOGGER.info("serializing %s points" % len(iterable))

        if not self.output:
            self.insert_output(self.get_output_type())
        LOGGER.info("output = '%s'" % self.output)

        if isinstance(iterable, dict):
            items = iterable.iteritems()
        else:
            items = iterable

        for key, values in items:
            self.insert_datum(key, values)

        if self.bulk_inserter:
            self.bulk_inserter.flush(self.session)
        self.session.commit()

        LOGGER.info("serialized %s points" % len(iterable))
        LOGGER.info("< serialize")


class CompositeWriter(object):
    """A writer that outputs to multiple writers"""

    def __init__(self, *writers):
        self.writers = writers

    def serialize(self, iterable):
        """Implementation of the "serialize" interface."""

        for writer in self.writers:
            if writer:
                writer.serialize(iterable)


def compose_writers(writers):
    """
    Takes a list of writers (the list can be empty or contain None items) and
    returns a single writer or None if the list didn't contain any writer.
    """

    if all(writer == None for writer in writers):  # True if the list is empty
        return None
    elif len(writers) == 1:
        return writers[0]
    else:
        return CompositeWriter(*writers)


class BulkInserter(object):
    """Handle bulk object insertion"""

    def __init__(self, sa_model):
        """Create a new bulk inserter for a SQLAlchemy model class"""
        self.table = sa_model.__table__
        self.fields = None
        self.values = []
        self.count = 0

    def add_entry(self, **kwargs):
        """
        Add a new entry to be inserted

        The first time the method is called the field list is stored;
        subsequent add_entry() calls must provide the same set of
        keyword arguments.

        Handles PostGIS/GeoAlchemy types.
        """
        if not self.fields:
            self.fields = kwargs.keys()
        assert set(self.fields) == set(kwargs.keys())
        for k in self.fields:
            self.values.append(kwargs[k])
        self.count += 1

    def flush(self, session):
        """Inserts the entries in the database using a bulk insert query"""
        if not self.values:
            return

        cursor = session.connection().connection.cursor()
        value_args = []
        for f in self.fields:
            col = self.table.columns[f]
            if hasattr(col.type, 'srid'):
                value_args.append('GeomFromText(%%s, %d)' % col.type.srid)
            else:
                value_args.append('%s')

        sql = "INSERT INTO %s.%s (%s) VALUES " % (
            self.table.schema, self.table.name, ", ".join(self.fields)) + \
            ", ".join(["(" + ", ".join(value_args) + ")"] * self.count)
        cursor.execute(sql, self.values)

        self.fields = None
        self.values = []
        self.count = 0
