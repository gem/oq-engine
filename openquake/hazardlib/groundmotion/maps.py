from abc import ABC, abstractmethod
from typing import Any
import logging

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

    def __init__(self, map=None) -> None:
        self._available_imts = []
        self._required_imts = []
        self._ground_motion_map = None
        self._discard_assets = False

        self.set_ground_motion_map(map)

    def set_ground_motion_map(self, map) -> None:
        """
        Save a new ground motion map.

        :param map: ground motion map
        """
        if map is not None:
            self._ground_motion_map = map
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

        if map is None:
            raise IMTsNotAvailable(
                'You need to assign a map before setting required IMTs.')
        elif self.check_available_imts(imts):
            self._required_imts = imts
        else:
            msg = 'The list of the available IMTs is {} ' \
                'but the IMTs {} are required. ' \
                'Please change the risk model otherwise you will have ' \
                'incorrect zero losses for the associated taxonomies'.format(
                    self._available_imts, imts
                )
            if self._discard_assets:
                self._required_imts = imts
                logging.error(msg)
            else:
                raise IMTsNotAvailable(msg)

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

    def associate_site_collection(self, sitecol: SiteCollection,
                                  assoc_distance: int, mode: str) -> Any:
        """
        :param sitecol: a site collection
        :param assoc_dist: the maximum distance for association
        :param mode: 'strict', 'warn' or 'filter'
        :returns: filtered site collection, filtered objects, discarded
        """
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
        pass

    @abstractmethod
    def _calculate_reduced_map(self) -> Any:
        """
        Build a copy of the ground motion map with only the relevant IMTs.

        :returns: Map with only the IMTs specified in '_required_imts'
        """
        pass

    @abstractmethod
    def _calculate_bounding_box(self) -> set:
        """
        Calculate bounding box of current ground motion map.
        :returns: set of coordinates (min(lon), min(lat), max(lon), max(lat))
        """
        pass

    @abstractmethod
    def extract_site_collection(self) -> SiteCollection:
        """
        Create a site collection out of the ground motion map.
        :returns: A valid SiteCollection
        """
        pass

    @abstractmethod
    def _associate_sites(self, sitecol, assoc_distance, mode) -> Any:
        """
        Associate the ground motion map to the site collection.
        :return: filtered site collection, filtered objects (map),
                 discarded objects
        """
        pass
