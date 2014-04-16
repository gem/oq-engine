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

import collections
import numpy

from openquake.hazardlib import geo
from openquake.hazardlib.imt import from_string

from openquake.engine import logs
from openquake.engine.db import models
from openquake.engine.performance import DummyMonitor


# all hazard getters are to be considered private, they should be called by
# the GetterBuilder only
class HazardGetter(object):
    """
    Base abstract class of an Hazard Getter.

    An Hazard Getter is used to query for the closest hazard data for
    each given asset. An Hazard Getter must be pickable such that it
    should be possible to use different strategies (e.g. distributed
    or not, using postgis or not).

    :attr hazard_output:
        A :class:`openquake.engine.db.models.Output` instance

    :attr assets:
        The assets for which we wants to compute.

    :attr imt:
        The imt (in long form) for which data have to be retrieved
    """
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

    def __init__(self, hazard_output, site_assets, imt):
        self.hazard_output = hazard_output
        self.site_assets = site_assets
        self.imt = imt
        self.imt_type, self.sa_period, self.sa_damping = from_string(imt)
        self.epsilons = None

    def __repr__(self):
        return "<%s assets=%s>" % (
            self.__class__.__name__, [a.id for a in self.assets])

    def get_data(self, monitor):
        """
        Subclasses must implement this.
        """
        raise NotImplementedError

    def __call__(self, monitor=None):
        """
        :param monitor: a performance monitor or None
        :returns:
            A tuple with two elements. The first is an array of instances of
            :class:`openquake.engine.db.models.ExposureData`, the second is
            the corresponding hazard data.
        """
        return self.get_data(monitor or DummyMonitor())


class HazardCurveGetterPerAsset(HazardGetter):
    """
    Simple HazardCurve Getter that performs a spatial query for each
    asset.

    :attr imls:
        The intensity measure levels of the curves we are going to get.
    """
    def get_data(self, monitor):
        """
        Calls ``get_by_site`` for each asset and pack the results as
        requested by the :meth:`HazardGetter.get_data` interface.
        """
        oc = self.hazard_output.output_container
        if oc.output.output_type == 'hazard_curve':
            imls = oc.imls
        elif oc.output.output_type == 'hazard_curve_multi':
            oc = models.HazardCurve.objects.get(
                output__oq_job=oc.output.oq_job,
                output__output_type='hazard_curve',
                statistics=oc.statistics,
                lt_realization=oc.lt_realization,
                imt=self.imt_type,
                sa_period=self.sa_period,
                sa_damping=self.sa_damping)
            imls = oc.imls

        all_assets, all_curves = [], []
        with monitor.copy('getting closest hazard curves'):
            for site_id, assets in self.site_assets:
                site = models.HazardSite.objects.get(pk=site_id)
                [poes] = self.get_by_site(site, oc.id)
                curve = zip(imls, poes)
                for asset in assets:
                    all_assets.append(asset)
                    all_curves.append(curve)
        return all_assets, all_curves

    def get_by_site(self, site, hazard_id):
        """
        :param site:
            An instance of :class:`django.contrib.gis.geos.point.Point`
            corresponding to the location of an asset.
        """
        cursor = models.getcursor('job_init')

        query = """\
        SELECT hzrdr.hazard_curve_data.poes
        FROM hzrdr.hazard_curve_data
        WHERE hazard_curve_id = %s AND location = %s
        """
        cursor.execute(query, (hazard_id, 'SRID=4326; ' + site.location.wkt))
        return cursor.fetchone()


class ScenarioGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It is instantiated
    with a set of assets all of the same taxonomy.
    """
    def get_gmvs(self, site_id):
        """
        :returns: gmvs and ruptures for the given site and IMT
        """
        gmvs = []
        for gmf in models.GmfData.objects.filter(
                gmf=self.hazard_output.output_container,
                site=site_id, imt=self.imt_type, sa_period=self.sa_period,
                sa_damping=self.sa_damping):
            gmvs.extend(gmf.gmvs)
            if not gmvs:
                logs.LOG.warn('No gmvs for site %s, IMT=%s', site_id, self.imt)
        return gmvs

    def get_data(self, monitor):
        """
        :returns: the assets and the corresponding ground motion values
        """
        all_assets = []
        all_gmvs = []
        with monitor.copy('getting gmvs and ruptures'):
            for site_id, assets in self.site_assets:
                n_assets = len(assets)
                all_assets.extend(assets)
                gmvs = self.get_gmvs(site_id)
                if gmvs:
                    array = numpy.array(gmvs)
                    all_gmvs.extend([array] * n_assets)
        return all_assets, all_gmvs

    @classmethod
    def make_epsilons(cls, lt_model, num_assets, seed, correlation):
        self.hazard_output.output_container
        num_ruptures = ses_coll.get_ruptures().count()
        zeros = numpy.zeros((num_assets, num_ruptures))
        return scientific.make_epsilons(zeros, seed, correlation)


class GroundMotionValuesGetter(HazardGetter):
    """
    Hazard getter for loading ground motion values. It is instantiated
    with a set of assets all of the same taxonomy.
    """
    def get_gmvs_ruptures(self, site_id):
        """
        :returns: gmvs and ruptures for the given site and IMT
        """
        gmvs = []
        ruptures = []
        for gmf in models.GmfData.objects.filter(
                gmf=self.hazard_output.output_container,
                site=site_id, imt=self.imt_type, sa_period=self.sa_period,
                sa_damping=self.sa_damping):
            gmvs.extend(gmf.gmvs)
            ruptures.extend(gmf.rupture_ids)
        if not gmvs:
            logs.LOG.warn('No gmvs for site %s, IMT=%s', site_id, self.imt)
        return gmvs, ruptures

    def get_data(self, monitor):
        """
        :returns:
            the assets and the hazard data as a pair (GMVs, rupture_ids).
        """
        all_ruptures = set()
        all_assets = []
        all_gmvs = []
        site_gmv = collections.OrderedDict()
        # dictionary site -> ({rupture_id: gmv}, n_assets)
        # the ordering is there only to have repeatable runs
        with monitor.copy('getting gmvs and ruptures'):
            for site_id, assets in self.site_assets:
                n_assets = len(assets)
                all_assets.extend(assets)
                gmvs, ruptures = self.get_gmvs_ruptures(site_id)
                site_gmv[site_id] = dict(zip(ruptures, gmvs)), n_assets
                for r in ruptures:
                    all_ruptures.add(r)

        # second pass, filling with zeros
        with monitor.copy('filling gmvs with zeros'):
            all_ruptures = sorted(all_ruptures)
            for site_id, (gmv, n_assets) in site_gmv.iteritems():
                array = numpy.array([gmv.get(r, 0.) for r in all_ruptures])
                gmv.clear()  # save memory
                all_gmvs.extend([array] * n_assets)
        return all_assets, (all_gmvs, all_ruptures)

    @classmethod
    def make_epsilons(cls, lt_model, num_assets, seed, correlation):
        ses_coll = models.SESCollection.objects.get(lt_model=lt_model)
        num_ruptures = ses_coll.get_ruptures().count()
        zeros = numpy.zeros((num_assets, num_ruptures))
        return scientific.make_epsilons(zeros, seed, correlation)


class BCRGetter(object):
    def __init__(self, getter_orig, getter_retro):
        self.assets = getter_orig.assets
        self.getter_orig = getter_orig
        self.getter_retro = getter_retro
        self.hid = getter_orig.hid
        self.weight = getter_orig.hid

    def __call__(self, monitor):
        assets, orig = self.getter_orig(monitor)
        _assets, retro = self.getter_retro(monitor)
        return assets, (orig, retro)


class GetterBuilder(object):
    """
    .asset_ids
    .site_ids

    Warning: instantiation a GetterBuilder performs a potentially
    expensive geospatial query.
    """
    def __init__(self, gettercls, riskmodel, rc):
        self.gettercls = gettercls
        self.riskmodel = riskmodel
        self.rc = rc
        self.hc = rc.get_hazard_calculation()
        self.max_dist = rc.best_maximum_distance * 1000 # km to meters
        cursor = connections['job_init'].cursor()
        cursor.execute("""
SELECT DISTINCT ON (exp.id) exp.id AS asset_id, hsite.id AS site_id
FROM riski.exposure_data AS exp
JOIN hzrdi.hazard_site AS hsite
ON ST_DWithin(exp.site, hsite.location, %s)
WHERE hsite.hazard_calculation_id = %s
AND exposure_model_id = %s AND taxonomy=%s
AND ST_COVERS(ST_GeographyFromText(%s), exp.site)
ORDER BY exp.id, ST_Distance(exp.site, hsite.location, false)
""", (self.max_dist, self.hc.id, rc.exposure_model.id,
      self.riskmodel.taxonomy, rc.region_constraint.wkt))
        self.asset_ids, self.site_ids = zip(*cursor.fetchall())

    def indices_site_assets(self, all_assets)
        indices = []
        site_assets = collections.defaultdict(list)
        for asset in all_assets:
            try:
                idx = self.asset_ids.index(asset.id)
            except ValueError:  # asset.id not in list
                logs.LOG.info(
                "No hazard with imt %s has been found for "
                "the asset %s within %s km", self.riskmodel.imt,
                    asset, self.max_dist)
            else:
                site_id = self.site_ids[idx]
                site_assets[site_id].append(asset)
                indices.append(idx)
        return site_assets, indices

    def init_getters(self, hazard_outputs, site_assets, indices):
        epsilons = self.gettercls.make_epsilons(len(self.asset_ids))
        getters = []
        for ho in self.hazard_outputs:
            getter = self.gettercls(ho, site_assets.items(), self.riskmodel.imt)
            if epsilons is not None:
                getter.epsilons = self.epsilons[indices]
            getters.append(getter)
        self.riskmodel.getters = getters

