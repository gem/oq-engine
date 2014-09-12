# -*- coding: utf-8 -*-

# Copyright (c) 2012-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Hazard getters for Risk calculators.

A HazardGetter is responsible fo getting hazard outputs needed by a risk
calculation.
"""
import itertools
import operator

import numpy

from openquake.hazardlib.imt import from_string
from openquake.risklib import scientific

from openquake.engine import logs
from openquake.engine.db import models

BYTES_PER_FLOAT = numpy.zeros(1, dtype=float).nbytes

NRUPTURES = 1  # constant for readability


class AssetSiteAssociationError(Exception):
    pass


def make_epsilons(asset_count, num_samples, seed, correlation):
    """
    :param int asset_count: the number of assets
    :param int num_ruptures: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    """
    zeros = numpy.zeros((asset_count, num_samples))
    return scientific.make_epsilons(zeros, seed, correlation)


class HazardGetter(object):
    """
    A Hazard Getter is used to query for the closest hazard data for
    each given asset. A Hazard Getter must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).
    A Hazard Getter should be instantiated by a GetterBuilder and
    not directly.

    :attr hazard_output:
        A :class:`openquake.engine.db.models.Output` instance

    :attr assets:
        The assets for which we want to extract the hazard

   :attr site_ids:
        The ids of the sites associated to the hazards
    """
    builder = None  # set by the GetterBuilder
    epsilons = None  # overridden in the GroundMotionValuesGetter

    def __init__(self, hazard_output, assets, site_ids):
        self.hazard_output = hazard_output
        self.assets = assets
        self.site_ids = site_ids

    def __repr__(self):
        shape = getattr(self.epsilons, 'shape', None)
        eps = ', %s epsilons' % str(shape) if shape else ''
        return "<%s %d assets%s, taxonomy=%s>" % (
            self.__class__.__name__, len(self.assets), eps,
            self.builder.taxonomy)

    def get_data(self):
        """
        Subclasses must implement this.
        """
        raise NotImplementedError

    @property
    def hid(self):
        """Return the id of the given hazard output"""
        return self.hazard_output.id

    @property
    def weight(self):
        """Return the weight of the realization of the hazard output"""
        h = self.hazard_output.output_container
        if hasattr(h, 'lt_realization') and h.lt_realization:
            return h.lt_realization.weight


class HazardCurveGetter(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.
    """ + HazardGetter.__doc__

    def get_data(self, imt):
        """
        Extracts the hazard curves for the given `imt` from the hazard output.

        :param str imt: Intensity Measure Type
        :returns: a list of N curves, each one being a list of pairs (iml, poe)
        """
        imt_type, sa_period, sa_damping = from_string(imt)

        oc = self.hazard_output.output_container
        if oc.output.output_type == 'hazard_curve':
            imls = oc.imls
        elif oc.output.output_type == 'hazard_curve_multi':
            oc = models.HazardCurve.objects.get(
                output__oq_job=oc.output.oq_job,
                output__output_type='hazard_curve',
                statistics=oc.statistics,
                lt_realization=oc.lt_realization,
                imt=imt_type,
                sa_period=sa_period,
                sa_damping=sa_damping)
            imls = oc.imls

        cursor = models.getcursor('job_init')
        query = """\
        SELECT hzrdr.hazard_curve_data.poes
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s AND location = %s
        """
        all_curves = []
        for site_id in self.site_ids:
            location = models.HazardSite.objects.get(pk=site_id).location
            cursor.execute(query, (oc.id, 'SRID=4326; ' + location.wkt))
            poes = cursor.fetchall()[0][0]
            all_curves.append(zip(imls, poes))
        return all_curves


def expand(array, N):
    """
    Given a non-empty array with n elements, expands it to a larger
    array with N elements.

    >>> expand([1], 3)
    array([1, 1, 1])
    >>> expand([1, 2, 3], 10)
    array([1, 2, 3, 1, 2, 3, 1, 2, 3, 1])
    >>> expand(numpy.zeros((2, 10)), 5).shape
    (5, 10)
    """
    n = len(array)
    assert n > 0, 'Empty array'
    if n >= N:
        raise ValueError('Cannot expand an array of %d elements to %d',
                         n, N)
    return numpy.array([array[i % n] for i in xrange(N)])


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values.
    """ + HazardGetter.__doc__
    sescoll = None  # set by the GetterBuilder
    asset_site_ids = None  # set by the GetterBuilder

    @property
    def rupture_ids(self):
        """
        Rupture_ids for the current getter
        """
        return self.builder.rupture_ids[self.sescoll.id]

    @property
    def epsilons(self):
        """
        Epsilon matrix for the current getter
        """
        epsilon_rows = []  # ordered by asset_site_id
        for eps in models.Epsilon.objects.filter(
                ses_collection=self.sescoll.id,
                asset_site__in=self.asset_site_ids):
            epsilon_rows.append(eps.epsilons)
        assert epsilon_rows, ('No epsilons for ses_collection_id=%s' %
                              self.sescoll.id)
        return numpy.array(epsilon_rows)

    def get_epsilons(self):
        """
        Expand the inner epsilons to the right number, if needed
        """
        eps = self.epsilons
        _n, m = eps.shape
        e = len(self.rupture_ids)
        if e > m:  # there are more ruptures than epsilons
            # notice the double transpose below; a shape (1, 3) will go into
            # (1, 3); without, it would go incorrectly into (3, 3)
            return expand(eps.T, e).T
        return eps

    def _get_gmv_dict(self, imt_type, sa_period, sa_damping):
        """
        :returns: a dictionary {rupture_id: gmv} for the given site and IMT
        """
        gmf_id = self.hazard_output.output_container.id
        if sa_period:
            imt_query = 'imt=%s and sa_period=%s and sa_damping=%s'
        else:
            imt_query = 'imt=%s and sa_period is %s and sa_damping is %s'
        gmv_dict = {}
        cursor = models.getcursor('job_init')
        cursor.execute('select site_id, rupture_ids, gmvs from '
                       'hzrdr.gmf_data where gmf_id=%s and site_id in %s '
                       'and {} order by site_id'.format(imt_query),
                       (gmf_id, tuple(set(self.site_ids)),
                        imt_type, sa_period, sa_damping))
        for sid, group in itertools.groupby(cursor, operator.itemgetter(0)):
            gmvs = []
            ruptures = []
            for site_id, rupture_ids, gmvs_chunk in group:
                gmvs.extend(gmvs_chunk)
                ruptures.extend(rupture_ids)
            gmv_dict[sid] = dict(itertools.izip(ruptures, gmvs))
        return gmv_dict

    def get_data(self, imt):
        """
        Extracts the GMFs for the given `imt` from the hazard output.

        :param str imt: Intensity Measure Type
        :returns: a list of N arrays with R elements each.
        """
        imt_type, sa_period, sa_damping = from_string(imt)
        gmv_dict = self._get_gmv_dict(imt_type, sa_period, sa_damping)
        all_gmvs = []
        for site_id in self.site_ids:
            gmv = gmv_dict.get(site_id, {})
            if not gmv:
                logs.LOG.info('No data for site_id=%d, imt=%s', site_id, imt)
            array = numpy.array([gmv.get(r, 0.) for r in self.rupture_ids])
            all_gmvs.append(array)
        return all_gmvs


class GetterBuilder(object):
    """
    A facility to build hazard getters. When instantiated, populates
    the lists .asset_ids and .site_ids with the associations between
    the assets in the current exposure model and the sites in the
    previous hazard calculation. It also populate the `asset_site`
    table in the database.

    :param str taxonomy: the taxonomy we are interested in
    :param rc: a :class:`openquake.engine.db.models.RiskCalculation` instance

    Warning: instantiating a GetterBuilder performs a potentially
    expensive geospatial query.
    """
    def __init__(self, taxonomy, rc, epsilon_sampling=0):
        self.taxonomy = taxonomy
        self.rc = rc
        self.epsilon_sampling = epsilon_sampling
        self.hc = rc.get_hazard_calculation()
        max_dist = rc.best_maximum_distance * 1000  # km to meters
        cursor = models.getcursor('job_init')

        # insert the associations for the current taxonomy
        self.assoc_query = cursor.mogrify("""\
WITH assocs AS (
  SELECT DISTINCT ON (exp.id) %s, exp.id, hsite.id
  FROM riski.exposure_data AS exp
  JOIN hzrdi.hazard_site AS hsite
  ON ST_DWithin(exp.site, hsite.location, %s)
  WHERE hsite.hazard_calculation_id = %s
  AND exposure_model_id = %s AND taxonomy=%s
  AND ST_COVERS(ST_GeographyFromText(%s), exp.site)
  ORDER BY exp.id, ST_Distance(exp.site, hsite.location, false)
)
INSERT INTO riskr.asset_site (job_id, asset_id, site_id)
SELECT * FROM assocs""", (rc.oqjob.id, max_dist, self.hc.id,
                          rc.exposure_model.id, taxonomy,
                          rc.region_constraint.wkt))
        cursor.execute(self.assoc_query)

        # now read the associations just inserted
        self.asset_sites = models.AssetSite.objects.filter(
            job=rc.oqjob, asset__taxonomy=taxonomy)
        if not self.asset_sites:
            raise AssetSiteAssociationError(
                'Could not associated any asset of taxonomy %s to '
                'hazard sites within the distance of %s km'
                % (taxonomy, self.rc.best_maximum_distance))

        self.asset_ids = [a.asset_id for a in self.asset_sites]
        self.site_ids = [a.site_id for a in self.asset_sites]
        self.rupture_ids = {}
        self.epsilons_shape = {}

    def calc_nbytes(self, hazard_outputs):
        """
        :param hazard_outputs: the outputs of a hazard calculation
        :returns: the number of bytes to be allocated (can be
                  much less if there is no correlation and the 'fast'
                  epsilons management is enabled).

        If the hazard_outputs come from an event based or scenario computation,
        populate the .epsilons_shape dictionary.
        """
        num_assets = len(self.asset_ids)
        if self.hc.calculation_mode == 'event_based':
            lt_model_ids = set(ho.output_container.lt_realization.lt_model.id
                               for ho in hazard_outputs)
            for lt_model_id in lt_model_ids:
                ses_coll = models.SESCollection.objects.get(
                    lt_model=lt_model_id)
                num_ruptures = ses_coll.get_ruptures().count()
                samples = min(self.epsilon_sampling, num_ruptures) \
                    if self.epsilon_sampling else num_ruptures
                self.epsilons_shape[ses_coll.id] = (num_assets, samples)
        elif self.hc.calculation_mode == 'scenario':
            [out] = self.hc.oqjob.output_set.filter(output_type='ses')
            samples = self.hc.number_of_ground_motion_fields
            self.epsilons_shape[out.ses.id] = (num_assets, samples)
        nbytes = 0
        for (n, r) in self.epsilons_shape.values():
            # the max(n, r) is taken because if n > r then the limiting
            # factor is the size of the correlation matrix, i.e. n
            nbytes += max(n, r) * n * BYTES_PER_FLOAT
        return nbytes

    def init_epsilons(self, hazard_outputs):
        """
        :param hazard_outputs: the outputs of a hazard calculation

        If the hazard_outputs come from an event based or scenario computation,
        populate the .epsilons and the .rupture_ids dictionaries.
        """
        if not self.epsilons_shape:
            self.calc_nbytes(hazard_outputs)
        if self.hc.calculation_mode == 'event_based':
            lt_model_ids = set(ho.output_container.lt_realization.lt_model.id
                               for ho in hazard_outputs)
            ses_collections = [
                models.SESCollection.objects.get(lt_model=lt_model_id)
                for lt_model_id in lt_model_ids]
        elif self.hc.calculation_mode == 'scenario':
            [out] = self.hc.oqjob.output_set.filter(output_type='ses')
            ses_collections = [out.ses]
        else:
            ses_collections = []
        for ses_coll in ses_collections:
            scid = ses_coll.id  # ses collection id
            num_assets, num_samples = self.epsilons_shape[scid]
            self.rupture_ids[scid] = ses_coll.get_ruptures(
                ).values_list('id', flat=True) or range(
                self.hc.number_of_ground_motion_fields)
            logs.LOG.info('Building (%d, %d) epsilons for taxonomy %s',
                          num_assets, num_samples, self.taxonomy)
            eps = make_epsilons(
                num_assets, num_samples,
                self.rc.master_seed, self.rc.asset_correlation)
            models.Epsilon.saveall(ses_coll, self.asset_sites, eps)

    def make_getters(self, gettercls, hazard_outputs, annotated_assets):
        """
        Build the appropriate hazard getters from the given hazard
        outputs. The assets which have no corresponding hazard site
        within the maximum distance are discarded. An AssetSiteAssociationError
        is raised if all assets are discarded. From outputs coming from
        an event based or a scenario calculation the right epsilons
        corresponding to the assets are stored in the database

        :param gettercls:
            the HazardGetter subclass to use
        :param hazard_outputs:
            the outputs of a hazard calculation
        :param annotated_assets:
            a block of assets with additional attributes

        :returns: a list of HazardGetter instances
        """
        # NB: the annotations to the assets are added by models.AssetManager
        asset_sites = models.AssetSite.objects.filter(
            job=self.rc.oqjob, asset__in=annotated_assets)
        if not asset_sites:
            raise AssetSiteAssociationError(
                'Could not associated any asset in %s to '
                'hazard sites within the distance of %s km'
                % (annotated_assets, self.rc.best_maximum_distance))
        if not self.epsilons_shape:
            self.init_epsilons(hazard_outputs)

        # skip the annotated assets without hazard
        asset_site_dict = {a.asset.id: a.site.id for a in asset_sites}
        annotated = []
        site_ids = []
        skipped = []
        for asset in annotated_assets:
            try:
                site_id = asset_site_dict[asset.id]
            except KeyError:
                # skipping assets without hazard
                skipped.append(asset.asset_ref)
                continue
            annotated.append(asset)
            site_ids.append(site_id)
        if skipped:
            logs.LOG.warn('Could not associate %d assets to hazard sites '
                          'within the distance of %s km', len(skipped),
                          self.rc.best_maximum_distance)

        # build the getters
        getters = []
        for ho in hazard_outputs:
            getter = gettercls(ho, annotated, site_ids)
            getter.builder = self
            if self.hc.calculation_mode == 'event_based':
                getter.sescoll = models.SESCollection.objects.get(
                    lt_model=ho.output_container.lt_realization.lt_model)
                getter.asset_site_ids = [a.id for a in asset_sites]
            elif self.hc.calculation_mode == 'scenario':
                [out] = ho.oq_job.output_set.filter(output_type='ses')
                getter.sescoll = out.ses
                getter.asset_site_ids = [a.id for a in asset_sites]
            getters.append(getter)
        return getters
