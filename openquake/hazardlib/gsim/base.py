# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.gsim.base` defines base classes for
different kinds of :class:`ground shaking intensity models
<GroundShakingIntensityModel>`.
"""
import abc
import math
import warnings
import functools
import numpy
from scipy.special import ndtr

from openquake.baselib.general import DeprecationWarning
from openquake.hazardlib import imt as imt_module
from openquake.hazardlib import const
from openquake.hazardlib.contexts import KNOWN_DISTANCES
from openquake.hazardlib.contexts import *  # for backward compatibility


ADMITTED_STR_PARAMETERS = ['DEFINED_FOR_TECTONIC_REGION_TYPE',
                           'DEFINED_FOR_INTENSITY_MEASURE_COMPONENT']
ADMITTED_FLOAT_PARAMETERS = ['DEFINED_FOR_REFERENCE_VELOCITY']
ADMITTED_TABLE_PARAMETERS = ['COEFFS_STRESS', 'COEFFS_HARD_ROCK',
                             'COEFFS_SITE_RESPONSE']
ADMITTED_SET_PARAMETERS = ['DEFINED_FOR_INTENSITY_MEASURE_TYPES',
                           'DEFINED_FOR_STANDARD_DEVIATION_TYPES',
                           'REQUIRES_DISTANCES',
                           'REQUIRES_SITES_PARAMETERS',
                           'REQUIRES_RUPTURE_PARAMETERS']

registry = {}  # GSIM name -> GSIM class
gsim_aliases = {}  # populated for instance in nbcc2015_AA13.py


class NotVerifiedWarning(UserWarning):
    """
    Raised when a non verified GSIM is instantiated
    """


class ExperimentalWarning(UserWarning):
    """
    Raised for GMPEs that are intended for experimental use or maybe subject
    to changes in future version.
    """


class AdaptedWarning(UserWarning):
    """
    Raised for GMPEs that are intended for experimental use or maybe subject
    to changes in future version.
    """


def gsim_imt_dt(sorted_gsims, sorted_imts):
    """
    Build a numpy dtype as a nested record with keys 'idx' and nested
    (gsim, imt).

    :param sorted_gsims: a list of GSIM instances, sorted lexicographically
    :param sorted_imts: a list of intensity measure type strings
    """
    dtlist = [(imt, numpy.float32) for imt in sorted_imts]
    imt_dt = numpy.dtype(dtlist)
    return numpy.dtype([(str(gsim), imt_dt) for gsim in sorted_gsims])


def get_mean_std(sctx, rctx, dctx, imts, gsims):
    """
    :returns: an array of shape (2, N, M, G) with means and stddevs
    """
    N = len(sctx.sids)
    M = len(imts)
    G = len(gsims)
    arr = numpy.zeros((2, N, M, G))
    num_tables = CoeffsTable.num_instances
    for g, gsim in enumerate(gsims):
        d = dctx.roundup(gsim.minimum_distance)
        for m, imt in enumerate(imts):
            mean, [std] = gsim.get_mean_and_stddevs(sctx, rctx, d, imt,
                                                    [const.StdDev.TOTAL])
            arr[0, :, m, g] = mean
            arr[1, :, m, g] = std
            if CoeffsTable.num_instances > num_tables:
                raise RuntimeError('Instantiating CoeffsTable inside '
                                   '%s.get_mean_and_stddevs' %
                                   gsim.__class__.__name__)
    return arr


def get_poes(mean_std, loglevels, truncation_level, gsims=()):
    """
    Calculate and return probabilities of exceedance (PoEs) of one or more
    intensity measure levels (IMLs) of one intensity measure type (IMT)
    for one or more pairs "site -- rupture".

    :param mean_std:
        An array of shape (2, N, M, G) with mean and standard deviation for
        the current intensity measure type
    :param loglevels:
        A DictArray imt -> logs of intensity measure levels
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
        have 2d numpy arrays of corresponding PoEs, first dimension
        represents sites and the second represents IMLs.

    :raises ValueError:
        If truncation level is not ``None`` and neither non-negative
        float number, and if ``imts`` dictionary contain wrong or
        unsupported IMTs (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
    """
    if truncation_level is not None and truncation_level < 0:
        raise ValueError('truncation level must be zero, positive number '
                         'or None')
    if len(gsims):
        assert mean_std.shape[-1] == len(gsims)
    tl = truncation_level
    if any(hasattr(gsim, 'weights_signs') for gsim in gsims):
        # implement average get_poes for the nshmp_2014 model
        shp = list(mean_std[0].shape)  # (N, M, G)
        shp[1] = len(loglevels.array)  # L
        arr = numpy.zeros(shp)
        for g, gsim in enumerate(gsims):
            if hasattr(gsim, 'weights_signs'):
                outs = []
                weights, signs = zip(*gsim.weights_signs)
                for s in signs:
                    ms = numpy.array(mean_std[:, :, :, g])  # make a copy
                    for m in range(len(loglevels)):
                        ms[0, :, m] += s * gsim.adjustment
                    outs.append(_get_poes(ms, loglevels, tl, squeeze=1))
                arr[:, :, g] = numpy.average(outs, weights=weights, axis=0)
            else:
                ms = mean_std[:, :, :, g]
                arr[:, :, g] = _get_poes(ms, loglevels, tl, squeeze=1)
        return arr
    else:
        # regular case
        return _get_poes(mean_std, loglevels, truncation_level)


# this is the critical function for the performance of the classical calculator
# it is dominated by memory allocations (i.e. _truncnorm_sf is ultra-fast)
# the only way to speedup is to reduce the maximum_distance, then the array
# will become shorted in the N dimension (number of affected sites)
def _get_poes(mean_std, loglevels, truncation_level, squeeze=False):
    mean, stddev = mean_std  # shape (N, M, G) each
    N, L, G = len(mean), len(loglevels.array), mean.shape[-1]
    out = numpy.zeros((N, L) if squeeze else (N, L, G))
    lvl = 0
    for m, imt in enumerate(loglevels):
        for iml in loglevels[imt]:
            if truncation_level == 0:  # just compare imls to mean
                out[:, lvl] = iml <= mean[:, m]
            else:
                out[:, lvl] = (iml - mean[:, m]) / stddev[:, m]
            lvl += 1
    return _truncnorm_sf(truncation_level, out)


class MetaGSIM(abc.ABCMeta):
    """
    A metaclass converting set class attributes into frozensets, to avoid
    mutability bugs without having to change already written GSIMs. Moreover
    it performs some checks against typos.
    """
    def __new__(meta, name, bases, dic):
        for k, v in dic.items():
            if isinstance(v, set):
                dic[k] = frozenset(v)
                if k == 'REQUIRES_DISTANCES':
                    missing = v - KNOWN_DISTANCES
                    if missing:
                        raise ValueError('Unknown distance %s in %s' %
                                         (missing, name))
        return super().__new__(meta, name, bases, dic)


@functools.total_ordering
class GroundShakingIntensityModel(metaclass=MetaGSIM):
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
    #: Reference to a
    #: :class:`tectonic region type <openquake.hazardlib.const.TRT>` this GSIM
    #: is defined for. One GSIM can implement only one tectonic region type.
    DEFINED_FOR_TECTONIC_REGION_TYPE = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can
    #: calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = abc.abstractproperty()

    #: Reference to a :class:`intensity measure component type
    #: <openquake.hazardlib.const.IMC>` this GSIM can calculate mean
    #: and standard
    #: deviation for.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = abc.abstractproperty()

    #: Set of
    #: :class:`standard deviation types <openquake.hazardlib.const.StdDev>`
    #: this GSIM can calculate.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = abc.abstractproperty()

    #: Set of site parameters names this GSIM needs. The set should include
    #: strings that match names of the attributes of a :class:`site
    #: <openquake.hazardlib.site.Site>` object.
    #: Those attributes are then available in the
    #: :class:`SitesContext` object with the same names.
    REQUIRES_SITES_PARAMETERS = abc.abstractproperty()

    #: Set of rupture parameters (excluding distance information) required
    #: by GSIM. Supported parameters are:
    #:
    #: ``mag``
    #:     Magnitude of the rupture.
    #: ``dip``
    #:     Rupture's surface dip angle in decimal degrees.
    #: ``rake``
    #:     Angle describing the slip propagation on the rupture surface,
    #:     in decimal degrees. See :mod:`~openquake.hazardlib.geo.nodalplane`
    #:     for more detailed description of dip and rake.
    #: ``ztor``
    #:     Depth of rupture's top edge in km. See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_top_edge_depth`.
    #:
    #: These parameters are available from the :class:`RuptureContext` object
    #: attributes with same names.
    REQUIRES_RUPTURE_PARAMETERS = abc.abstractproperty()

    #: Set of types of distance measures between rupture and sites. Possible
    #: values are:
    #:
    #: ``rrup``
    #:     Closest distance to rupture surface.  See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_min_distance`.
    #: ``rjb``
    #:     Distance to rupture's surface projection. See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_joyner_boore_distance`.
    #: ``rx``
    #:     Perpendicular distance to rupture top edge projection.
    #:     See :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_rx_distance`.
    #: ``ry0``
    #:     Horizontal distance off the end of the rupture measured parallel to
    #      strike. See:
    #:     See :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_ry0_distance`.
    #: ``rcdpp``
    #:     Direct point parameter for directivity effect centered on the site- and earthquake-specific
    #      average DPP used. See:
    #:     See :meth:`~openquake.hazardlib.source.rupture.ParametricProbabilisticRupture.get_dppvalue`.
    #: ``rvolc``
    #:     Source to site distance passing through surface projection of volcanic zone
    #:
    #: All the distances are available from the :class:`DistancesContext`
    #: object attributes with same names. Values are in kilometers.
    REQUIRES_DISTANCES = abc.abstractproperty()

    _toml = ''  # set by valid.gsim
    minimum_distance = 0  # set by valid.gsim
    superseded_by = None
    non_verified = False
    experimental = False
    adapted = False
    get_poes = staticmethod(get_poes)

    @classmethod
    def __init_subclass__(cls):
        stddevtypes = cls.DEFINED_FOR_STANDARD_DEVIATION_TYPES
        if not isinstance(stddevtypes, abc.abstractproperty):  # concrete class
            if const.StdDev.TOTAL not in stddevtypes:
                raise ValueError('%s.DEFINED_FOR_STANDARD_DEVIATION_TYPES is '
                                 'not defined for const.StdDev.TOTAL' %
                                 cls.__name__)
            registry[cls.__name__] = cls

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        cls = self.__class__
        if cls.superseded_by:
            msg = '%s is deprecated - use %s instead' % (
                cls.__name__, cls.superseded_by.__name__)
            warnings.warn(msg, DeprecationWarning)
        if cls.non_verified:
            msg = ('%s is not independently verified - the user is liable '
                   'for their application') % cls.__name__
            warnings.warn(msg, NotVerifiedWarning)
        if cls.experimental:
            msg = ('%s is experimental and may change in future versions - '
                   'the user is liable for their application') % cls.__name__
            warnings.warn(msg, ExperimentalWarning)
        if cls.adapted:
            msg = ('%s is not intended for general use and the behaviour '
                   'may not be as expected - '
                   'the user is liable for their application') % cls.__name__
            warnings.warn(msg, AdaptedWarning)

    @abc.abstractmethod
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Calculate and return mean value of intensity distribution and it's
        standard deviation.

        Method must be implemented by subclasses.

        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`
            with parameters of sites
            collection assigned to respective values as numpy arrays.
            Only those attributes that are listed in class'
            :attr:`REQUIRES_SITES_PARAMETERS` set are available.
        :param rup:
            Instance of :class:`openquake.hazardlib.source.rupture.BaseRupture`
            with parameters of a rupture
            assigned to respective values. Only those attributes that are
            listed in class' :attr:`REQUIRES_RUPTURE_PARAMETERS` set are
            available.
        :param dists:
            Instance of :class:`DistancesContext` with values of distance
            measures between the rupture and each site of the collection
            assigned to respective values as numpy arrays. Only those
            attributes that are listed in class' :attr:`REQUIRES_DISTANCES`
            set are available.
        :param imt:
            An instance (not a class) of intensity measure type.
            See :mod:`openquake.hazardlib.imt`.
        :param stddev_types:
            List of standard deviation types, constants from
            :class:`openquake.hazardlib.const.StdDev`.
            Method result value should include
            standard deviation values for each of types in this list.

        :returns:
            Method should return a tuple of two items. First item should be
            a numpy array of floats -- mean values of respective component
            of a chosen intensity measure type, and the second should be
            a list of numpy arrays of standard deviation values for the same
            single component of the same single intensity measure type, one
            array for each type in ``stddev_types`` parameter, preserving
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

    @abc.abstractmethod
    def to_distribution_values(self, values):
        """
        Convert a list or array of values in units of IMT to a numpy array
        of values of intensity measure distribution (like taking the natural
        logarithm for :class:`GMPE`).

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual GSIM implementations.
        """

    @abc.abstractmethod
    def to_imt_unit_values(self, values):
        """
        Convert a list or array of values of intensity measure distribution
        (like ones returned from :meth:`get_mean_and_stddevs`) to values
        in units of IMT. This is the opposite operation
        to :meth:`to_distribution_values`.

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual GSIM implementations.
        """

    def _check_imt(self, imt):
        """
        Make sure that ``imt`` is valid and is supported by this GSIM.
        """
        names = set(f.__name__
                    for f in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES)
        if imt.name not in names:
            raise ValueError('imt %s is not supported by %s' %
                             (imt.name, type(self).__name__))

    def __lt__(self, other):
        """
        The GSIMs are ordered according to string representation
        """
        return str(self) < str(other)

    def __eq__(self, other):
        """
        The GSIMs are equal if their string representations are equal
        """
        return str(self) == str(other)

    def __hash__(self):
        """
        We use the __str__ representation as hash: it means that we can
        use equivalently GSIM instances or strings as dictionary keys.
        """
        return hash(str(self))

    def __repr__(self):
        """
        String representation for GSIM instances in TOML format.
        """
        if self._toml:
            return self._toml
        return '[%s]' % self.__class__.__name__


def _truncnorm_sf(truncation_level, values):
    """
    Survival function for truncated normal distribution.

    Assumes zero mean, standard deviation equal to one and symmetric
    truncation.

    :param truncation_level:
        Positive float number representing the truncation on both sides
        around the mean, in units of sigma, or None, for non-truncation
    :param values:
        Numpy array of values as input to a survival function for the given
        distribution.
    :returns:
        Numpy array of survival function results in a range between 0 and 1.

    >>> from scipy.stats import truncnorm
    >>> truncnorm(-3, 3).sf(0.12345) == _truncnorm_sf(3, 0.12345)
    True
    >>> from scipy.stats import norm
    >>> norm.sf(0.12345) == _truncnorm_sf(None, 0.12345)
    True
    """
    if truncation_level == 0:
        return values

    if truncation_level is None:
        return ndtr(- values)

    # notation from http://en.wikipedia.org/wiki/Truncated_normal_distribution.
    # given that mu = 0 and sigma = 1, we have alpha = a and beta = b.

    # "CDF" in comments refers to cumulative distribution function
    # of non-truncated distribution with that mu and sigma values.

    # assume symmetric truncation, that is ``a = - truncation_level``
    # and ``b = + truncation_level``.

    # calculate CDF of b
    phi_b = ndtr(truncation_level)

    # calculate Z as ``Z = CDF(b) - CDF(a)``, here we assume that
    # ``CDF(a) == CDF(- truncation_level) == 1 - CDF(b)``
    z = phi_b * 2 - 1

    # calculate the result of survival function of ``values``,
    # and restrict it to the interval where probability is defined --
    # 0..1. here we use some transformations of the original formula
    # that is ``SF(x) = 1 - (CDF(x) - CDF(a)) / Z`` in order to minimize
    # number of arithmetic operations and function calls:
    # ``SF(x) = (Z - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(a) - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(x)) / Z``.
    return ((phi_b - ndtr(values)) / z).clip(0.0, 1.0)


class GMPE(GroundShakingIntensityModel):
    """
    Ground-Motion Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` with a distinct feature
    that the intensity values are log-normally distributed.

    Method :meth:`~GroundShakingIntensityModel.get_mean_and_stddevs`
    of actual GMPE implementations is supposed to return the mean
    value as a natural logarithm of intensity.
    """
    def to_distribution_values(self, values):
        """
        Returns numpy array of natural logarithms of ``values``.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # avoid RuntimeWarning: divide by zero encountered in log
            return numpy.log(values)

    def to_imt_unit_values(self, values):
        """
        Returns numpy array of exponents of ``values``.
        """
        return numpy.exp(values)

    def open(self, fname_or_file):
        """
        :param fname_or_file: filename or filelike object
        :returns: the file object
        """
        if hasattr(fname_or_file, 'read'):
            return fname_or_file
        return open(fname_or_file, 'rb')

    def set_parameters(self):
        """
        Combines the parameters of the GMPE provided at the construction level
        with the ones originally assigned to the backbone modified GMPE.
        """
        for key in (ADMITTED_STR_PARAMETERS + ADMITTED_FLOAT_PARAMETERS +
                    ADMITTED_SET_PARAMETERS):
            try:
                val = getattr(self.gmpe, key)
            except AttributeError:
                pass
            else:
                setattr(self, key, val)


class IPE(GroundShakingIntensityModel):
    """
    Intensity Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` which is suitable for
    intensity measures that are normally distributed. In particular,
    for :class:`~openquake.hazardlib.imt.MMI`.
    """
    def to_distribution_values(self, values):
        """
        Returns numpy array of ``values`` without any conversion.
        """
        return numpy.array(values, dtype=float)

    def to_imt_unit_values(self, values):
        """
        Returns numpy array of ``values`` without any conversion.
        """
        return numpy.array(values, dtype=float)


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
    see :mod:`openquake.hazardlib.imt`:

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

    If there are :class:`~openquake.hazardlib.imt.SA` IMTs in the table, they
    are not referenced by name, because they require parametrization:

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

    >>> from openquake.hazardlib import imt
    >>> ct[imt.PGA()] == dict(a=1, b=2.4, c=-5, d=0.01)
    True
    >>> ct[imt.PGD()] == dict(a=7.6, b=12, c=0, d=44.1)
    True
    >>> ct[imt.SA(damping=5, period=0.1)] == dict(a=10, b=20, c=30, d=40)
    True
    >>> ct[imt.PGV()]
    Traceback (most recent call last):
        ...
    KeyError: PGV
    >>> ct[imt.SA(1.0, 4)]
    Traceback (most recent call last):
        ...
    KeyError: SA(1.0, 4)

    Table of coefficients for spectral acceleration could be indexed
    by instances of :class:`openquake.hazardlib.imt.SA` with period
    value that is not specified in the table. The coefficients then
    get interpolated between the ones for closest higher and closest
    lower period. That scaling of coefficients works in a logarithmic
    scale of periods and only within the same damping:

    >>> '%.5f' % ct[imt.SA(period=0.2, damping=5)]['a']
    '7.29073'
    >>> '%.5f' % ct[imt.SA(period=0.9, damping=5)]['c']
    '4.23545'
    >>> '%.5f' % ct[imt.SA(period=5, damping=5)]['c']
    '5.09691'
    >>> ct[imt.SA(period=0.9, damping=15)]
    Traceback (most recent call last):
        ...
    KeyError: SA(0.9, 15)

    Extrapolation is not possible:

    >>> ct[imt.SA(period=0.01, damping=5)]
    Traceback (most recent call last):
        ...
    KeyError: SA(0.01)

    It is also possible to instantiate a table from a tuple of dictionaries,
    corresponding to the SA coefficients and non-SA coefficients:

    >>> coeffs = {imt.SA(0.1): {"a": 1.0, "b": 2.0},
    ...           imt.SA(1.0): {"a": 3.0, "b": 4.0},
    ...           imt.PGA(): {"a": 0.1, "b": 1.0},
    ...           imt.PGV(): {"a": 0.5, "b": 10.0}}
    >>> ct = CoeffsTable(sa_damping=5, table=coeffs)
    """
    num_instances = 0

    def __init__(self, **kwargs):
        if 'table' not in kwargs:
            raise TypeError('CoeffsTable requires "table" kwarg')
        self._coeffs = {}  # cache
        table = kwargs.pop('table')
        self.sa_coeffs = {}
        self.non_sa_coeffs = {}
        sa_damping = kwargs.pop('sa_damping', None)
        if kwargs:
            raise TypeError('CoeffsTable got unexpected kwargs: %r' % kwargs)
        if isinstance(table, str):
            self._setup_table_from_str(table, sa_damping)
        elif isinstance(table, dict):
            for imt in table:
                if imt.name == 'SA':
                    self.sa_coeffs[imt] = table[imt]
                else:
                    self.non_sa_coeffs[imt] = table[imt]
        else:
            raise TypeError("CoeffsTable cannot be constructed with inputs "
                            "of the form '%s'" % table.__class__.__name__)
        self.__class__.num_instances += 1

    def _setup_table_from_str(self, table, sa_damping):
        """
        Builds the input tables from a string definition
        """
        table = table.strip().splitlines()
        header = table.pop(0).split()
        if not header[0].upper() == "IMT":
            raise ValueError('first column in a table must be IMT')
        coeff_names = header[1:]
        for row in table:
            row = row.split()
            imt_name = row[0].upper()
            if imt_name == 'SA':
                raise ValueError('specify period as float value '
                                 'to declare SA IMT')
            imt_coeffs = dict(zip(coeff_names, map(float, row[1:])))
            try:
                sa_period = float(imt_name)
            except Exception:
                if imt_name not in imt_module.registry:
                    raise ValueError('unknown IMT %r' % imt_name)
                imt = imt_module.registry[imt_name]()
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
        or the dictionary of interpolated coefficients, if ``imt`` is
        of type :class:`~openquake.hazardlib.imt.SA` and interpolation
        is possible.

        :raises KeyError:
            If ``imt`` is not available in the table and no interpolation
            can be done.
        """
        try:
            return self._coeffs[imt]
        except KeyError:
            pass
        if imt.name != 'SA':
            self._coeffs[imt] = c = self.non_sa_coeffs[imt]
            return c
        try:
            self._coeffs[imt] = c = self.sa_coeffs[imt]
            return c
        except KeyError:
            pass

        max_below = min_above = None
        for unscaled_imt in list(self.sa_coeffs):
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
        self._coeffs[imt] = c = {
            co: (min_above[co] - max_below[co]) * ratio + max_below[co]
            for co in max_below}
        return c
