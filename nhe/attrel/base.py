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
    Base class for all the Attenuation Relationships.

    This class is not intended to be subclassed directly, instead
    the actual attenuation relationships should subclass either
    :class:`GMPE` or :class:`IPE`.

    Subclasses of both must implement :meth:`get_mean_and_stddevs`
    and all the class attributes with names starting from ``DEFINED_FOR``
    and ``REQUIRES``.
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
    #: prefixed with ``site_`` (like ``site_vs30`` for instance).
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

    def get_poes(self, ctx, imts, component_type, truncation_level):
        """
        Calculate and return probabilities of exceedance (PoEs) of one or more
        intensity measure levels (IMLs) of one or more intensity measure types
        (IMTs).

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
            float number, if intensity measure component is not supported
            by the attenuation relationship (see
            :attr:`DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS`) and if ``imts``
            dictionary contain wrong or unsupported IMTs (see
            :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
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

        ret = {}
        if truncation_level == 0:
            # zero truncation mode, just compare imls to mean
            for imt, imls in imts.items():
                imls = self._convert_imls(imls)
                mean, _ = self.get_mean_and_stddevs(ctx, imt, [],
                                                    component_type)
                ret[imt] = (imls >= mean).astype(float)
        else:
            # use real normal distribution
            assert (const.StdDev.TOTAL
                    in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
            if truncation_level is None:
                distribution = scipy.stats.norm()
            else:
                distribution = scipy.stats.truncnorm(- truncation_level,
                                                     truncation_level)
            for imt, imls in imts.items():
                imls = self._convert_imls(imls)
                mean, [stddev] = self.get_mean_and_stddevs(
                    ctx, imt, [const.StdDev.TOTAL], component_type
                )
                ret[imt] = distribution.sf((imls - mean) / stddev)

        return ret

    @abc.abstractmethod
    def _convert_imls(self, imls):
        """
        Convert a list of IML values to a numpy array and convert the actual
        values with respect to intensity measure distribution (like taking
        the natural logarithm for :class:`GMPE`).

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual attenuation relationship
        implementations.
        """

    def make_context(self, site, rupture, distances=None):
        """
        Create a :meth:`AttRelContext` object for given site and rupture.

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

        :raises ValueError:
            If any of declared required parameters (that includes site, rupture
            and distance parameters) is unknown. If distances dict is provided
            but is missing some of the required distance information.
        """
        context = AttRelContext()
        all_ctx_attrs = set(AttRelContext.__slots__)

        clsname = type(self).__name__

        for param in self.REQUIRES_SITE_PARAMETERS:
            attr = 'site_%s' % param
            if not attr in all_ctx_attrs:
                raise ValueError('%s requires unknown site parameter %r' %
                                 (clsname, param))
            setattr(context, attr, getattr(site, param))

        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            attr = 'rup_%s' % param
            if not attr in all_ctx_attrs:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (clsname, param))
            if param == 'mag':
                value = rupture.mag
            elif param == 'trt':
                value = rupture.tectonic_region_type
            elif param == 'dip':
                value = rupture.surface.get_dip()
            elif param == 'rake':
                value = rupture.rake
            setattr(context, attr, value)

        for param in self.REQUIRES_DISTANCES:
            attr = 'dist_%s' % param
            if not attr in all_ctx_attrs:
                raise ValueError('%s requires unknown distance measure %r' %
                                 (clsname, param))
            if distances is not None:
                if not param in distances:
                    raise ValueError("'distances' dict should include all "
                                     "the required distance measures: %s" %
                                     ', '.join(self.REQUIRES_DISTANCES))
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


class GMPE(AttenuationRelationship):
    """
    Ground-Motion Prediction Equation is a subclass of generic
    :class:`AttenuationRelationship` with a distinct feature that
    the intensity values are log-normally distributed.

    Method :meth:`~AttenuationRelationship.get_mean_and_stddevs`
    of actual GMPE implementations is supposed to return the mean
    value as a natural logarithm of intensity.
    """
    def _convert_imls(self, imls):
        """
        Returns numpy array of natural logarithms of ``imls``.
        """
        return numpy.log(imls)


class IPE(AttenuationRelationship):
    """
    Intensity Prediction Equation is a subclass of generic
    :class:`AttenuationRelationship` which is suitable for intensity measures
    that are normally distributed. In particular, for :class:`~nhe.imt.MMI`.
    """
    def _convert_imls(self, imls):
        """
        Returns numpy array of ``imls`` without any conversion.
        """
        return numpy.array(imls, dtype=float)


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
        'site_vs30 site_vs30measured site_z1pt0 site_z2pt5 '
        # rupture parameters
        'rup_mag rup_trt rup_dip rup_rake '
        # distance parameters
        'dist_rrup dist_rx dist_rjb dist_ztor'
    ).split()


class CoeffsTable(object):
    r"""
    Instances of :class:`CoeffsTable` encapsulate tables of coefficients
    corresponding to different IMTs.

    Tables are defined in a space-separated tabular form in a simple string
    literal (heading and trailing whitespace does not matter):

    >>> ct = CoeffsTable('''
    ...     imt  a    b   c    d
    ...     pga  1   2.4 -5  0.01
    ...     pgd 7.6  12   0  44.1
    ... ''')

    The first column in the table must be named "IMT" (or "imt") and thus
    should represent IMTs:

    >>> ct = CoeffsTable('imf z\n' 'pga 1\n ')
    Traceback (most recent call last):
        ...
    ValueError: first column in a table must be IMT

    Names of other columns are used as coefficients dicts keys. The values
    in the first column should correspond to real intensity measure types,
    see :mod:`nhe.imt`:

    >>> ct = CoeffsTable('imt z\n' 'pgx 2')
    Traceback (most recent call last):
        ...
    ValueError: unknown IMT 'PGX'

    Table objects could be indexed by IMT objects (this returns a dictionary
    of coefficients):

    >>> from nhe import imt
    >>> ct[imt.PGA()] == dict(a=1, b=2.4, c=-5, d=0.01)
    True
    >>> ct[imt.PGD()] == dict(a=7.6, b=12, c=0, d=44.1)
    True
    >>> ct[imt.PGV()]  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    KeyError: <nhe.imt.PGV object at 0x...>

    Separate tables can be merged one into another, see :meth:`update`:

    >>> ct2 = CoeffsTable('imt x\n' 'pgv 10')
    >>> ct.update(ct2)  # here we merge ct2 into ct,
    >>> ct[imt.PGV()]  # so ct now has coeffs for PGV
    {'x': 10.0}
    """
    _METACOLUMNS = ['IMT']

    _IMT_CLASSES_BY_NAME = dict((cls.__name__, cls)
                                for cls in imt_module._IMT.__subclasses__())

    def __init__(self, table):
        table = table.strip().splitlines()
        header = table.pop(0).split()
        meta = slice(len(self._METACOLUMNS))
        data = slice(len(self._METACOLUMNS), None)
        metacolumns = header[meta]
        if not [col.upper() for col in metacolumns] == self._METACOLUMNS:
            if len(self._METACOLUMNS) == 1:
                raise ValueError('first column in a table must be %s' %
                                 tuple(self._METACOLUMNS))
            else:
                raise ValueError('first %s columns must be %s' %
                                 (len(self._METACOLUMNS),
                                  (', '.join(self._METACOLUMNS)).lower()))
        coeff_names = header[data]
        coeffs = {}
        for row in table:
            row = row.split()
            if not row:
                continue
            imt = self._imt_from_metacolumns(*row[meta])
            coeffs[imt] = dict(zip(coeff_names, map(float, row[data])))
        self.coeffs = coeffs

    def _imt_from_metacolumns(self, imt_name):
        imt_name = imt_name.upper()
        if not imt_name in self._IMT_CLASSES_BY_NAME:
            raise ValueError('unknown IMT %r' % imt_name)
        return self._IMT_CLASSES_BY_NAME[imt_name]()

    def __getitem__(self, imt):
        """
        Return a dictionary of coefficients corresponding to ``imt``.

        :raises KeyError:
            If ``imt`` is not listed in the original table.
        """
        return self.coeffs[imt]

    def update(self, other_table):
        """
        Merge values from other instance of :class:`CoeffsTable` into this one.
        This makes coefficients that were only in ``other_table`` available
        in the one whose method :meth:`update` was called and override the
        coefficients that were in both. So it works the same way as python
        dictionaries' ``update()`` method does.
        """
        self.coeffs.update(other_table.coeffs)


class SACoeffsTable(CoeffsTable):
    """
    Table of coefficients specific to :class:`spectral acceleration
    <nhe.imt.SA>` IMT -- considers that SA values are always parametrized
    by values of period and damping.

    Tables for spectral acceleration are created the same way
    as :class:`CoeffsTable`, the only difference is that first two columns
    should be "period" and "damping" -- these values are used for creating
    :class:`~nhe.imt.SA` object corresponding to the row.

    >>> ct = SACoeffsTable('''period damping alpha beta
    ...                       10.0     5      0.1  -10.3
    ...                       20.0     5      1.1  -20.3
    ...                       11.0    10      4     0
    ...                       19.0    10      40  -30''')
    >>> SACoeffsTable('''period foo bar
    ...                   1     2    3''')
    Traceback (most recent call last):
        ...
    ValueError: first 2 columns must be period, damping

    For exact values of period and damping indexing of:class:`SACoeffsTable`
    works the same way as :class:`CoeffsTable`, just returns the coefficients
    dictionary:

    >>> from nhe.imt import SA
    >>> ct[SA(period=10, damping=5)] == {'alpha': 0.1, 'beta': -10.3}
    True
    >>> ct[SA(period=19, damping=10)] == {'alpha': 40.0, 'beta': -30.0}
    True

    Table of coefficients for spectral acceleration could be indexed
    by instances of :class:`nhe.imt.SA` with period value that is not specified
    in the table. The coefficients then get interpolated between the ones for
    closest higher and closest lower period. That scaling of coefficients works
    only within the same damping:

    >>> ct[SA(period=11, damping=5)] == {'alpha': 0.2, 'beta': -11.3}
    True
    >>> ct[SA(period=15, damping=5)] == {'alpha': 0.6, 'beta': -15.3}
    True

    Extrapolation is not possible:

    >>> ct[SA(period=0.5, damping=5)]
    Traceback (most recent call last):
        ...
    KeyError: 'could not find nor scale coeffs for damping 5 and period 0.5'
    """
    _METACOLUMNS = ['PERIOD', 'DAMPING']

    def _imt_from_metacolumns(self, period, damping):
        return imt_module.SA(float(period), float(damping))

    def __getitem__(self, imt):
        """
        Works the same as :class:`CoeffsTable` for IMTs other than
        :class:`~nhe.imt.SA` and for spectral acceleration of known
        (listed in the table) period and damping.

        If the requested ``imt`` is of type SA and is missing from the
        table, the linear interpolation across values of the same damping
        and smallest period above and largest below requested.
        """
        if not isinstance(imt, imt_module.SA) or imt in self.coeffs:
            return self.coeffs[imt]

        max_below = min_above = None
        for unscaled_imt in self.coeffs.keys():
            if unscaled_imt.damping != imt.damping:
                continue
            if unscaled_imt.period > imt.period:
                if min_above is None or unscaled_imt.period < min_above.period:
                    min_above = unscaled_imt
            elif unscaled_imt.period < imt.period:
                if max_below is None or unscaled_imt.period > max_below.period:
                    max_below = unscaled_imt
        if max_below is None or min_above is None:
            raise KeyError(
                'could not find nor scale coeffs for damping %s and period %s'
                % (imt.damping, imt.period)
            )

        # ratio tends to 1 when target period tends to a minimum
        # known period above and to 0 if target period is close
        # to maximum period below.
        ratio = (imt.period - max_below.period) / (min_above.period
                                                   - max_below.period)
        max_below = self.coeffs[max_below]
        min_above = self.coeffs[min_above]
        return dict(
            (co, (min_above[co] - max_below[co]) * ratio + max_below[co])
            for co in max_below.keys()
        )
