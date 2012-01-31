"""
Module :mod:`nhe.source.area` defines :class:`AreaSource`.
"""
from nhe.source.point import PointSource


class AreaSource(PointSource):
    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 polygon, area_discretization, *args, **kwargs):
        super(AreaSource, self).__init__(
            source_id, name, tectonic_region_type, mfd, *args,
            location=None, **kwargs
        )
        self.polygon = polygon
        self.area_discretization = area_discretization

    def iter_ruptures(self, temporal_occurrence_model):
        """
        See :meth:`nhe.source.base.SeismicSource.iter_ruptures`.
        """
        for location in self._discretize_area():
            ruptures_at_location = self._iter_ruptures_at_location(
                temporal_occurrence_model, location
            )
            for rupture in ruptures_at_location:
                yield rupture

    def _discretize_area(self):
        # TODO: implement
        pass
