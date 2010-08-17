# vim: tabstop=4 shiftwidth=4 softtabstop=4

from eventlet import event
from eventlet import tpool
import numpy, os
from osgeo import osr, gdal

from opengem import writer

class GeoTiffFile(writer.FileWriter):
    """Rough implementation of the GeoTiff format,
    based on http://adventuresindevelopment.blogspot.com/2008/12/
                python-gdal-adding-geotiff-meta-data.html
    """
    
    format = "GTiff"
    
    def __init__(self, path, ncols, nrows, xllcorner, yllcorner, cellsize):
        self.finished = event.Event()
        driver = gdal.GetDriverByName(self.format)
        self.target = driver.Create(path, ncols, nrows, 1, gdal.GDT_Byte)

        # top left x, w-e pixel resolution, rotation, 
        #   top left y, rotation, n-s pixel resolution
        self.target.SetGeoTransform([xllcorner, cellsize, 0, yllcorner, 0, cellsize])

        # set the reference info 
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS("WGS84")
        self.target.SetProjection(srs.ExportToWkt())
        
        self.raster = numpy.zeros( (ncols, nrows), dtype = numpy.uint8)
        # TODO(jmc): Get this to work with the eventlet tpool stuff.
        # self.file = tpool.Proxy(open(self.path, 'w'))
    
    def write(self, cell, value):
        # TODO(jmc): Make sure these are zero-based cell addresses!
        self.raster[cell[0], cell[1]] = value

    def close(self):
        """Make sure the file is flushed, and send exit event"""


        # write the band
        self.target.GetRasterBand(1).WriteArray(self.raster)
        self.finished.send(True)


# http://adventuresindevelopment.blogspot.com/2008/12/
# python-gdal-adding-geotiff-meta-data.html
# ncols         174
# nrows         115
# xllcorner     14.97
# yllcorner     -34.54
# cellsize      0.11