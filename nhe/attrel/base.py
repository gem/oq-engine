"""
Module :mod:`nhe.attrel.base` defines base :class:`AttenuationRelationship`.
"""
import abc


class AttenuationRelationship(object):
    """
    Base class for all the Attenuation Relationships --
    GMPEs (ground motion prediction equations) and IPEs
    (intensity prediction equations).

    Subclasses must implement :meth:`get_mean_and_stddev`
    and all the class attributes with names starting from
    ``DEFINED_FOR`` and ``REQUIRES``.
    """
    __metaclass__ = abc.ABCMeta

    #: The closest and furthest distances between the site and a rupture
    #: this attenuation relationship is defined for. Should be a tuple
    #: of two elements, representing closest and furthest distances in km.
    DEFINED_FOR_DISTANCE_RANGE = abc.abstractproperty()

    #: Set of :class:`tectonic region types <nhe.const.TRT>` this attenuation
    #: relationship is defined for.
    DEFINED_FOR_TECTONIC_REGION_TYPES = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <nhe.imt>` this attenuation
    #: relationship can calculate. A set should contain classes from
    #: module :mod:`nhe.imt`.
    DEFINED_FOR_INTENCITY_MEASURE_TYPES = abc.abstractproperty()

    #: Set of :class:`standard deviation types <nhe.const.StdDev>`
    #: this attenuation relationship can calculate.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = abc.abstractproperty()

    #: Set of site parameters names this attenuation relationship
    #: needs. The set should include strings that match names
    #: of the :class:`site <nhe.site.Site>` object. Those attributes
    #: are then available in the context object with the same names
    #: prefixed with ``site_`` (like ``site_vs30type`` for instance).
    REQUIRES_SITE_PARAMETERS = abc.abstractproperty()

    #: Set of rupture parameters (excluding distance information) required
    #: by attenuation relationship. Supported parameters are:
    #:
    #: ``mag``
    #:     Magnitude of the rupture.
    #: ``trt``
    #:     Rupture's tectonic region type. A constant from
    #:     :class:`nhe.const.TRT`.
    #: ``dip``
    #:     Rupture's surface dip angle in decimal degrees.
    #: ``rake``
    #:     Angle describing the energy propagation from the rupture,
    #:     in decimal degrees. See :mod:`~nhe.geo.nodalplane` for more
    #:     detailed description of dip and rake.
    #:
    #: These parameters are available from the context object attributes
    #: with same names prefixed with ``rup_``.
    REQUIRES_RUPTURE_PARAMETERS = abc.abstractproperty()

    #: Set of types of distance measures between rupture and site. Possible
    #: values are:
    #:
    #: ``rrup``
    #:     Closest distance to rupture surface.
    #:     See :meth:`~nhe.geo.surface.base.BaseSurface.get_min_distance`.
    #: ``rjb``
    #:     Distance to rupture's surface projection. See
    #:     :meth:`~nhe.geo.surface.base.BaseSurface.get_joyner_boore_distance`.
    #: ``rx``
    #:     Perpendicular distance to rupture top edge projection.
    #:     See :meth:`~nhe.geo.surface.base.BaseSurface.get_rx_distance`.
    #: ``ztor``
    #:     Rupture's top edge depth. See
    #:     :meth:`~nhe.geo.surface.base.BaseSurface.get_top_edge_depth`.
    #:
    #: All the distances are available from the context object attributes
    #: with same names prefixed with ``dist_``. Values are in kilometers.
    REQUIRES_DISTANCES = abc.abstractproperty()

    @abc.abstractmethod
    def get_mean_and_stddevs(self, context, imt, stddev_types, component_type):
        # TODO: document
        pass

    def get_probabilities_of_exceedance(self, context, imts, component_type):
        # TODO: document
        # TODO: implement
        raise NotImplementedError()

    @classmethod
    def make_context(cls, site, rupture, distances=None):
        # TODO: document
        # TODO: unittest this
        context = AttRelContext()

        for param in cls.REQUIRES_SITE_PARAMETERS:
            attr = 'site_%s' % param
            if not hasattr(context, attr):
                raise ValueError('site parameter %r is not defined' % param)
            setattr(context, attr, getattr(site, param))

        for param in cls.REQUIRES_RUPTURE_PARAMETERS:
            attr = 'rupture_%s' % param
            if not hasattr(context, attr):
                raise ValueError('rupture parameter %r is not defined' % param)
            if param == 'mag':
                value = rupture.mag
            elif param == 'trt':
                value = rupture.tectonic_region_type
            elif param == 'dip':
                value = rupture.surface.get_dip()
            elif param == 'rake':
                value = rupture.rake
            setattr(context, value)

        for param in cls.REQUIRES_DISTANCES:
            attr = 'dist_%s' % param
            if not hasattr(context, attr):
                raise ValueError('distance %r is not defined' % param)
            if distances is not None:
                value = distances[param]
            else:
                if param == 'rrup':
                    value = rupture.surface.get_min_distance(site.location)
                elif param == 'rx':
                    value = rupture.surface.get_rx_distance(site.location)
                elif param == 'rjb':
                    value = rupture.surface.get_joyner_boore_distance(
                        site.location
                    )
                elif param == 'ztor':
                    value = rupture.surface.get_top_edge_depth()
        return context


class _NotSet(object):
    def die(self, *args, **kwargs):
        raise ValueError('parameter is not set')
    __cmp__ = __eq__ = __ne__ = __len__ = die
NOT_SET = _NotSet()


class AttRelContext(object):
    # TODO: document
    __slots__ = (
        # site parameters
        'site_vs30 site_vs30type site_z1pt0 site_z2pt5 '
        # rupture parameters
        'rup_mag rup_trt rup_dip rup_rake '
        # distance parameters
        'dist_rrup dist_rx dist_rjb dist_ztor'
    ).split()

    def __init__(self):
        # TODO: unittest this and NOT_SET object
        for param in type(self).__slots__:
            setattr(self, param, NOT_SET)
