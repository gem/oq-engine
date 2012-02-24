"""
Module :mod:`nhe.attrel.base` defines base :class:`AttenuationRelationship`.
"""
import abc


class AttenuationRelationship(object):
    """
    Base class for all the Attenuation Relationships --
    GMPEs (ground motion prediction equations) and IPEs
    (intensity prediction equations).

    Subclasses must implement :meth:`get_mean_and_stddevs`
    and all the class attributes with names starting from
    ``DEFINED_FOR`` and ``REQUIRES``.
    """
    __metaclass__ = abc.ABCMeta

    #: Set of :class:`tectonic region types <nhe.const.TRT>` this attenuation
    #: relationship is defined for.
    DEFINED_FOR_TECTONIC_REGION_TYPES = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <nhe.imt>` this attenuation
    #: relationship can calculate. A set should contain classes from
    #: module :mod:`nhe.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = abc.abstractproperty()

    #: Set of :class:`intensity measure component types <nhe.const.IMC>`
    #: this attenuation relationship can calculate mean and standard
    #: deviation for.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS = abc.abstractproperty()

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
    #:     Angle describing the slip propagation on the rupture surface,
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
        """
        Calculate and return mean value of intensity distribution and it's
        standard deviation.

        Method must be implemented by subclasses.

        :param context:
            Instance of :class:`AttRelContext` with parameters of rupture, site
            and their relative position (read, distances) assigned to respective
            attributes. Only those attributes that are listed in class'
            :attr:`REQUIRES_SITE_PARAMETERS`, :attr:`REQUIRES_DISTANCES`
            and :attr:`REQUIRES_RUPTURE_PARAMETERS` are available.
        :param imt:
            An instance (not a class) of intensity measure type.
            See :mod:`nhe.imt`.
        :param stddev_types:
            List of standard deviation types, constants from
            :class:`nhe.const.StdDev`. Method result value should include
            standard deviation values for each of types in this list.
        :param component_type:
            A component of interest of intensity measure. A constant from
            :class:`nhe.const.IMC`.

        :returns:
            Method should return a tuple of two items. First item should be
            a mean value of respective component of a chosen intensity measure
            type and the second should be a list of standard deviation values
            for the same single component of the same single intensity measure
            type, one for each type in ``stddev_types`` parameter, preserving
            the order.

        Combining interface to mean and standard deviation values in a single
        method allows to avoid redoing the same intermediate calculations
        if there are some shared between stddev and mean formulae without
        resorting to keeping any sort of internal state (and effectively
        making attenuation relationship not reenterable).

        However it is advised to split calculation of mean and stddev values
        and make ``get_mean_and_stddevs()`` just combine both (and possibly
        compute interim steps).
        """

    def get_probabilities_of_exceedance(self, ctx, imts, component_type):
        # TODO: document
        # TODO: implement
        raise NotImplementedError()

    @classmethod
    def make_context(cls, site, rupture, distances=None):
        """
        Create a :meth:`AttRelContext` object for given site and rupture.

        This classmethod should be called from an actual attenuation
        relationship implementation, not from the base class.

        :param site:
            Instance of :class:`nhe.site.Site`.
        :param rupture:
            Instance of :class:`~nhe.source.rupture.Rupture` (or its subclass
            :class:`~nhe.source.rupture.ProbabilisticRupture`).
        :param distances:
            If provided should be a dictionary mapping distance types (strings
            like ``'rrup'`` or ``'rjb'``, see :attr:`REQUIRES_DISTANCES`)
            to actual distances between corresponding ``site`` and ``rupture``.
            If this value is not None, it's expected to contain all the
            distance information the attenuation relationship requires,
            those values are used without checks. Otherwise distances will
            be calculated.

        :returns:
            An instance of :class:`AttRelContext` with those (and only those)
            attributes that are required by attenuation relationship filled in.
        """
        # TODO: unittest this
        assert cls is not AttenuationRelationship
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
            setattr(context, attr, value)

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
            setattr(context, attr, value)

        return context


class AttRelContext(object):
    """
    Calculation context for attenuation relationships.

    Instances of this class are passed into
    :meth:`AttenuationRelationship.get_mean_and_stddevs`. They are intended
    to represent relevant features of the site, the rupture and their relative
    position. Every Attenuation relationship class is required to declare what
    :attr:`site <AttenuationRelationship.REQUIRES_SITE_PARAMETERS>`,
    :attr:`rupture <AttenuationRelationship.REQUIRES_RUPTURE_PARAMETERS>`
    and :attr:`distance <AttenuationRelationship.REQUIRES_DISTANCES>`
    information does it need. Only those required parameters are calculated and
    made available in a result of :meth:`AttenuationRelationship.make_context`.
    """
    __slots__ = (
        # site parameters
        'site_vs30 site_vs30type site_z1pt0 site_z2pt5 '
        # rupture parameters
        'rup_mag rup_trt rup_dip rup_rake '
        # distance parameters
        'dist_rrup dist_rx dist_rjb dist_ztor'
    ).split()
