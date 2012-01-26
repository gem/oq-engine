"""
Module :mod:`nhe.source.base` defines a base class for seismic sources.
"""
import abc

from nhe import const


class SourceError(Exception):
    """
    An error happened during creation of seismic source or earthquake rupture
    object.
    """

class SeismicSource(object):
    """
    Seismic Source is an object representing geometry and activity rate
    of a structure generating seismicity.

    :param source_id:
        Some (numeric or literal) source identifier. Supposed to be unique
        within the source model.
    :param name:
        String, a human-readable name of the source.
    :param tectonic_region_type:
        Source's tectonic regime. See :class:`const.TRT`.
    :param mfd:
        Magnitude-Frequency distribution for the source. See :mod:`nhe.mfd`.
    :raises SourceError:
        If ``tectonic_region_type`` is wrong/unknown.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, source_id, name, tectonic_region_type, mfd):
        if not const.TRT.is_valid(tectonic_region_type):
            raise SourceError('unknown tectonic region type %r' %
                              tectonic_region_type)
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.mfd = mfd

    @abc.abstractmethod
    def iter_ruptures(self, temporal_occurrence_model):
        """
        Get a generator object that yields ruptures the source consists of.

        :param temporal_occurrence_model:
            Temporal occurrence model (supposedly
            :class:`nhe.common.tom.PoissonTOM`). It is passed intact
            to the probabilistic rupture constructor.
        :returns:
            Generator of instances of :class:`ProbabilisticRupture`.
        """


class Rupture(object):
    """
    Rupture object represents a single earthquake rupture.

    :param mag:
        Magnitude of the rupture.
    :param nodal_plane:
        An instance of :class:`nhe.common.nodalplane.NodalPlane` describing
        the orientation of the rupture and it's propagation direction.
    :param tectonic_region_type:
        Rupture's tectonic regime. One of constants in :class:`nhe.const.TRT`.
    :param hypocenter:
        A :class:`~nhe.common.geo.Point`, rupture's hypocenter.
    :param surface:
        An instance of subclass of :class:`nhe.surface.base.BaseSurface`.
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
        be an instance of :class:`nhe.common.tom.PoissonTOM`.

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
