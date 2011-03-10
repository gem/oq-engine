# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
Base classes for the output methods of the various codecs.
"""


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
            Note(LB): Some sublcasses override this behavior in their
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
