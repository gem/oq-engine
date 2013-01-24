# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base classes for the output methods of the various codecs.
"""

import logging
from os.path import basename

from django.db import transaction
from django.db import connections
from django.db import router
from django.contrib.gis.db import models as gis_models

from openquake.db import models

LOGGER = logging.getLogger('serializer')


class FileWriter(object):
    """Simple output half of the codec process."""

    def __init__(self, path):
        self.path = path
        self.file = None
        self.root_node = None

    def initialize(self):
        """Initialization hook for derived classes."""
        pass

    def open(self):
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
        if self.file:
            self.file.close()

    def serialize(self, iterable):
        """Wrapper for writing all items in an iterable object."""
        if isinstance(iterable, dict):
            iterable = iterable.items()
        self.initialize()
        self.open()
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
        self.initialize()
        self.open()
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

    def __init__(self, nrml_path, oq_job_id):
        self.nrml_path = nrml_path
        self.oq_job_id = oq_job_id
        self.output = None
        self.bulk_inserter = None

    def insert_output(self, output_type):
        """Insert an `uiapi.output` record for the job at hand."""

        assert self.output is None

        job = models.OqJob.objects.get(id=self.oq_job_id)

        # al-maisan, Fri, 29 Jun 2012 17:36:35 +0200
        # https://bugs.launchpad.net/openquake/+bug/1019317
        # figure out why using a single output record for gmf_data breaks the
        # probablistic event-based risk calculator.
        if output_type == "gmf":
            one_or_none = []
        else:
            one_or_none = models.Output.objects.filter(
                oq_job=job, display_name=basename(self.nrml_path),
                output_type=output_type)
        if len(one_or_none) == 1:
            self.output = one_or_none[0]
            LOGGER.info("using output = '%s'", self.output)
        else:
            self.output = models.Output(
                owner=job.owner, oq_job=job,
                display_name=basename(self.nrml_path), output_type=output_type)
            self.output.save()
            LOGGER.info("creating output = '%s'", self.output)

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

    @transaction.commit_on_success('reslt_writer')
    def serialize(self, iterable):
        """
        Implementation of the "serialize" interface.

        An Output record with type get_output_type() will be created, then
        each item of the iterable will be serialized in turn to the database.
        """
        LOGGER.info("serializing %s points", len(iterable))

        if not self.output:
            self.insert_output(self.get_output_type())
        LOGGER.info("output = '%s'", self.output)

        if isinstance(iterable, dict):
            items = iterable.iteritems()
        else:
            items = iterable

        for key, values in items:
            self.insert_datum(key, values)

        if self.bulk_inserter:
            self.bulk_inserter.flush()

        LOGGER.info("serialized %s points", len(iterable))


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


# pylint: disable=W0212
class BulkInserter(object):
    """Handle bulk object insertion"""

    def __init__(self, dj_model, max_cache_size=None):
        """
        Create a new bulk inserter for a Django model class

        :param dj_model:
            Django model class
        :param int max_cache_size:
            The number of entries to cache before flushing/inserting. This
            helps to limit memory consumption for large sets of inserts.

            The default value is `None`, which means there is no maximum.
        """
        self.table = dj_model
        self.max_cache_size = max_cache_size
        self.fields = None
        self.values = []
        self.count = 0

    def add_entry(self, **kwargs):
        """
        Add a new entry to be inserted

        The first time the method is called the field list is stored;
        subsequent add_entry() calls must provide the same set of
        keyword arguments.

        Handles PostGIS/GeoDjango types.
        """
        if not self.fields:
            self.fields = kwargs.keys()
        assert set(self.fields) == set(kwargs.keys())
        for k in self.fields:
            self.values.append(kwargs[k])
        self.count += 1

        # If we have hit the `max_cache_size` is set,
        if self.max_cache_size is not None:
            # check if we have hit the maximum insert the current batch.
            if len(self.values) >= self.max_cache_size:
                self.flush()

    def flush(self):
        """Inserts the entries in the database using a bulk insert query"""
        if not self.values:
            return

        alias = router.db_for_write(self.table)
        cursor = connections[alias].cursor()
        value_args = []

        field_map = dict()
        for f in self.table._meta.fields:
            field_map[f.column] = f

        for f in self.fields:
            col = field_map[f]
            if isinstance(col, gis_models.GeometryField):
                value_args.append('GeomFromText(%%s, %d)' % col.srid)
            else:
                value_args.append('%s')

        sql = "INSERT INTO \"%s\" (%s) VALUES " % (
            self.table._meta.db_table, ", ".join(self.fields)) + \
            ", ".join(["(" + ", ".join(value_args) + ")"] * self.count)
        cursor.execute(sql, self.values)
        transaction.set_dirty(using=alias)

        self.fields = None
        self.values = []
        self.count = 0
