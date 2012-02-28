"""
Module :mod:`nhe.attrel.base` defines base :class:`AttenuationRelationship`.
"""
from __future__ import division

import abc

import scipy.stats
import numpy

from nhe import const
from nhe import imt as imt_module


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
    def get_mean_and_stddevs(self, ctx, imt, stddev_types, component_type):
        """
        Calculate and return mean value of intensity distribution and it's
        standard deviation.

        Method must be implemented by subclasses.

        :param ctx:
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

    def get_probabilities_of_exceedance(self, ctx, imts, component_type,
                                        truncation_level):
        """
        Calculate and return probabilities of exceedance of one or more
        intensity measure levels of one or more intensity measure types.

        :param ctx:
            An instance of :class:`AttRelContext` with the same meaning
            as for :meth:`get_mean_and_stddevs`.
        :param imts:
            Dictionary mapping intensity measure type objects (that is,
            instances of classes from :mod:`nhe.imt`) to lists of
            interested intensity measure levels. Those lists contain
            just floats representing the value of intensity exceedance
            of which is of interest.
        :param component_type:
            A component of interest of intensity measure. A constant from
            :class:`nhe.const.IMC`.
        :param truncation_level:
            Can be ``None``, which means that the distribution of intensity
            is treated as Gaussian distribution with possible values ranging
            from minus infinity to plus infinity.

            When set to zero, the mean intensity is treated as an exact
            value (standard deviation is not even computed for that case)
            and resulting array contains 0 in places where IMT is strictly
            lower than the mean value of intensity and 1.0 where IMT is equal
            or greater.

            When truncation level is positive number, the intensity
            distribution is processed as symmetric truncated Gaussian with
            range borders being ``mean - truncation_level * stddev`` and
            ``mean + truncation_level * stddev``. That is, the truncation
            level expresses how far the range borders are from the mean
            value and is defined in units of sigmas. The resulting PoEs
            for that mode are values of complementary cumulative distribution
            function of that truncated Gaussian applied to IMLs.

        :returns:
            A dictionary of the same structure as parameter ``imts`` (see
            above). Instead of lists of IMLs values of the dictionaries
            have numpy arrays of corresponding PoEs.

        :raises ValueError:
            If truncation level is not ``None`` and neither non-negative
            float number, if intensity measure component or rupture's tectonic
            region type is not supported by the attenuation relationship
            (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS` and
            :attr:`DEFINED_FOR_TECTONIC_REGION_TYPES`), if ``imts``
            dictionary contain wrong or unsupported IMTs (see
            :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
        :raises AssertionError:
            If ``truncation_level`` is not zero and attenuation relationship
            doesn't support standard deviation :attr:`~nhe.const.StdDev.TOTAL`.
        """
        if truncation_level is not None and truncation_level < 0:
            raise ValueError('truncation level must be zero, positive number '
                             'or None')

        if not component_type in self.DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS:
            raise ValueError(
                'intensity measure component %r is not supported by %s' %
                (component_type, type(self).__name__)
            )

        for imt in imts.keys():
            if not issubclass(type(imt), imt_module._IMT):
                raise ValueError('keys of imts dictionary must be instances ' \
                                 'of IMT classes')
            if not type(imt) in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES:
                raise ValueError(
                    'intensity measure type %s is not supported by %s' %
                    (type(imt).__name__, type(self).__name__)
                )

        if (hasattr(ctx, 'rup_trt')
                and not ctx.rup_trt in self.DEFINED_FOR_TECTONIC_REGION_TYPES):
            raise ValueError('tectonic region type %r is not supported by %s' %
                             (ctx.rup_trt, type(self).__name__))

        ret = {}
        if truncation_level == 0:
            # zero truncation mode, just compare imls to mean
            for imt, imls in imts.items():
                mean, _ = self.get_mean_and_stddevs(ctx, imt, [],
                                                    component_type)
                ret[imt] = (numpy.array(imls) >= mean).astype(float)
        else:
            # use real normal distribution
            if (not const.StdDev.TOTAL
                    in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES):
                raise AssertionError(
                    '%s does not support TOTAL standard deviation which is '
                    'required for calculating probabilities of exceedance '
                    'with non-zero truncation level' % type(self).__name__
                )
            if truncation_level is None:
                distribution = scipy.stats.norm()
            else:
                distribution = scipy.stats.truncnorm(- truncation_level,
                                                     truncation_level)
            for imt, imls in imts.items():
                mean, [stddev] = self.get_mean_and_stddevs(
                    ctx, imt, [const.StdDev.TOTAL], component_type
                )
                imls = numpy.array(imls, float)
                ret[imt] = distribution.sf((imls - mean) / stddev)

        return ret

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

        :raises AssertionError:
            If called as a method of abstract base class in opposed to
            an actual GMPE/IPE implementation class.
        :raises ValueError:
            If any of declared required parameters (that includes site, rupture
            and distance parameters) are unknown. If tectonic region type
            of the rupture is not supported. If distances dict is provided
            but is missing some of the required distance information.
        """
        if cls is AttenuationRelationship:
            raise AssertionError(
                'make_context() should be called as a specific GMPE/IPE '
                'method, not the abstract base class %s' % cls.__name__
            )
        context = AttRelContext()
        all_ctx_attrs = set(AttRelContext.__slots__)

        if (not rupture.tectonic_region_type
                in cls.DEFINED_FOR_TECTONIC_REGION_TYPES):
            raise ValueError('tectonic region type %r is not supported by %s' %
                             (rupture.tectonic_region_type, cls.__name__))

        for param in cls.REQUIRES_SITE_PARAMETERS:
            attr = 'site_%s' % param
            if not attr in all_ctx_attrs:
                raise ValueError('%s requires unknown site parameter %r' %
                                 (cls.__name__, param))
            setattr(context, attr, getattr(site, param))

        for param in cls.REQUIRES_RUPTURE_PARAMETERS:
            attr = 'rup_%s' % param
            if not attr in all_ctx_attrs:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (cls.__name__, param))
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
            if not attr in all_ctx_attrs:
                raise ValueError('%s requires unknown distance measure %r' %
                                 (cls.__name__, param))
            if distances is not None:
                if not param in distances:
                    raise ValueError("'distances' dict should include all "
                                     "the required distance measures: %s" %
                                     ', '.join(cls.REQUIRES_DISTANCES))
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
