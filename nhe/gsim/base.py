"""
Module :mod:`nhe.gsim.base` defines base classes for different kinds
of :class:`ground shaking intensity models <GroundShakingIntensityModel>`.
"""
from __future__ import division

import abc
import math

import scipy.stats
import numpy

from nhe import const
from nhe import imt as imt_module


class GroundShakingIntensityModel(object):
    """
    Base class for all the ground shaking intensity models.

    A Ground Shaking Intensity Model (GSIM) defines a set of equations
    for computing mean and standard deviation of a Normal distribution
    representing the variability of an intensity measure (or of its logarithm)
    at a site given an earthquake rupture.

    This class is not intended to be subclassed directly, instead
    the actual GSIMs should subclass either :class:`GMPE` or :class:`IPE`.

    Subclasses of both must implement :meth:`get_mean_and_stddevs`
    and all the class attributes with names starting from ``DEFINED_FOR``
    and ``REQUIRES``.
    """
    __metaclass__ = abc.ABCMeta

    #: Set of :class:`tectonic region types <nhe.const.TRT>` this GSIM
    #: is defined for.
    DEFINED_FOR_TECTONIC_REGION_TYPES = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <nhe.imt>` this GSIM can calculate.
    #: A set should contain classes from module :mod:`nhe.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = abc.abstractproperty()

    #: Set of :class:`intensity measure component types <nhe.const.IMC>`
    #: this GSIM can calculate mean and standard deviation for.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS = abc.abstractproperty()

    #: Set of :class:`standard deviation types <nhe.const.StdDev>`
    #: this GSIM can calculate.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = abc.abstractproperty()

    #: Set of site parameters names this GSIM needs. The set should include
    #: strings that match names of the :class:`site <nhe.site.Site>` object.
    #: Those attributes are then available in the context object with the same
    #: names prefixed with ``site_`` (like ``site_vs30`` for instance).
    REQUIRES_SITE_PARAMETERS = abc.abstractproperty()

    #: Set of rupture parameters (excluding distance information) required
    #: by GSIM. Supported parameters are:
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
            Instance of :class:`GSIMContext` with parameters of rupture, site
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
        making GSIM not reenterable).

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
            An instance of :class:`GSIMContext` with the same meaning
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
            by the GSIM (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_COMPONENTS`)
            and if ``imts`` dictionary contain wrong or unsupported IMTs (see
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
        so there is no need to override it in actual GSIM implementations.
        """

    def make_context(self, site, rupture, distances=None):
        """
        Create a :meth:`GSIMContext` object for given site and rupture.

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
            distance information the GSIM requires, those values are used
            without checks. Otherwise distances will be calculated.

        :returns:
            An instance of :class:`GSIMContext` with those (and only those)
            attributes that are required by GSIM filled in.

        :raises ValueError:
            If any of declared required parameters (that includes site, rupture
            and distance parameters) is unknown. If distances dict is provided
            but is missing some of the required distance information.
        """
        context = GSIMContext()
        all_ctx_attrs = set(GSIMContext.__slots__)

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


class GMPE(GroundShakingIntensityModel):
    """
    Ground-Motion Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` with a distinct feature
    that the intensity values are log-normally distributed.

    Method :meth:`~GroundShakingIntensityModel.get_mean_and_stddevs`
    of actual GMPE implementations is supposed to return the mean
    value as a natural logarithm of intensity.
    """
    def _convert_imls(self, imls):
        """
        Returns numpy array of natural logarithms of ``imls``.
        """
        return numpy.log(imls)


class IPE(GroundShakingIntensityModel):
    """
    Intensity Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` which is suitable for
    intensity measures that are normally distributed. In particular,
    for :class:`~nhe.imt.MMI`.
    """
    def _convert_imls(self, imls):
        """
        Returns numpy array of ``imls`` without any conversion.
        """
        return numpy.array(imls, dtype=float)


class GSIMContext(object):
    """
    Calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are intended
    to represent relevant features of the site, the rupture and their relative
    position. Every GSIM class is required to declare what
    :attr:`site <GroundShakingIntensityModel.REQUIRES_SITE_PARAMETERS>`,
    :attr:`rupture <GroundShakingIntensityModel.REQUIRES_RUPTURE_PARAMETERS>`
    and :attr:`distance <GroundShakingIntensityModel.REQUIRES_DISTANCES>`
    information does it need. Only those required parameters are calculated
    and made available in a result
    of :meth:`GroundShakingIntensityModel.make_context`.
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
    literal (heading and trailing whitespace does not matter). The first column
    in the table must be named "IMT" (or "imt") and thus should represent IMTs:

    >>> CoeffsTable(table='''imf z
    ...                      pga 1''')
    Traceback (most recent call last):
        ...
    ValueError: first column in a table must be IMT

    Names of other columns are used as coefficients dicts keys. The values
    in the first column should correspond to real intensity measure types,
    see :mod:`nhe.imt`:

    >>> CoeffsTable(table='''imt  z
    ...                      pgx  2''')
    Traceback (most recent call last):
        ...
    ValueError: unknown IMT 'PGX'

    Note that :class:`CoeffsTable` only accepts keyword argumets:

    >>> CoeffsTable()
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable requires "table" kwarg
    >>> CoeffsTable(table='', foo=1)
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable got unexpected kwargs: {'foo': 1}

    If there are :class:`~nhe.imt.SA` IMTs in the table, they are not
    referenced by name, because they require parametrization:

    >>> CoeffsTable(table='''imt  x
    ...                      sa   15''')
    Traceback (most recent call last):
        ...
    ValueError: specify period as float value to declare SA IMT
    >>> CoeffsTable(table='''imt  x
    ...                      0.1  20''')
    Traceback (most recent call last):
        ...
    TypeError: attribute "sa_damping" is required for tables defining SA

    So proper table defining SA looks like this:

    >>> ct = CoeffsTable(sa_damping=5, table='''
    ...     imt   a    b     c   d
    ...     pga   1    2.4  -5   0.01
    ...     pgd  7.6  12     0  44.1
    ...     0.1  10   20    30  40
    ...     1.0   1    2     3   4
    ...     10    2    4     6   8
    ... ''')

    Table objects could be indexed by IMT objects (this returns a dictionary
    of coefficients):

    >>> from nhe import imt
    >>> ct[imt.PGA()] == dict(a=1, b=2.4, c=-5, d=0.01)
    True
    >>> ct[imt.PGD()] == dict(a=7.6, b=12, c=0, d=44.1)
    True
    >>> ct[imt.SA(damping=5, period=0.1)] == dict(a=10, b=20, c=30, d=40)
    True
    >>> ct[imt.PGV()]
    Traceback (most recent call last):
        ...
    KeyError: PGV()
    >>> ct[imt.SA(1.0, 4)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=1.0, damping=4)

    Table of coefficients for spectral acceleration could be indexed
    by instances of :class:`nhe.imt.SA` with period value that is not specified
    in the table. The coefficients then get interpolated between the ones for
    closest higher and closest lower period. That scaling of coefficients works
    in a logarithmic scale of periods and only within the same damping:

    >>> '%.5f' % ct[imt.SA(period=0.2, damping=5)]['a']
    '7.29073'
    >>> '%.5f' % ct[imt.SA(period=0.9, damping=5)]['c']
    '4.23545'
    >>> '%.5f' % ct[imt.SA(period=5, damping=5)]['c']
    '5.09691'
    >>> ct[imt.SA(period=0.9, damping=15)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=0.9, damping=15)

    Extrapolation is not possible:

    >>> ct[imt.SA(period=0.01, damping=5)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=0.01, damping=5)
    """
    def __init__(self, **kwargs):
        if not 'table' in kwargs:
            raise TypeError('CoeffsTable requires "table" kwarg')
        table = kwargs.pop('table').strip().splitlines()
        sa_damping = kwargs.pop('sa_damping', None)
        if kwargs:
            raise TypeError('CoeffsTable got unexpected kwargs: %r' % kwargs)
        header = table.pop(0).split()
        if not header[0].upper() == "IMT":
            raise ValueError('first column in a table must be IMT')
        coeff_names = header[1:]
        self.sa_coeffs = {}
        self.non_sa_coeffs = {}
        for row in table:
            row = row.split()
            imt_name = row[0].upper()
            if imt_name == 'SA':
                raise ValueError('specify period as float value '
                                 'to declare SA IMT')
            imt_coeffs = dict(zip(coeff_names, map(float, row[1:])))
            try:
                sa_period = float(imt_name)
            except:
                if not hasattr(imt_module, imt_name):
                    raise ValueError('unknown IMT %r' % imt_name)
                imt = getattr(imt_module, imt_name)()
                self.non_sa_coeffs[imt] = imt_coeffs
            else:
                if sa_damping is None:
                    raise TypeError('attribute "sa_damping" is required '
                                    'for tables defining SA')
                imt = imt_module.SA(sa_period, sa_damping)
                self.sa_coeffs[imt] = imt_coeffs

    def __getitem__(self, imt):
        """
        Return a dictionary of coefficients corresponding to ``imt``
        from this table (if there is a line for requested IMT in it),
        or the dictionary of interpolated coefficients, if ``imt``
        is of type :class:`~nhe.imt.SA` and interpolation is possible.

        :raises KeyError:
            If ``imt`` is not available in the table and no interpolation
            can be done.
        """
        if not isinstance(imt, imt_module.SA):
            return self.non_sa_coeffs[imt]

        try:
            return self.sa_coeffs[imt]
        except KeyError:
            pass

        max_below = min_above = None
        for unscaled_imt in self.sa_coeffs.keys():
            if unscaled_imt.damping != imt.damping:
                continue
            if unscaled_imt.period > imt.period:
                if min_above is None or unscaled_imt.period < min_above.period:
                    min_above = unscaled_imt
            elif unscaled_imt.period < imt.period:
                if max_below is None or unscaled_imt.period > max_below.period:
                    max_below = unscaled_imt
        if max_below is None or min_above is None:
            raise KeyError(imt)

        # ratio tends to 1 when target period tends to a minimum
        # known period above and to 0 if target period is close
        # to maximum period below.
        ratio = ((math.log(imt.period) - math.log(max_below.period))
                 / (math.log(min_above.period) - math.log(max_below.period)))
        max_below = self.sa_coeffs[max_below]
        min_above = self.sa_coeffs[min_above]
        return dict(
            (co, (min_above[co] - max_below[co]) * ratio + max_below[co])
            for co in max_below.keys()
        )
