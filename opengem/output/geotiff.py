# vim: tabstop=4 shiftwidth=4 softtabstop=4

from opengem import writer

class GeoTiffFile(writer.FileWriter):
    """Example output class.

    Were this a real class it would probably be doing something much more
    interesting.

    """
    
    def write(self, cell, value):
        self.file.write('%s %s %s\n' % (cell[0], cell[1], value))
        #self.file.flush()
