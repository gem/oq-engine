# The Hazard Library
# Copyright (C) 2012-2016 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.base` defines a base class for
seismic sources.
"""
import abc
import numpy
from decimal import Decimal
from openquake.baselib.slots import with_slots
from openquake.baselib.python3compat import with_metaclass


class SourceGroupCollection(object):
    """
    :param grp_list:
        A list of :class:`openquake.hazardlib.source.base.SourceGroup`
        instances
    :param name:
        The name of the group
    :param grp_interdep:
        Interdependence between groups of sources can be either 'indep' or
        'mutex'.
    """
    def __init__(self, grp_list, name='', grp_interdep='indep'):
        # checks
        assert isinstance(grp_list, list), grp_list
        if grp_interdep not in ['indep', 'mutex']:
            raise ValueError('group interdependence incorrect %s ' %
                             grp_interdep)
        # set instance parameters
        self.grp_list = grp_list
        self.name = name
        self.grp_interdep = grp_interdep

    def __iter__(self):
        return iter(self.grp_list)


class SourceGroup(object):
    """
    :param src_list:
        A list containing seismic sources
    :param name:
        The name of the group
    :param src_interdep:
        A string specifying if the sources in this cluster are independent or
        mutually exclusive
    :param rup_indep:
        A string specifying if the ruptures within each source of the cluster
        are independent or mutually exclusive
    :param weights:
        A dictionary whose keys are the source IDs of the cluster and the
        values are the weights associated with each source
    :param checkw:
        Flag controlling the verification of weights assigned to the sources
        in the group
    """

    @property
    def source_id(self):
        """Name of the source group"""
        # alias useful for the write_source_model function
        return self.name

    def __init__(self, src_list, name, src_interdep='indep',
                 rup_interdep='indep', srcs_weights=None, trt='', checkw=True):
        # checks
        self._check_init_variables(src_list, name, src_interdep, rup_interdep,
                                   srcs_weights, checkw)
        # set instance parameters
        self.src_list = src_list
        self.name = name
        self.src_interdep = src_interdep
        self.rup_interdep = rup_interdep
        if srcs_weights is None:
            self.srcs_weights = numpy.ones([len(src_list)])
            self.srcs_weights[0:-2] = Decimal(1./len(src_list))
            self.srcs_weights[-1] = 1 - numpy.sum(self.srcs_weights[0:-2])
        else:
            self.srcs_weights = srcs_weights
        self.tectonic_region_type = trt

    def _check_init_variables(self, src_list, name, src_interdep, rup_interdep,
                              srcs_weights, checkw):
        assert isinstance(src_list, list)
        # check source interdependence
        try:
            assert set(['indep', 'mutex']) & set([src_interdep])
        except:
            raise ValueError('source interdependence incorrect %s ' %
                             src_interdep)
        # check rupture interdependence definition
        assert set(['indep', 'mutex']) & set([rup_interdep])
        # check srcs weights defined by the user
        if srcs_weights is not None:
            if isinstance(srcs_weights, dict):
                import pdb; pdb.set_trace()
            # Check weights
            if checkw:
                assert abs(1. - sum(map(float, srcs_weights))) < 1e-6

    def __iter__(self):
        return iter(self.src_list)


@with_slots
class BaseSeismicSource(with_metaclass(abc.ABCMeta)):
    """
    Base class representing a seismic source, that is a structure generating
    earthquake ruptures.

    :param source_id:
        Some (numeric or literal) source identifier. Supposed to be unique
        within the source model.
    :param name:
        String, a human-readable name of the source.
    :param tectonic_region_type:
        Source's tectonic regime. See :class:`openquake.hazardlib.const.TRT`.
    """

    _slots_ = ['source_id', 'name', 'tectonic_region_type',
               'src_group_id', 'num_ruptures', 'seed', 'id']

    MODIFICATIONS = abc.abstractproperty()

    RUPTURE_WEIGHT = 1.  # overridden in PointSource

    @property
    def weight(self):
        """
        Determine the source weight from the number of ruptures, by
        multiplying with the scale factor RUPTURE_WEIGHT
        """
        return self.num_ruptures * self.RUPTURE_WEIGHT

    def __init__(self, source_id, name, tectonic_region_type):
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.src_group_id = None  # set by the engine
        self.num_ruptures = 0  # set by the engine
        self.seed = None  # set by the engine
        self.id = None  # set by the engine

    @abc.abstractmethod
    def iter_ruptures(self):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of sublclass of :class:
            `~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`.
        """

    @abc.abstractmethod
    def count_ruptures(self):
        """
        Return the number of ruptures that will be generated by the source.
        """

    @abc.abstractmethod
    def get_min_max_mag(self):
        """
        Return minimum and maximum magnitudes of the ruptures generated
        by the source.
        """

    @abc.abstractmethod
    def get_rupture_enclosing_polygon(self, dilation=0):
        """
        Get a polygon which encloses all the ruptures generated by the source.

        The rupture enclosing polygon is meant to be used in all hazard
        calculators to filter out sources whose ruptures the user wants
        to be neglected because they are too far from the locations
        of interest.

        For performance reasons, the ``get_rupture_enclosing_polygon()``
        should compute the polygon, without creating all the ruptures.
        The rupture enclosing polygon may not be necessarily the *minimum*
        enclosing polygon, but must guarantee that all ruptures are within
        the polygon.

        This method must be implemented by subclasses.

        :param dilation:
            A buffer distance in km to extend the polygon borders to.
        :returns:
            Instance of :class:`openquake.hazardlib.geo.polygon.Polygon`.
        """

    def filter_sites_by_distance_to_source(self, integration_distance, sites):
        """
        Filter out sites from the collection that are further from the source
        than some arbitrary threshold.

        :param integration_distance:
            Distance in km representing a threshold: sites that are further
            than that distance from the closest rupture produced by the source
            should be excluded.
        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`
            to filter.
        :returns:
            Filtered :class:`~openquake.hazardlib.site.SiteCollection`.

        Method can be overridden by subclasses in order to achieve
        higher performance for a specific typology. Base class method calls
        :meth:`get_rupture_enclosing_polygon` with ``integration_distance``
        as a dilation value and then filters site collection by checking
        :meth:
        `containment <openquake.hazardlib.geo.polygon.Polygon.intersects>`
        of site locations.

        The main criteria for this method to decide whether a site should be
        filtered out or not is the minimum distance between the site and all
        the ruptures produced by the source. If at least one rupture is closer
        (in terms of great circle distance between surface projections) than
        integration distance to a site, it should not be filtered out. However,
        it is important not to make this method too computationally intensive.
        If short-circuits are taken, false positives are generally better than
        false negatives (it's better not to filter a site out if there is some
        uncertainty about its distance).
        """
        rup_enc_poly = self.get_rupture_enclosing_polygon(integration_distance)
        return sites.filter(rup_enc_poly.intersects(sites.mesh))

    def modify(self, modification, parameters):
        """
        Apply a single modificaton to the source parameters
        Reflects the modification method and calls it passing ``parameters``
        as keyword arguments.

        Modifications can be applied one on top of another. The logic
        of stacking modifications is up to a specific source implementation.

        :param modification:
            String name representing the type of modification.
        :param parameters:
            Dictionary of parameters needed for modification.
        :raises ValueError:
            If ``modification`` is missing from the attribute `MODIFICATIONS`.
        """
        if modification not in self.MODIFICATIONS:
            raise ValueError('Modification %s is not supported by %s' %
                             (modification, type(self).__name__))
        meth = getattr(self, 'modify_%s' % modification)
        meth(**parameters)


@with_slots
class ParametricSeismicSource(with_metaclass(abc.ABCMeta, BaseSeismicSource)):
    """
    Parametric Seismic Source generates earthquake ruptures from source
    parameters, and associated probabilities of occurrence are defined through
    a magnitude frequency distribution and a temporal occurrence model.

    :param mfd:
        Magnitude-Frequency distribution for the source.
        See :mod:`openquake.hazardlib.mfd`.
    :param rupture_mesh_spacing:
        The desired distance between two adjacent points in source's
        ruptures' mesh, in km. Mainly this parameter allows to balance
        the trade-off between time needed to compute the :meth:`distance
        <openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_min_distance>`
        between the rupture surface and a site and the precision of that
        computation.
    :param magnitude_scaling_relationship:
        Instance of subclass of
        :class:`openquake.hazardlib.scalerel.base.BaseMSR` to
        describe how does the area of the rupture depend on magnitude and rake.
    :param rupture_aspect_ratio:
        Float number representing how much source's ruptures are more wide
        than tall. Aspect ratio of 1 means ruptures have square shape,
        value below 1 means ruptures stretch vertically more than horizontally
        and vice versa.
    :param temporal_occurrence_model:
        Instance of
        :class:`openquake.hazardlib.tom.PoissonTOM` defining temporal
        occurrence model for calculating rupture occurrence probabilities

    :raises ValueError:
        If either rupture aspect ratio or rupture mesh spacing is not positive
        (if not None).
    """

    _slots_ = BaseSeismicSource._slots_ + '''mfd rupture_mesh_spacing
    magnitude_scaling_relationship rupture_aspect_ratio
    temporal_occurrence_model'''.split()

    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model):
        super(ParametricSeismicSource, self). \
            __init__(source_id, name, tectonic_region_type)

        if rupture_mesh_spacing is not None and not rupture_mesh_spacing > 0:
            raise ValueError('rupture mesh spacing must be positive')

        if rupture_aspect_ratio is not None and not rupture_aspect_ratio > 0:
            raise ValueError('rupture aspect ratio must be positive')

        self.mfd = mfd
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.magnitude_scaling_relationship = magnitude_scaling_relationship
        self.rupture_aspect_ratio = rupture_aspect_ratio
        self.temporal_occurrence_model = temporal_occurrence_model

    def get_annual_occurrence_rates(self, min_rate=0):
        """
        Get a list of pairs "magnitude -- annual occurrence rate".

        The list is taken from assigned MFD object
        (see :meth:`openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`)
        with simple filtering by rate applied.

        :param min_rate:
            A non-negative value to filter magnitudes by minimum annual
            occurrence rate. Only magnitudes with rates greater than that
            are included in the result list.
        :returns:
            A list of two-item tuples -- magnitudes and occurrence rates.
        """
        return [(mag, occ_rate)
                for (mag, occ_rate) in self.mfd.get_annual_occurrence_rates()
                if min_rate is None or occ_rate > min_rate]

    def get_min_max_mag(self):
        """
        Get the minimum and maximum magnitudes of the ruptures generated
        by the source from the underlying MFD.
        """
        return self.mfd.get_min_max_mag()

    def __repr__(self):
        """
        String representation of a source, displaying the source class name
        and the source id.
        """
        return '<%s %s>' % (self.__class__.__name__, self.source_id)
