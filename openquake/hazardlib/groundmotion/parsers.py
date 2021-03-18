from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from urllib.request import urlopen

import io
import zipfile
import logging
import requests
import numpy

from openquake.baselib.node import node_from_xml
from openquake.hazardlib.groundmotion.maps import ShakeMap


F32 = numpy.float32
SHAKEMAP_FIELDS = set(
    'LON LAT SVEL PGA MMI PSA03 PSA10 PSA30 STDPGA \
        STDMMI STDPSA03 STDPSA10 STDPSA30'
    .split())
FIELDMAP = {
    'LON': 'lon',
    'LAT': 'lat',
    'SVEL': 'vs30',
    'PGA': ('val', 'PGA'),
    'MMI': ('val', 'MMI'),
    'PSA03': ('val', 'SA(0.3)'),
    'PSA10': ('val', 'SA(1.0)'),
    'PSA30': ('val', 'SA(3.0)'),
    'STDPGA': ('std', 'PGA'),
    'STDMMI': ('std', 'MMI'),
    'STDPSA03': ('std', 'SA(0.3)'),
    'STDPSA10': ('std', 'SA(1.0)'),
    'STDPSA30': ('std', 'SA(3.0)'),
}


def parse_ground_motion_input(request):
    """
    Try and parse a shakemap with the provided object.

    :param request: a shakemap grid file
    :param uncertainty_file: a shakemap uncertainty_file file
    :returns: array with fields lon, lat, vs30, val, std
    """
    # instantiate parsers
    usgs_parser = UsgsShakemapIdParser()
    general_parser = ShakemapParser()

    # build chain of execution
    usgs_parser.set_next(general_parser)
    # general_parser.set_next(new_parser) and so on

    # execute chain and return result
    logging.info("Start parsing ground motion map...")
    return usgs_parser.parse(request)


class GroundMotionInputParser(ABC):
    """
    The Parser interface declares a method for building a chain of Parsers.
    """

    _next_parser: GroundMotionInputParser = None

    def set_next(self, parser: GroundMotionInputParser) -> \
            GroundMotionInputParser:
        """
        Assign a object which will recieve the request and will try
        and parse the request if the current one does not return.
        """
        self._next_parser = parser
        return parser

    @abstractmethod
    def parse(self, request: Any) -> str:
        """
        Overwrite this method to implement a strategy to identify and parse
        the request object.

        This method should never raise an error and end execution but instead
        call its super().parse() function to pass the request on to the next
        function in the Chain.
        """
        if self._next_parser:
            return self._next_parser.parse(request)
        return None


class UsgsShakemapIdParser(GroundMotionInputParser):
    """
    In case a shakemap_id is supplied, the corresponding geojson file is
    parsed and the grid and uncertainty url's are passed on to the next
    method in the chain.
    """

    def parse(self, request: Any) -> str:
        urls = None
        if len(request) == 1 or isinstance(request, str):
            logging.info("Checking if input is a USGS ID...")
            urls = self._get_grid_urls(request)

        if urls:
            request = urls

        return super().parse(request)

    @staticmethod
    def _get_grid_urls(request: Any):
        """
        Read geojson from USGS site for the given ID and extract shakemap files
        """
        if isinstance(request, list):
            request = request[0]
        us_gov = 'https://earthquake.usgs.gov'
        shakemap_url = us_gov + \
            '/fdsnws/event/1/query?eventid={}&format=geojson'
        try:
            r = requests.get(shakemap_url.format(request))
            r = r.json()[
                'properties']['products']['shakemap'][-1]['contents']

            grid = r.get('download/grid.xml')
            uncertainty = r.get(
                'download/uncertainty.xml.zip') or r.get(
                    'download/uncertainty.xml')
            return [grid['url'],
                    uncertainty['url'] if uncertainty else None]

        except Exception as e:
            logging.info('USGS Parser failed with error %s', e)

        return None


class ShakemapParser(GroundMotionInputParser):
    """
    If a list of two paths for shakemaps are supplied, download and try to
    parse those files.
    """

    def parse(self, request: Any) -> str:
        try:
            if isinstance(request, list) and isinstance(request[0], str) \
                    and len(request[0]) > 3 and request[0][-3:] == 'xml':
                logging.info('Trying to parse as shakemap xml file...')
                shakemap_array = None
                if len(request) < 2 or request[1] is None:
                    with urlopen(request[0]) as f:
                        shakemap_array = self._get_shakemap_array(f)
                else:
                    with urlopen(request[0]) as f1, self.url_extract(
                            request[1], 'uncertainty.xml') as f2:
                        shakemap_array = self._get_shakemap_array(f1, f2)
                if shakemap_array is not None:
                    return ShakeMap(shakemap_array)
            # in case shakemap is already supplied as an array
            # (eg. through oq.inputs['shakemap'])
            elif isinstance(request, numpy.ndarray):
                return ShakeMap(request)
        except Exception as e:
            logging.info('ShakemapParser failed with error %s', e)

        return super().parse(request)

    def _get_shakemap_array(self, grid_file, uncertainty_file=None):
        """
        :param grid_file: a shakemap grid file
        :param uncertainty_file: a shakemap uncertainty_file file
        :returns: array with fields lon, lat, vs30, val, std
        """
        data = self.parse_shakemap_file(grid_file)
        if uncertainty_file:
            data2 = self.parse_shakemap_file(uncertainty_file)
            # sanity check: lons and lats must be the same
            for coord in ('lon', 'lat'):
                numpy.testing.assert_equal(data[coord], data2[coord])
            # copy the stddevs from the uncertainty array
            for imt in data2['std'].dtype.names:
                data['std'][imt] = data2['std'][imt]
        return data

    @staticmethod
    def parse_shakemap_file(xml_file):
        """
        A converter from Shakemap files (see https://earthquake.usgs.gov/
        scenario/product/shakemap-scenario/sclegacyshakeout2full_se/us/14
        65655085705/about_formats.html) to numpy composite arrays.

        :param grid_file: a shakemap grid file
        :returns: array with fields lon, lat, vs30, val, std
        """
        if hasattr(xml_file, 'read'):
            data = io.BytesIO(xml_file.read())
        else:
            data = open(xml_file)
        grid_node = node_from_xml(data)
        fields = grid_node.getnodes('grid_field')
        lines = grid_node.grid_data.text.strip().splitlines()
        rows = [line.split() for line in lines]

        # the indices start from 1, hence the -1 below
        idx = {f['name']: int(f['index']) - 1 for f in fields
               if f['name'] in SHAKEMAP_FIELDS}
        out = {name: [] for name in idx}
        for name in idx:
            i = idx[name]
            if name in FIELDMAP:
                out[name].append([float(row[i]) for row in rows])
        dt = sorted((imt[1], F32) for key, imt in FIELDMAP.items()
                    if imt[0] == 'val')
        dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
                  ('val', dt), ('std', dt)]
        data = numpy.zeros(len(rows), dtlist)
        for name, field in sorted(FIELDMAP.items()):
            if name not in out:
                continue
            if isinstance(field, tuple):
                # for ('val', IMT) or ('std', IMT)
                data[field[0]][field[1]] = F32(out[name])
            else:
                # for lon, lat, vs30
                data[field] = F32(out[name])
        return data

    @staticmethod
    def url_extract(url, fname):
        """
        Download and unzip an archive and extract the underlying fname
        """
        if not url.endswith('.zip'):
            return urlopen(url)
        with urlopen(url) as f:
            data = io.BytesIO(f.read())
        with zipfile.ZipFile(data) as z:
            try:
                return z.open(fname)
            except KeyError:
                # for instance the ShakeMap ci3031111 has inside a file
                # data/verified_atlas2.0/reviewed/19920628115739/output/
                # uncertainty.xml
                # instead of just uncertainty.xml
                zinfo = z.filelist[0]
                if zinfo.filename.endswith(fname):
                    return z.open(zinfo)
                else:
                    raise
