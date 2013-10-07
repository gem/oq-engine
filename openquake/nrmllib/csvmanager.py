#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
import inspect
import zipfile
import StringIO
import itertools
import tempfile
from abc import ABCMeta, abstractmethod

from openquake.nrmllib.record import Table
from openquake.nrmllib.node import node_to_nrml, node_from_nrml
from openquake.nrmllib import InvalidFile, records, converter


class FileWrapper(object):
    """
    Mixin class providing a file-like interface to the underlying
    .fileobj.
    """
    def __iter__(self):
        return self

    def next(self):
        return self.fileobj.next()

    def readline(self):
        return self.fileobj.readline()

    def read(self, n=-1):
        return self.fileobj.read(n)

    def write(self, data):
        self.fileobj.write(data)

    def flush(self):
        self.fileobj.flush()

    def close(self):
        self.fileobj.close()

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        self.close()


class FileObject(FileWrapper):
    """
    A named reusable StringIO for reading and writing, useful for the tests
    """
    def __init__(self, name, bytestring):
        self.name = name
        self.bytestring = bytestring
        self.fileobj = StringIO.StringIO(bytestring)

    def close(self):
        data = self.fileobj.getvalue()
        self.fileobj.close()
        self.fileobj = StringIO.StringIO(data)


class NotInArchive(Exception):
    """Raised when trying to open a non-existing file in the archive"""


class ArchiveABC(object):
    """
    Abstract Base Class for Archive classes. Subclasses must override
    the methods ``_open`` and ``extract_filenames``.
    """
    __metaclass__ = ABCMeta

    opened = []

    def open(self, name, mode='r'):
        f = self._open(name, mode)
        self.opened.add(f)
        return f

    @abstractmethod
    def _open(self, name, mode):
        pass

    @abstractmethod
    def extract_filenames(self, prefix=''):
        pass

    def close(self):
        for f in self.opened:
            f.close()

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.extract_filenames())


# Writing directly to a zip archive is not possible because .writestr
# adds a new object every time it is called, so you cannot work line-by-line.
# The solution is to write to a temporary file and then push it into the
# archive at closing time
class TempFile(FileWrapper):
    """
    Wrapper over a NamedTemporaryFile to be used in conjunction with
    ZipArchive objects. It automatically stores the data in the archive
    at file closing time.
    """
    def __init__(self, arczip, arcname, mode):
        self.arczip = arczip
        self.arcname = arcname
        self.fileobj = tempfile.NamedTemporaryFile(mode)
        self.name = self.fileobj.name
        self.closed = False

    def close(self):
        if self.closed:  # already closed, do nothing
            return
        self.arczip.write(self.name, self.arcname)  # save in the archive
        self.fileobj.close()  # remove the temporary file
        self.closed = True


class ZipArchive(ArchiveABC):
    """
    Thin wrapper over a ZipFile object.
    """
    def __init__(self, zipname, mode='a'):
        self.zip = zipfile.ZipFile(zipname, mode)
        self.name = self.zip.filename
        self.opened = set()

    def _open(self, name, mode):
        if mode in ('w', 'w+', 'r+'):
            # write on a temporary file
            return TempFile(self.zip, name, mode)
        else:
            # open for reading
            return self.zip.open(name, mode)

    def extract_filenames(self, prefix=''):
        return set(i.filename for i in self.zip.infolist()
                   if i.filename.startswith(prefix))


class DirArchive(ArchiveABC):
    """
    Provides an archive interface over a filesystem directory
    """
    def __init__(self, dirname, mode='r'):
        self.name = dirname
        self.mode = mode
        if mode in ('w', 'w+', 'r+') and not os.path.exists(dirname):
            os.mkdir(dirname)
        self.opened = set()

    def _open(self, name, mode):
        return open(os.path.join(self.name, name), mode)

    def extract_filenames(self, prefix=''):
        return [f for f in os.listdir(self.name) if f.startswith(prefix)]


class MemArchive(ArchiveABC):
    """
    Provides an archive interface over FileObjects in memory
    """
    def __init__(self, items, mode='r'):
        self.dic = {}
        for name, csvstr in items:
            self.add(name, csvstr)
        self.opened = set()

    def add(self, name, csvstr):
        self.dic[name] = FileObject(name, csvstr)

    def _open(self, name, mode='r'):
        if mode in ('w', 'w+', 'r+'):
            self.dic[name] = f = FileObject(name, '')
            return f
        try:
            return self.dic[name]
        except KeyError:
            raise NotInArchive(name)

    def extract_filenames(self, prefix=''):
        return [f for f in self.dic if f.startswith(prefix)]


# used in the tests
def create_table(recordtype, csvstr):
    name = '__' + recordtype.__name__ + '.csv'
    archive = MemArchive([(name, csvstr)])
    man = CSVManager(archive, has_header=False)
    reclist = list(man.read(recordtype))
    return Table(recordtype, reclist)


class MultipleConverterError(Exception):
    """
    Raised when it is not possible to extract a single converter
    from an archive of CSV files (i.e. there more than one common
    prefix).
    """


class CSVManager(object):
    """
    A class to manage CSV files stored in an Archive object.
    The file names must be of the form <prefix>__<recordtype>.csv
    where <recordtype> is the name of the record class describing
    the structure of the file. For instance an archive could contain
    the files

     vulnerability-model-discrete__DiscreteVulnerability.csv
     vulnerability-model-discrete__DiscreteVulnerabilityData.csv
     vulnerability-model-discrete__DiscreteVulnerabilitySet.csv

    then the method .convert_to_node() would convert the files
    into a Node object by using the appropriate converter and
    the method .convert_to_nrml() would generate an XML file
    named vulnerability-model-discrete.xml in the archive.
    Viceversa, starting from an empty archive and a file named
    vulnerability-model-discrete.xml, it is possible to generate
    the CSV files by calling

    CSVManager(archive).convert_from_nrml()
    """
    def __init__(self, archive, prefix='', has_header=True):
        self.archive = archive
        self.prefix = prefix
        self.has_header = has_header
        self.rt2reader = {}
        self.rt2writer = {}
        self.rt2file = {}

    def _getconverters(self):
        """
        Returns a list of Converter instances, one for each file group
        in the underlying archive. Each converter has its own manager
        with the right prefix.
        """
        converters = {}  # name->converter dictionary
        cc = {}  # converter name -> converter class dictionary
        for name, value in vars(converter).iteritems():
            if inspect.isclass(value) and issubclass(
                    value, converter.Converter):
                cc[name] = value
        for fname in sorted(self.archive.extract_filenames()):
            try:
                prefix, recordcsv = fname.split('__')
            except ValueError:
                continue
            if not recordcsv.endswith('.csv'):
                continue
            recordtype = getattr(records, recordcsv[:-4], None)
            if recordtype is None:
                continue
            if not prefix in converters:
                man = self.__class__(self.archive, prefix)
                conv = cc[recordtype.convertername](man)
                converters[prefix] = conv
        return converters.values()

    def _getconverter(self):
        """
        Extract the appropriate converter to convert the files in
        the underlying archive. Raise an error is no converter is
        found (this happens if there are no files following the
        naming conventions).
        """
        converters = self._getconverters()
        if not converters:
            raise NotInArchive(
                'Could not determine the right converter '
                'from files %s' % self.archive.extract_filenames())
        elif len(converters) > 1:
            raise MultipleConverterError(
                'Found %d converters %s, expected 1' %
                (len(converters), converters))
        return converters[0]

    def convert_to_node(self):
        """
        Convert the CSV files in the archive with the given prefix
        into a Node object. Raise an error if some files are missing.
        """
        return self._getconverter().csv_to_node()

    def convert_to_nrml(self, outdir=None):
        """
        From CSV files with the given prefix to .xml files; if the output
        directory is not specified, use the input archive to store the output.
        """
        fnames = []
        for conv in self._getconverters():
            with conv.man as man:
                outname = man.prefix + '.xml'
                if outdir is None:
                    out = man.archive.open(outname, 'w+')
                else:
                    out = open(os.path.join(outdir, outname), 'w+')
                with out:
                    node_to_nrml(conv.csv_to_node(), out)
                fnames.append(out.name)
        return fnames

    def convert_from_nrml(self, fname):
        """
        Populate the underlying archive with CSV files extracted from the
        given XML file.
        """
        assert fname.endswith('.xml'), fname
        prefix = os.path.basename(fname)[:-4]
        return self.convert_from_node(node_from_nrml(fname)[0], prefix)

    def convert_from_node(self, node, prefix=None):
        """
        Populate the underlying archive with CSV files extracted from the
        given Node object.
        """
        if prefix is None:
            man = self
        else:  # creates a new CSVManager for the given prefix
            man = self.__class__(self.archive, prefix)
        conv = converter.Converter.from_tag(node.tag)(man)
        with man:
            for rec in conv.node_to_records(node):
                man.write(rec)  # automatically opens the needed files
        return [f.name for f in man.archive.opened]

    def read(self, recordtype):
        """
        Read the records from the underlying CSV file. Returns an iterator.
        """
        reader = self.rt2reader.get(recordtype)
        if reader is None:
            fname = '%s__%s.csv' % (self.prefix, recordtype.__name__)
            self.rt2file[recordtype] = f = self.archive.open(fname, 'r')
            self.rt2reader[recordtype] = reader = csv.reader(f)
            if self.has_header:
                header = reader.next()
                if header != recordtype.fieldnames:
                    raise InvalidFile(
                        '%s: line 1: got %s as header, expected %s' %
                        (fname, header, recordtype.fieldnames))
        for row in reader:
            yield recordtype(*row)

    # this is used when converting from csv -> nrml
    def groupby(self, keyfields, recordtype):
        """
        Group the records on the underlying CSV according to the given
        keyfield. Assume the records are sorted.
        """
        keyindexes = [recordtype._name2index[k] for k in keyfields]
        return itertools.groupby(
            self.read(recordtype), lambda rec: [rec[i] for i in keyindexes])

    def readtable(self, recordtype):
        """
        Generate a Table object from the underlying CSV
        """
        return Table(recordtype, list(self.read(recordtype)))

    def write(self, record):
        """
        Write a record on the corresponding CSV file
        """
        rt = type(record)  # record type
        writer = self.rt2writer.get(rt)
        if writer is None:
            fname = '%s__%s.csv' % (self.prefix, rt.__name__)
            self.rt2file[rt] = f = self.archive.open(fname, 'w')
            self.rt2writer[rt] = writer = csv.writer(f)
            if self.has_header:
                writer.writerow(rt.fieldnames)
        writer.writerow(record)

    def __enter__(self):
        """Initialize a few dictionaries"""
        self.rt2reader = {}
        self.rt2writer = {}
        self.rt2file = {}
        self.archive.opened = set()
        return self

    def __exit__(self, etype, exc, tb):
        """Close the underlying archive"""
        self.archive.close()
