"""
Module :mod:`nhe.source.rupture` defines classes :class:`Rupture`
and its subclass :class:`ProbabilisticRupture`.
"""
from nhe import const
from nhe.source.base import SourceError


class Rupture(object):
    """
    Rupture object represents a single earthquake rupture.

    :param mag:
        Magnitude of the rupture.
    :param nodal_plane:
        An instance of :class:`nhe.source.nodalplane.NodalPlane` describing
        the orientation of the rupture and it's propagation direction.
    :param tectonic_region_type:
        Rupture's tectonic regime. One of constants in :class:`nhe.const.TRT`.
    :param hypocenter:
        A :class:`~nhe.geo.point.Point`, rupture's hypocenter.
    :param surface:
        An instance of subclass of :class:`~nhe.geo.surface.base.BaseSurface`.
        Object representing the rupture surface geometry.

    :raises SourceError:
        If magnitude value is not positive, hypocenter is above the earth
        surface or tectonic region type is unknown.
    """
    def __init__(self, mag, nodal_plane, tectonic_region_type,
                 hypocenter, surface):
        if not mag > 0:
            raise SourceError('magnitude must be positive')
        if not hypocenter.depth > 0:
            raise SourceError('rupture hypocenter must have positive depth')
        if not const.TRT.is_valid(tectonic_region_type):
            raise SourceError('unknown tectonic region type %r' %
                              tectonic_region_type)
        self.tectonic_region_type = tectonic_region_type
        self.mag = mag
        self.nodal_plane = nodal_plane
        self.hypocenter = hypocenter
        self.surface = surface


class ProbabilisticRupture(Rupture):
    """
    :class:`Rupture` associated with an occurrence rate and a temporal
    occurrence model.

    :param occurrence_rate:
        Number of times rupture happens per year.
    :param temporal_occurrence_model:
        Temporal occurrence model assigned for this rupture. Should
        be an instance of :class:`nhe.tom.PoissonTOM`.

    :raises SourceError:
        If occurrence rate is not positive.
    """
    def __init__(self, mag, nodal_plane, tectonic_region_type,
                 hypocenter, surface,
                 occurrence_rate, temporal_occurrence_model):
        if not occurrence_rate > 0:
            raise SourceError('occurrence rate must be positive')
        super(ProbabilisticRupture, self).__init__(
            mag, nodal_plane, tectonic_region_type, hypocenter, surface
        )
        self.temporal_occurrence_model = temporal_occurrence_model
        self.occurrence_rate = occurrence_rate
