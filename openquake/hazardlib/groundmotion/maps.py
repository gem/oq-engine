from abc import ABC, abstractmethod
from typing import Any
import logging
import numpy

from openquake.hazardlib import geo
from openquake.hazardlib.site import SiteCollection


class IMTsNotAvailable(Exception):
    """One or more of the requested IMTs are not available"""


class GroundMotionMap(ABC):
    """
    Interface for objects to save and manipulate a shakemap.

    To create a new class to save and work with ground motion maps
    you can inherit from this interface and implement the abstract
    methods defined at the end.
    """

    def __init__(self, gmm=None) -> None:
        self._available_imts = []
        self._required_imts = []
        self._ground_motion_map = None
        self._discard_assets = False

        self.set_ground_motion_map(gmm)

    def set_ground_motion_map(self, gmm) -> None:
        """
        Save a new ground motion map.

        :param map: ground motion map
        """
        if gmm is not None:
            self._ground_motion_map = gmm
            self._available_imts = self._calculate_available_imts()
            self.set_required_imts(self._required_imts, self._discard_assets)

    def set_required_imts(self, imts, discard_assets=False) -> None:
        """
        Set required imts for this map. The rest of the IMT information will
        be discarded.

        :param imts: required IMTs as a list of strings
        :param discard_assets: set to zero the risk on assets with missing IMTs
        :raises IMTsNotAvailable: If the required imts are not available
        in the current map.
        """
        self._discard_assets = discard_assets

        if self._ground_motion_map is None:
            raise IMTsNotAvailable(
                'You need to assign a map before setting required IMTs.')
        if self.check_available_imts(imts):
            self._required_imts = imts
        else:
            msg = 'The list of the available IMTs is {} ' \
                'but the IMTs {} are required. ' \
                'Please change the risk model otherwise you will have ' \
                'incorrect zero losses for the associated taxonomies'.format(
                    self._available_imts, imts
                )
            if self._discard_assets:
                self._required_imts = set(
                    imts).intersection(self._available_imts)
                logging.error(msg)
            else:
                raise IMTsNotAvailable(msg)

        # allow _required_imts to be reset
        if len(self._required_imts) > 0:
            self._ground_motion_map = self._calculate_reduced_map()
            self._available_imts = self._calculate_available_imts()

    def check_available_imts(self, requested_imts) -> bool:
        """
        Checks whether all of the requested imts are available in the map

        :param requested_imts: List of the requested imts to be tested.
        :returns: True if all requested items are available, else False
        """
        return set(requested_imts).issubset(set(self._available_imts))

    def associate_site_collection(self, sitecol: SiteCollection = None,
                                  assoc_distance: int = None,
                                  mode: str = 'warn') -> Any:
        """
        :param sitecol: a site collection
        :param assoc_dist: the maximum distance for association
        :param mode: 'strict', 'warn' or 'filter'
        :returns: filtered site collection, filtered objects, discarded
        """
        if sitecol is None:  # extract the sites from the shakemap
            return self.extract_site_collection(), self._ground_motion_map

        bbox = self._calculate_bounding_box()
        indices = sitecol.within_bbox(bbox)
        if len(indices) == 0:
            raise RuntimeError('There are no sites within the bounding box %s'
                               % str(bbox))
        sites = sitecol.filtered(indices)
        logging.info('Associating %d GMVs to %d sites',
                     len(self._ground_motion_map), len(sites))

        return self._associate_sites(sites, assoc_distance, mode)

    @abstractmethod
    def _calculate_available_imts(self) -> list:
        """
        Extract a list of available imts from the current map.

        :returns: List of strings with the names of the available imts
        """

    @abstractmethod
    def _calculate_reduced_map(self) -> Any:
        """
        Build a copy of the ground motion map with only the relevant IMTs.

        :returns: Map with only the IMTs specified in '_required_imts'
        """

    @abstractmethod
    def _calculate_bounding_box(self) -> set:
        """
        Calculate bounding box of current ground motion map.
        :returns: set of coordinates (min(lon), min(lat), max(lon), max(lat))
        """

    @abstractmethod
    def extract_site_collection(self) -> SiteCollection:
        """
        Create a site collection out of the ground motion map.
        :returns: A valid SiteCollection
        """

    @abstractmethod
    def _associate_sites(self, sitecol, assoc_distance, mode) -> Any:
        """
        Associate the ground motion map to the site collection.
        :return: filtered site collection, filtered objects (map),
                 discarded objects
        """


class ShakeMap(GroundMotionMap):
    """
    Class to interact with a ground motion map parsed from a ShakeMap format.
    """

    def _calculate_available_imts(self) -> list:
        return list(self._ground_motion_map['val'].dtype.names)

    def _calculate_reduced_map(self) -> None:
        F32 = numpy.float32

        # build a copy of the ShakeMap with only the relevant IMTs
        dt = [(imt, F32) for imt in sorted(self._required_imts)]
        dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
                  ('val', dt), ('std', dt)]
        data = numpy.zeros(len(self._ground_motion_map), dtlist)
        for name in ('lon',  'lat', 'vs30'):
            data[name] = self._ground_motion_map[name]
        for name in ('val', 'std'):
            for im in self._required_imts:
                if im in self._ground_motion_map[name].dtype.names:
                    data[name][im] = self._ground_motion_map[name][im]

        return data

    def extract_site_collection(self) -> SiteCollection:
        return SiteCollection.from_shakemap(self._ground_motion_map)

    def _calculate_bounding_box(self) -> set:
        bbox = (self._ground_motion_map['lon'].min(),
                self._ground_motion_map['lat'].min(),
                self._ground_motion_map['lon'].max(),
                self._ground_motion_map['lat'].max())
        return bbox

    def _associate_sites(self, sitecol, assoc_distance, mode) -> Any:
        return geo.utils.assoc(self._ground_motion_map, sitecol,
                               assoc_distance, mode)
