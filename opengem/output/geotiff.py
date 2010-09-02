# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
A trivial implementation of the GeoTiff format,
using GDAL.

In order to make this run, you'll need GDAL installed,
and on the Mac I couldn't get the brew recipe to work.
I recommend the DMG framework at 
http://www.kyngchaos.com/software:frameworks.

I had to add the installed folders to 
PYTHONPATH in my .bash_profile file to get them to load.
"""

import numpy.core.multiarray as ncm
from osgeo import osr, gdal

from opengem import writer

class GeoTiffFile(writer.FileWriter):
    """Rough implementation of the GeoTiff format,
    based on http://adventuresindevelopment.blogspot.com/2008/12/
                python-gdal-adding-geotiff-meta-data.html
    """
    
    format = "GTiff"
    
    def __init__(self, path, image_grid):
        self.grid = image_grid
        self.raster = ncm.zeros((self.grid.ncols, self.grid.nrows))
        self.target = None
        super(GeoTiffFile, self).__init__(path)
        
    def _init_file(self):
        driver = gdal.GetDriverByName(self.format)
        self.target = driver.Create(self.path, self.grid.ncols, 
                        self.grid.nrows, 1, gdal.GDT_Byte)

        # top left x, w-e pixel resolution, rotation, 
        #   top left y, rotation, n-s pixel resolution
        self.target.SetGeoTransform(
            [self.grid.xulcorner, self.grid.cellsize, 
             0, self.grid.yulcorner, 0, self.grid.cellsize])

        # set the reference info 
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS("WGS84")
        self.target.SetProjection(srs.ExportToWkt())
        
        # This doesn't work with the eventlet tpool stuff.
        # self.file = tpool.Proxy(open(self.path, 'w'))
    
    def write(self, cell, value):
        """Stores the cell values in the NumPy array for later 
        serialization. Make sure these are zero-based cell addresses."""
        self.raster[int(cell[0]), int(cell[1])] = int(value)

    def close(self):
        """Make sure the file is flushed, and send exit event"""
        self.target.GetRasterBand(1).WriteArray(self.raster)
        self.target = None  # This is required to flush the file
        self.finished.send(True)


# http://adventuresindevelopment.blogspot.com/2008/12/
# python-gdal-adding-geotiff-meta-data.html
# ncols         174
# nrows         115
# xllcorner     14.97
# yllcorner     -34.54
# cellsize      0.11