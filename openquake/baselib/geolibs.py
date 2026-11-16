"""
The geospatial libraries used by OpenQuake. They are imported here, so that
the check of the installation lives in one place. GDAL and geopandas are
heavy and are imported only when they are needed.
"""
import os

MISSING = ('The geospatial libraries must be installed using our '
           'requirements.txt files (see https://github.com/gem/oq-engine). '
           'Only the GEM wheels are tested and guaranteed to work')

try:
    import fiona  # noqa: F401
    import pyproj  # noqa: F401
    from fiona.crs import CRS  # noqa: F401
except ImportError:
    raise ImportError(MISSING)


def get_geopandas():
    """
    :returns: the geopandas module
    """
    try:
        import geopandas
    except ImportError:
        raise ImportError(MISSING)
    return geopandas


def get_gdal():
    """
    :returns: the osgeo.gdal module, with exceptions enabled
    """
    # PROJ_DATA must be set before GDAL is imported (proj == 9.0.1), to avoid
    # 'ERROR 1: PROJ: proj_create_from_name: Cannot find proj.db'
    if 'PROJ_DATA' not in os.environ:
        os.environ['PROJ_DATA'] = pyproj.datadir.get_data_dir()
    try:
        from osgeo import gdal
    except ImportError:
        raise ImportError(MISSING)
    gdal.UseExceptions()
    return gdal
