#!/usr/bin/env python
# coding: utf-8

import pprint
import logging
import time
import csv
import sys
import os
from shapely.geometry import Point, shape
from collections import Counter
from openquake.baselib import sap
from openquake.hazardlib.geo.packager import fiona
from openquake.qa_tests_data import mosaic, global_risk

CLOSE_DIST_THRESHOLD = 0.1  # degrees


class GlobalModelGetter:
    """
    Class with methods to associate coordinates to models
    """
    def __init__(self, kind='mosaic', shapefile_path=None):
        if kind not in ('mosaic', 'global_risk'):
            raise ValueError(f'Model getter for {kind} is not implemented')
        self.kind = kind
        if self.kind == 'mosaic':
            self.model_code = 'code'
        elif self.kind == 'global_risk':
            self.model_code = 'shapeGroup'
        if shapefile_path is None:  # read from openquake.cfg
            if kind == 'mosaic':
                self.dir = os.path.dirname(mosaic.__file__)
                shapefile_path = os.path.join(self.dir, 'ModelBoundaries.shp')
            elif kind == 'global_risk':
                self.dir = os.path.dirname(global_risk.__file__)
                shapefile_path = os.path.join(
                    self.dir, 'geoBoundariesCGAZ_ADM0.shp')
        self.shapefile_path = shapefile_path

    def get_models_list(self):
        """
        Returns a list of all models in the shapefile
        """
        if fiona is None:
            print('fiona/GDAL is not installed properly!', sys.stderr)
            return []
        with fiona.open(self.shapefile_path, 'r') as shp:
            models = [polygon['properties'][self.model_code]
                      for polygon in shp]
        return models

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
                        model = polygon['properties'][self.model_code]
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
                polygon['properties'][self.model_code]:
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
