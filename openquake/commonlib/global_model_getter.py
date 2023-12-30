#!/usr/bin/env python
# coding: utf-8

import pprint
import logging
import time
import csv
import sys
import os
import numpy as np
from shapely.geometry import Point, shape
from shapely.strtree import STRtree
from shapely import wkt, points
from collections import Counter
from openquake.baselib import sap, general
from openquake.hazardlib.geo.packager import fiona
from openquake.qa_tests_data import mosaic, global_risk

CLOSE_DIST_THRESHOLD = 0.1  # degrees


class GlobalModelGetter:
    """
    Class with methods to associate coordinates to models

    :param kind: 'mosaic' or 'global_risk'
    :param model_code_field: shapefile fieldname containing the model code
    :param shapefile_path: path of the shapefile containing geometries and data
    :param model_codes: if not None, only that subset of model codes will be
        taken into account when building the spatial index
    """
    def __init__(self, kind='mosaic', model_code_field=None,
                 shapefile_path=None, model_codes=None):
        if kind not in ('mosaic', 'global_risk'):
            raise ValueError(f'Model getter for {kind} is not implemented')
        self.kind = kind
        if model_code_field is None:
            if self.kind == 'mosaic':
                model_code_field = 'code'
            elif self.kind == 'global_risk':
                model_code_field = 'shapeGroup'
        if shapefile_path is None:  # read from openquake.cfg
            if kind == 'mosaic':
                self.dir = os.path.dirname(mosaic.__file__)
                shapefile_path = os.path.join(self.dir, 'ModelBoundaries.shp')
            elif kind == 'global_risk':
                self.dir = os.path.dirname(global_risk.__file__)
                shapefile_path = os.path.join(
                    self.dir, 'geoBoundariesCGAZ_ADM0.shp')
        self.model_code_field = model_code_field
        self.shapefile_path = shapefile_path
        self.model_codes = model_codes

    def get_geoms(self, model_codes):
        with fiona.open(self.shapefile_path, 'r') as shp:
            geoms = [
                shape(polygon['geometry']) for polygon in shp
                if polygon['properties'][
                    self.model_code_field] in model_codes]
        return geoms

    @general.cached_property
    def sindex(self):
        with fiona.open(self.shapefile_path, 'r') as shp:
            if self.model_codes is not None:
                geoms = [
                    shape(polygon['geometry']) for polygon in shp
                    if polygon['properties'][
                        self.model_code_field] in self.model_codes]
            else:
                geoms = [shape(polygon['geometry']) for polygon in shp]
            sindex = STRtree(geoms)
        return sindex

    @general.cached_property
    def sinfo(self):
        # if model_codes is not None, build the index only for those
        with fiona.open(self.shapefile_path, 'r') as shp:
            # NOTE: the dtype is hardcoded and it might not be optimal
            dtype = [(name, 'U50') for name in list(shp[0]['properties'])]
            if self.model_codes is not None:
                sinfo = np.array(
                    [tuple(zone['properties'].values()) for zone in shp
                     if zone['properties'][
                         self.model_code_field] in self.model_codes],
                    dtype=dtype)
            else:
                sinfo = np.array(
                    [tuple(zone['properties'].values()) for zone in shp],
                    dtype=dtype)
        return sinfo

    def get_models_list(self):
        """
        Returns a list of all models in the shapefile
        """
        if self.sinfo is not None:
            models = list(np.unique([info[self.model_code_field]
                                     for info in self.sinfo]))
            return models
        if fiona is None:
            print('fiona/GDAL is not installed properly!', sys.stderr)
            return []
        with fiona.open(self.shapefile_path, 'r') as shp:
            models = [polygon['properties'][self.model_code_field]
                      for polygon in shp]
        return models

    def is_inside(self, geoms, model_code):
        """
        :param geoms: array of items we want to classify if they are within the
            boundaries of a model
        :param model_code: code of the model
        :returns: an array of booleans indicating if each item is within the
            model boundaries
        """
        # NOTE: the index is one for adm0 but it can be more for adm2
        model_indices = np.where(
            self.sinfo[self.model_code_field] == model_code)
        t0 = time.time()
        within = self.sindex.query(geoms, 'within')
        t1 = time.time()
        logging.debug(
            f'Geospatial query done in {t1 - t0} seconds')
        # NOTE: within[0] are the indices of the input geometries
        #       within[1] are the indices of the indexed geometries
        matched_idxs = np.isin(within[1], model_indices)
        geoms_idxs = np.arange(0, len(geoms))
        return np.isin(geoms_idxs, within[0][matched_idxs])

    def is_lon_lat_array_inside(self, lon_array, lat_array, model_code):
        geoms = points(lon_array, lat_array)
        return self.is_inside(geoms, model_code)

    def is_hypocenter_array_inside(self, hypocenters, model_code):
        t0 = time.time()
        logging.debug(f'Checking {len(hypocenters)} hypocenters')
        geoms = points(hypocenters)
        ok = self.is_inside(geoms, model_code)
        t1 = time.time()
        logging.debug(
            f'Indices within model boundaries retrieved in {t1 - t0} seconds')
        return ok

    def get_models_by_wkt(self, geom_wkt, predicate='intersects'):
        t0 = time.time()
        geom = wkt.loads(geom_wkt)
        idxs = self.sindex.query(geom, predicate)
        models = list(np.unique([info[self.model_code_field]
                                 for info in self.sinfo[idxs]]))
        logging.info(f'Models retrieved in {time.time() - t0} seconds')
        return models

    def get_models_by_geoms_array(
            self, geoms, predicate='intersects', distance=CLOSE_DIST_THRESHOLD,
            return_indices_only=False):
        t0 = time.time()
        idxs = self.sindex.query(geoms, predicate=predicate, distance=distance)
        if return_indices_only:
            return idxs
        models = list(np.unique([info[self.model_code_field]
                                 for info in self.sinfo[idxs][1]]))
        logging.info(f'Models retrieved in {time.time() - t0} seconds')
        return models

    def get_nearest_models_by_geoms_array(
            self, geoms, max_distance=CLOSE_DIST_THRESHOLD,
            return_distance=False, exclusive=False, all_matches=True,
            return_indices_only=False):
        t0 = time.time()
        idxs = self.sindex.query_nearest(
            geoms, max_distance=max_distance, return_distance=return_distance,
            exclusive=exclusive, all_matches=all_matches)
        if return_indices_only:
            return idxs
        models = list(np.unique([info[self.model_code_field]
                                 for info in self.sinfo[idxs[1]]]))
        logging.info(f'Models retrieved in {time.time() - t0} seconds')
        return models

    def get_nearest_model_by_lon_lat_sindex(self, lon, lat, strict=True):
        lon = float(lon)
        lat = float(lat)
        point = Point(lon, lat)
        idxs = self.sindex.query(
            point, 'dwithin', distance=CLOSE_DIST_THRESHOLD)
        if len(idxs) > 0:
            close_models = self.sinfo[idxs][self.model_code_field]
            if len(close_models) > 1:
                idxs, dists = self.sindex.query_nearest(
                    point, max_distance=CLOSE_DIST_THRESHOLD,
                    return_distance=True)
                closest_model = self.sinfo[idxs[np.argmin(dists)]][
                    self.model_code_field]
                logging.warning(
                    f'Site at lon={lon} lat={lat} is on the border between'
                    f' more than one model: {close_models}. Using'
                    f' {closest_model}')
                return closest_model
            else:
                model = close_models[0]
                logging.info(f'Site at lon={lon} lat={lat} is'
                             f' covered by model {model}')
                return model
        elif strict:
            raise ValueError(
                f'Site at lon={lon} lat={lat} is not covered'
                f' by any model!')
        else:
            logging.error(
                f'Site at lon={lon} lat={lat} is not covered'
                f' by any model!')
        return None

    def get_model_by_lon_lat_sindex(self, lon, lat, strict=True):
        lon = float(lon)
        lat = float(lat)
        point = Point(lon, lat)
        idxs = self.sindex.query(
            point, 'dwithin', distance=CLOSE_DIST_THRESHOLD)
        models = list(np.unique([info[self.model_code_field]
                                 for info in self.sinfo[idxs]]))
        if len(models) > 1:
            raise ValueError(
                f'Site at lon={lon} lat={lat} is'
                f' covered by multiple models {models}')
        if len(models) == 1:
            model = models[0]
            logging.info(f'Site at lon={lon} lat={lat} is'
                         f' covered by model {model}')
        elif strict:
            raise ValueError(
                f'Site at lon={lon} lat={lat} is not covered'
                f' by any model!')
        else:
            logging.error(
                f'Site at lon={lon} lat={lat} is not covered'
                f' by any model!')
            return None
        return model

    def get_model_by_lon_lat(
            self, lon, lat, strict=True, check_overlaps=True,
            measure_time=False):
        """
        Given a longitude and latitude, finds the corresponding model

        :param lon:
            The site longitude
        :param lat:
            The site latitude
        :param strict:
            If True (the default) raise an error, otherwise log an error
        :param check_overlaps:
            If True (the default) check if the site is close to the border
            between multiple models
        :param measure_time:
            If True log the time spent to search the model
        :returns: the code of the closest (or only) model
        """
        t0 = time.time()
        lon = float(lon)
        lat = float(lat)
        point = Point(lon, lat)

        with fiona.open(self.shapefile_path, 'r') as shp:
            if not check_overlaps:
                for polygon in shp:
                    if point.within(shape(polygon['geometry'])):
                        model = polygon['properties'][self.model_code_field]
                        logging.info(f'Site at lon={lon} lat={lat} is'
                                     f' covered by model {model}')
                        break
                else:
                    if measure_time:
                        logging.info(
                            f'Model search took {time.time() - t0} seconds')
                    if strict:
                        raise ValueError(
                            f'Site at lon={lon} lat={lat} is not covered'
                            f' by any model!')
                    else:
                        logging.error(
                            f'Site at lon={lon} lat={lat} is not covered'
                            f' by any model!')
                    return None
                if measure_time:
                    logging.info(
                        f'Model search took {time.time() - t0} seconds')
                return model

            # NOTE: poly.distance(point) returns 0.0 if point is within poly
            #       To calculate the distance to the nearest edge, one would do
            #       poly.exterior.distance(point) instead
            model_dist = {
                polygon['properties'][self.model_code_field]:
                    shape(polygon['geometry']).distance(point)
                for polygon in shp
            }
        close_models = {
            model: model_dist[model]
            for model in model_dist
            if model_dist[model] < CLOSE_DIST_THRESHOLD
        }
        num_close_models = len(close_models)
        if num_close_models < 1:
            if strict:
                raise ValueError(
                    f'Site at lon={lon} lat={lat} is not covered by any'
                    f' model!')
            else:
                logging.error(
                    f'Site at lon={lon} lat={lat} is not covered by any'
                    f' model!')
                model = None
        elif num_close_models > 1:
            model = min(close_models, key=close_models.get)
            logging.warning(
                f'Site at lon={lon} lat={lat} is on the border between more'
                f' than one model: {close_models}. Using {model}')
        else:  # only one close model was found
            model = list(close_models)[0]
            logging.info(
                f'Site at lon={lon} lat={lat} is covered by model {model}'
                f' (distance: {model_dist[model]})')
        if measure_time:
            logging.info(f'Model search took {time.time() - t0} seconds')
        return model

    def get_models_by_sites_csv(self, csv_path):
        """
        Given a csv file with (Longitude, Latitude) of sites, returns a
        dictionary having as key the site location and as value the
        model that covers that site

        :param csv_path:
            path of the csv file containing sites coordinates
        """
        model_by_site = {}
        with open(csv_path, 'r') as sites:
            for site in csv.DictReader(sites):
                try:
                    lon = site['Longitude']
                    lat = site['Latitude']
                except KeyError:
                    lon = site['lon']
                    lat = site['lat']
                model_by_site[(lon, lat)] = self.get_model_by_lon_lat(
                    lon, lat, strict=False)
        logging.info(Counter(model_by_site.values()))
        return model_by_site

    def get_models_by_sites_csv_sindex(self, csv_path):
        """
        Given a csv file with (Longitude, Latitude) of sites, returns the
        list of models covering each of the sites

        :param csv_path:
            path of the csv file containing sites coordinates
        """
        geoms = []
        with open(csv_path, 'r') as sites:
            for site in csv.DictReader(sites):
                try:
                    lon = site['Longitude']
                    lat = site['Latitude']
                except KeyError:
                    lon = site['lon']
                    lat = site['lat']
                geoms.append(Point(lon, lat))
        self.get_models_by_geoms_array(geoms)


def main(sites_csv_path, models_boundaries_shp_path):
    logging.basicConfig(level=logging.INFO)
    model_by_site = GlobalModelGetter(
        models_boundaries_shp_path).get_models_by_sites_csv(sites_csv_path)
    pprint.pprint(model_by_site)


main.sites_csv_path = 'path of a csv file containing sites coordinates'
main.models_boundaries_shp_path = \
    'path of a shapefile containing boundaries of models'

if __name__ == '__main__':
    sap.run(main)
