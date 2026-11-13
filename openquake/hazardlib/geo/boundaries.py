"""
Country and mosaic boundaries read from GeoPackage files. Lives in hazardlib
so that hazardlib does not need to import commonlib.readinput.
"""
import os
import logging
import functools
from shapely.geometry import shape
from shapely.validation import make_valid, explain_validity
from openquake.baselib import config
from openquake.baselib.geolibs import fiona, get_geopandas


# NOTE: we expect to call this for mosaic or global_risk (adm0-1-2)
@functools.lru_cache(maxsize=4)
def read_geometries(fname, name):
    """
    :param fname: path of the file containing the geometries
    :param name: name of the primary key field
    :returns: GeoDataFrame frame with codes and geometries
    """
    gpd = get_geopandas()
    codes = []
    geoms = []
    with fiona.open(fname, IMMUTABLE="YES") as f:
        crs = f.crs
        for feature in f:
            props = feature["properties"]
            geom = feature["geometry"]
            code = props[name]
            if code and geom:
                g = shape(geom)
                if not g.is_valid:
                    logging.warning("Invalid geometry for %s: %s",
                                    code, explain_validity(g))
                    g = make_valid(g)
                codes.append(code)
                geoms.append(g)
            else:
                logging.error(f"{code=}, {geom=} in {fname}")
    # NOTE: "geometry" instead of "geom" would be the standard in GeoPandas,
    #       but using "geom" we avoid changing other code using this object
    return gpd.GeoDataFrame(
        dict(code=codes, geom=geoms), geometry="geom", crs=crs)


def read_countries_df():
    """
    :returns: a DataFrame of geometries for the world countries
    """
    country_boundaries_file = None
    if hasattr(config.directory, 'admin0_boundaries_file'):
        country_boundaries_file = config.directory.admin0_boundaries_file
    if not country_boundaries_file:
        # keep local: the default file is in the qa_tests_data package
        from openquake.qa_tests_data import global_risk
        country_boundaries_file = os.path.join(
            os.path.dirname(global_risk.__file__),
            'geoBoundariesCGAZ_ADM0.gpkg')
    logging.info(f'Reading {country_boundaries_file}')
    return read_geometries(country_boundaries_file, 'shapeGroup')
