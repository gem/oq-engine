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
Hazard input management for Risk calculators.
"""
import itertools
import operator

import numpy

from openquake.hazardlib.imt import from_string
from openquake.risklib import scientific

from openquake.engine import logs
from openquake.engine.db import models
from django.db import transaction


BYTES_PER_FLOAT = numpy.zeros(1, dtype=float).nbytes

NRUPTURES = 1  # constant for readability


class AssetSiteAssociationError(Exception):
    pass


class Hazard(object):
    """
    Hazard objects have attributes .hazard_output, .data and .imt.
    Moreover you can extract the .hid (hazard_output.id) and the
    .weight associated to the underlying realization.
    The hazard .data is a numpy array of shape (N, R) where N is the
    number of assets and R the number of seismic events (ruptures)
    or the resolution of the hazard curve, depending on the calculator.
    """
    def __init__(self, hazard_output, data, imt):
        self.hazard_output = hazard_output
        self.data = data
        self.imt = imt

    @property
    def hid(self):
        """Return the id of the given hazard output"""
        return self.hazard_output.id

    @property
    def weight(self):
        """Return the realization weight of the hazard output"""
        h = self.hazard_output.output_container
        if hasattr(h, 'lt_realization') and h.lt_realization:
            return h.lt_realization.weight


def make_epsilons(asset_count, num_samples, seed, correlation):
    """
    :param int asset_count: the number of assets
    :param int num_ruptures: the number of ruptures
    :param int seed: a random seed
    :param float correlation: the correlation coefficient
    """
    zeros = numpy.zeros((asset_count, num_samples))
    return scientific.make_epsilons(zeros, seed, correlation)


class RiskInput(object):
    """
    A RiskInput objects stores a chunk of assets and their associated
    hazard data. In case of scenario and event based calculators it
    also stores the ruptures and the epsilons.
    The RiskInput must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).

    :attr bridge:
        A :class:`HazardRiskBridge` instance

    :attr assets:
        The assets for which we want to extract the hazard

   :attr site_ids:
        The ids of the sites associated to the hazards
    """
    def __init__(self, bridge, assets):
        self.bridge = bridge
        self.assets = assets
        self.site_ids = []
        self.asset_site_ids = []

    def init(self):
        """
        Call this right after installation to read hazards and epsilons
        from the database, as well as asset_site associations.
        """
        # asset_site associations
        for asset in self.assets:
            asset_site_id = asset.asset_site_id
            assoc = models.AssetSite.objects.get(pk=asset_site_id)
            self.site_ids.append(assoc.site.id)
            self.asset_site_ids.append(asset_site_id)

    def get_hazards(self, imt):
        """
        Return a list of Hazard instances for the given IMT.
        """
        return [Hazard(ho, self._get_data(ho, imt), imt)
                for ho in self.bridge.hazard_outputs]

    def get_data(self, imt):
        """
        Shortcut returning the hazard data when there is a single realization
        """
        [hazard] = self.get_hazards(imt)
        return hazard.data

    @property
    def hid(self):
        """
        Return the id of the hazard output, when there is a single realization
        """
        [ho] = self.bridge.hazard_outputs
        return ho.id

    @property
    def taxonomy(self):
        """The underlying taxonomy of the assets"""
        return self.bridge.taxonomy

    def __repr__(self):
        shape = getattr(self.epsilons, 'shape', None)
        eps = ', %s epsilons' % str(shape) if shape else ''
        return "<%s %d assets%s, taxonomy=%s>" % (
            self.__class__.__name__, len(self.assets), eps,
            self.bridge.taxonomy)


class HazardCurveInput(RiskInput):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.
    """ + RiskInput.__doc__

    def _get_data(self, ho, imt):
        """
        Extracts the hazard curves for the given `imt` from the hazard output.

        :param str imt: Intensity Measure Type
        :returns: a list of N curves, each one being a list of pairs (iml, poe)
        """
        imt_type, sa_period, sa_damping = from_string(imt)
        oc = ho.output_container
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


class GroundMotionInput(RiskInput):
    """
    Hazard getter for loading ground motion values.
    """ + RiskInput.__doc__

    def init(self):
        """
        Perform the needed queries on the database to populate
        hazards and epsilons.
        """
        RiskInput.init(self)  # assoc asset -> site

        self.hazards = {}  # dict ho, imt -> {site_id: {rup_id: gmv}}
        for ho in self.bridge.hazard_outputs:
            for imt in self.bridge.imts:
                self.hazards[ho, imt] = self._get_gmv_dict(ho, imt)

        epsilon_rows = []  # ordered by asset_site_id
        for eps in models.Epsilon.objects.filter(
                ses_collection__in=self.bridge.ses_coll_ids,
                asset_site__in=self.asset_site_ids):
            epsilon_rows.append(eps.epsilons)
        if epsilon_rows:
            self.epsilons = numpy.array(epsilon_rows)

    @property
    def rupture_ids(self):
        """The rupture_ids of the underlying bridge"""
        return self.bridge.rupture_ids

    def get_epsilons(self):
        """
        Expand the underlying epsilons
        """
        eps = self.epsilons
        # expand the inner epsilons to the right number, if needed
        _n, m = eps.shape
        e = len(self.rupture_ids)
        if e > m:  # there are more ruptures than epsilons
            # notice the double transpose below; a shape (1, 3) will go into
            # (1, 3); without, it would go incorrectly into (3, 3)
            return expand(eps.T, e).T
        return eps

    def _get_gmv_dict(self, ho, imt):
        """
        :returns: a dictionary {rupture_id: gmv} for the given site and IMT
        """
        imt_type, sa_period, sa_damping = from_string(imt)
        gmf_id = ho.output_container.id
        if sa_period:
            imt_query = 'imt=%s and sa_period=%s and sa_damping=%s'
        else:
            imt_query = 'imt=%s and sa_period is %s and sa_damping is %s'
        gmv_dict = {}  # dict site_id -> {rup_id: gmv}
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

    def _get_data(self, ho, imt):
        """
        Extracts the GMFs for the given `imt` from the hazard output.

        :param str imt: Intensity Measure Type
        :returns: a list of N arrays with R elements each.
        """
        all_gmvs = []
        no_data = 0
        gmv_dict = self.hazards[ho, imt]
        for site_id in self.site_ids:
            gmv = gmv_dict.get(site_id, {})
            if not gmv:
                no_data += 1
            array = numpy.array([gmv.get(r, 0.) for r in self.rupture_ids])
            all_gmvs.append(array)
        if no_data:
            logs.LOG.info('No data for %d assets out of %d, IMT=%s',
                          no_data, len(self.site_ids), imt)
        return all_gmvs


class HazardRiskBridge(object):
    """
    A facility providing the brigde between the hazard (sites and outputs)
    and the risk (assets and risk models). When instantiated, populates
    the `asset_site` table with the associations between the assets in
    the current exposure model and the sites in the previous hazard
    calculation.

    :param hazard_outputs:
        outputs of the previous hazard calculation
    :param taxonomy:
        the taxonomy of the assets we are interested in
    :param rc:
        a :class:`openquake.engine.db.models.RiskCalculation` instance

    Warning: instantiating a HazardRiskBridge may perform a potentially
    expensive geospatial query.
    """
    def __init__(self, hazard_outputs, taxonomy, rc):
        self.hazard_outputs = hazard_outputs
        self.taxonomy = taxonomy
        self.rc = rc
        self.hc = rc.hazard_calculation
        self.calculation_mode = self.rc.oqjob.get_param('calculation_mode')
        self.number_of_ground_motion_fields = self.hc.get_param(
            'number_of_ground_motion_fields', 0)
        max_dist = rc.best_maximum_distance * 1000  # km to meters
        cursor = models.getcursor('job_init')
        self.imts = sorted(
            i.imt.imt_str for i in models.ImtTaxonomy.objects.filter(
                job=rc.oqjob, taxonomy=taxonomy))
        hazard_exposure = models.extract_from([self.hc], 'exposuremodel')
        if self.rc.exposure_model is hazard_exposure:
            # no need of geospatial queries, just join on the location
            self.assoc_query = cursor.mogrify("""\
WITH assocs AS (
  SELECT %s, exp.id, hsite.id
  FROM riski.exposure_data AS exp
  JOIN hzrdi.hazard_site AS hsite
  ON exp.site::text = hsite.location::text
  WHERE hsite.hazard_calculation_id = %s
  AND exposure_model_id = %s AND taxonomy=%s
  AND ST_COVERS(ST_GeographyFromText(%s), exp.site)
)
INSERT INTO riskr.asset_site (job_id, asset_id, site_id)
SELECT * FROM assocs""", (rc.oqjob.id, self.hc.id,
                          rc.exposure_model.id, taxonomy,
                          rc.region_constraint.wkt))
        else:
            # associate each asset to the closest hazard site
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

        # insert the associations for the current taxonomy
        with transaction.commit_on_success(using='job_init'):
            cursor.execute(self.assoc_query)

        # now read the associations just inserted
        self.asset_sites = models.AssetSite.objects.filter(
            job=rc.oqjob, asset__taxonomy=taxonomy)
        if not self.asset_sites:
            raise AssetSiteAssociationError(
                'Could not associated any asset of taxonomy %s to '
                'hazard sites within the distance of %s km'
                % (taxonomy, self.rc.best_maximum_distance))
        self.rupture_ids = []
        self._rupture_ids = {}
        self.epsilons_shape = {}

    def calc_nbytes(self, epsilon_sampling=None):
        """
        :param epsilon_sampling:
             flag saying if the epsilon_sampling feature is enabled
        :returns:
            the number of bytes to be allocated (a guess)

        If the hazard_outputs come from an event based or scenario computation,
        populate the .epsilons_shape dictionary.
        """
        num_assets = len(self.asset_sites)
        if self.calculation_mode.startswith('event_based'):
            lt_model_ids = set(ho.output_container.lt_realization.lt_model.id
                               for ho in self.hazard_outputs)
            for lt_model_id in lt_model_ids:
                ses_coll = models.SESCollection.objects.get(
                    lt_model=lt_model_id)
                num_ruptures = ses_coll.get_ruptures().count()
                samples = min(epsilon_sampling, num_ruptures) \
                    if epsilon_sampling else num_ruptures
                self.epsilons_shape[ses_coll.id] = (num_assets, samples)
        elif self.calculation_mode.startswith('scenario'):
            [out] = self.hc.output_set.filter(output_type='ses')
            samples = self.number_of_ground_motion_fields
            self.epsilons_shape[out.ses.id] = (num_assets, samples)
        nbytes = 0
        for (n, r) in self.epsilons_shape.values():
            # the max(n, r) is taken because if n > r then the limiting
            # factor is the size of the correlation matrix, i.e. n
            nbytes += max(n, r) * n * BYTES_PER_FLOAT
        return nbytes

    def init_epsilons(self, epsilon_sampling=None):
        """
        :param epsilon_sampling:
             flag saying if the epsilon_sampling feature is enabled

        Populate the .epsilons_shape and the ._rupture_ids dictionaries.
        For the calculators `event_based_risk` and `scenario_risk` also
        stores the epsilons in the database for each asset_site association.
        """
        if not self.epsilons_shape:
            self.calc_nbytes(epsilon_sampling)
        if self.calculation_mode.startswith('event_based'):
            lt_model_ids = set(ho.output_container.lt_realization.lt_model.id
                               for ho in self.hazard_outputs)
            ses_collections = [
                models.SESCollection.objects.get(lt_model=lt_model_id)
                for lt_model_id in lt_model_ids]
        elif self.calculation_mode.startswith('scenario'):
            [out] = self.hc.output_set.filter(output_type='ses')
            ses_collections = [out.ses]
        else:
            ses_collections = []
        for ses_coll in ses_collections:
            scid = ses_coll.id  # ses collection id
            num_assets, num_samples = self.epsilons_shape[scid]
            self._rupture_ids[scid] = ses_coll.get_ruptures(
                ).values_list('id', flat=True) or range(
                self.number_of_ground_motion_fields)
            self.rupture_ids.extend(self._rupture_ids[scid])
            # do not build the epsilons for scenario_damage
            if self.calculation_mode != 'scenario_damage':
                logs.LOG.info('Building (%d, %d) epsilons for taxonomy %s',
                              num_assets, num_samples, self.taxonomy)
                eps = make_epsilons(
                    num_assets, num_samples,
                    self.rc.master_seed, self.rc.asset_correlation)
                models.Epsilon.saveall(ses_coll, self.asset_sites, eps)

    @property
    def ses_coll_ids(self):
        """
        SESCollection IDs in a fixed order (sorted by ID)
        """
        return sorted(self._rupture_ids)
