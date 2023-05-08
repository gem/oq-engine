# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
Module :mod:`openquake.hmtk.seismicity.declusterer.dec_reasenberg`
defines the Reasenberg declustering algorithm
"""

from bisect import bisect_left
from typing import Callable, Tuple, Dict, Optional
from openquake.hazardlib.geo.geodetic import geodetic_distance, distance, _prepare_coords 
import numpy as np

# import datetime
from openquake.hmtk.seismicity.declusterer.base import (BaseCatalogueDecluster, DECLUSTERER_METHODS)
from openquake.hmtk.seismicity.utils import haversine



@DECLUSTERER_METHODS.add(
    "decluster",
    taumin=1.0,  # look ahead time for not clustered events, days
    taumax=10.0,  # maximum look ahead time for clustered events, days
    P=0.95,  # confidence level that this is next event in sequence
    xk=0.5,  # factor used with xmeff to modify magnitude cutoff during clusters
    xmeff=1.5,  # magnitude effective, used with xk to define magnitude cutoff
    rfact=10,  # factor for interaction radius for dependent events
    horiz_error=1.5,  # epicenter error, km.  if unspecified or None, it is pulled from the catalogue
    depth_error=2.0,  # depth error, km.  if unspecified or None, it is pulled from the catalogue
    interaction_formula='Reasenberg1985',  # either `Reasenberg1985` or `WellsCoppersmith1994`
    max_interaction_dist=np.inf  # km, some studies limit to crustal thickness (ex. 30)
)
class Reasenberg(BaseCatalogueDecluster):
    """
    This class implements the Reasenberg algorithm as described in
    this paper:

    Reasenberg, P., 1985. Second‐order moment of central California
    seismicity, 1969–1982. Journal of Geophysical Research: Solid Earth,
    90(B7), pp.5479-5495.

    Declustering code originally converted to MATLAB by A. Allman.
    Then, highly modified and converted to Python by CG Reyes. Further modified by K Bayliss.


    # default_config = dict(taumin=1.0,  # tau(t==0)
    #                       taumax=10.,  # tau(t -> inf), computational simplification should be scaled to local bg rate
    #                       P=0.95,
    #                       xk=0.5,
    #                       xmeff=1.5,
    #                       rfact=10.,
    #                       horiz_error=1.5,
    #                       depth_error=2.,
    #                       dmethod='gc', ## REMOVED
    #                       interaction_formula='Reasenberg1985',
    #                       max_interaction_dist=30  # km, limit to crustal distance
    #                       )

    """

    def __init__(self):
        self.verbose = False
        self.interaction_formulas = {'Reasenberg1985': lambda m: 0.011 * 10 ** (0.4 * m),
                                     'WellsCoppersmith1994': lambda m: 0.01 * 10 ** (0.5 * m)}  # Helmstetter (SRL) 2007

    @staticmethod
    def clust_look_ahead_time(mag_big: float, dt_big: np.ndarray, xk: float, xmeff: float, p: float) -> np.ndarray:
        """ CLUSTLOOKAHEAD calculate look ahead time for clustered events

        :param mag_big:
            biggest magnitude in the cluster
        :param dt_big:
            days difference between biggest event and this one
        :param xk:
            factor used with xmeff to define magnitude cutoff - increases effective magnitude during clusters
        :param xmeff:
            magnitude effective, used with xk to define magnitude cutoff
        :param p:
            confidence level that this is next event in sequence
        :returns:
            tau: look-ahead time for clustered events (days)
        """

        deltam = (1 - xk) * mag_big - xmeff  # delta in magnitude

        if deltam < 0:
            deltam = 0

        denom = 10.0 ** ((deltam - 1) * 2 / 3)  # expected rate of aftershocks
        top = -np.log(1 - p) * dt_big  # natural log, verified in Reasenberg
        tau = top / denom  # equation from Reasenberg paper
        return tau
         

    def decluster(self, catalogue, config) -> Tuple[np.ndarray, np.ndarray]:
        """
        decluster the catalog using the provided configuration

        :param catalogue: Catalogue of earthquakes
        :param config: Configuration parameters
        :returns:
          **vcl vector** indicating cluster number,
          **ms vector** indicating which events should be considered mainshock events

        if catalogue contains additional data keys data['depthError'] and/or
        data['horizError'], containing the location error for each event, then
        these will be used to bring the decluster distance closer together
        [additively].  To override the inbuilt catalog depth and horiz errors,
        set the value of config['depth_error'] and config['horiz_error'] respectively

        """

        self.verbose = config.get('verbose', self.verbose)
        # Get relevant parameters
        neq = catalogue.get_number_events()  # Number of earthquakes

        min_lookahead_days = config['taumin']
        max_lookahead_days = config['taumax']

        # Get elapsed days
        elapsed = days_from_first_event(catalogue)

        assert np.all(elapsed[1:] >= elapsed[:-1]), "catalogue needs to be in ascending date order"

        # easy-access variables
        ### What even is dmethod? This is literally never explained...
        #if config.get('dmethod', 'gc') == 'gc':
        #    surf_pos = (catalogue['latitude'], catalogue['longitude'])
        #    event_distance = event_gc_distance

        #elif config['dmethod'] == 'p2p':
        #    surf_pos = geodetic_to_ecef(catalogue['latitude'], catalogue['longitude'])  # assumes at surface
        #    event_distance = event_p2p_distance
        #else:
        #    raise ValueError("unknown configuration dmethod. it should be 'gc' or 'p2p'")

        mags = catalogue['magnitude']
        depth = catalogue['depth']

        # Errors are determined 1st by the config. If this value doesn't exist or is None, then get the
        # error values from the catalog.  If errors do not exist within the catalog, then set the errors to 0.
        if config.get('horiz_error', None) is None:
            horiz_error = catalogue.data.get('horizError', np.zeros(1))
        else:
            horiz_error = config['horiz_error']

        if config.get('depth_error', None) is None:
            depth_error = catalogue.data.get('depthError', np.zeros(1))
        else:
            depth_error = config['depth_error']

        # Pre-allocate cluster index vectors
        vcl = np.zeros(neq, dtype=int).flatten()
        msi = np.zeros(neq, dtype=int).flatten()
        ev_id = np.zeros(neq, dtype=int).flatten()
        # set the interaction zones, in km
        # Reasenberg 1987 or alternate version: Wells & Coppersmith 1994 / Helmstetter (SRL) 2007
        zone_noclust, zone_clust = self.get_zone_distances_per_mag(
            mags=mags,
            rfact=config['rfact'],
            formula=self.interaction_formulas[config['interaction_formula']],
            max_interact_km=config.get('max_interaction_dist', np.inf))

        k = 0  # clusterindex

        # variable to store information whether earthquake is already clustered
        clusmaxmag = np.array([-np.inf] * neq)
        clus_biggest_idx = np.zeros(neq, dtype=int)

        # for every earthquake in catalog, main loop
        for i in range(neq - 1):
            ev_id[i] = i
            my_mag = mags[i]

            # variable needed for distance and timediff
            my_cluster = vcl[i]
            not_classified = my_cluster == 0

            # attach interaction time

            if not_classified:
                # this event is not associated with a cluster, yet
                # self.debug_print(i, ' is not in a cluster')
                look_ahead_days = min_lookahead_days

            elif my_mag >= clusmaxmag[my_cluster]:
                # this is the biggest event  in this cluster, so far (or equal to it).
                # note, if this is now the biggest, then the cluster range collapses into its radius
                # self.debug_print(f'{i} is the biggest event of cluster M={my_mag}')
                clusmaxmag[my_cluster] = my_mag
                clus_biggest_idx[my_cluster] = i
                look_ahead_days = min_lookahead_days
                # time between largest event in cluster and this event is 0, so use min_lookahead_days (rather than 0).
            else:
                # this event is already tied to a cluster, but is not the largest event
                #self.debug_print(i, ' is already in cluster, but not biggest')
                idx_biggest = clus_biggest_idx[my_cluster]
                days_since_biggest = elapsed[i] - elapsed[idx_biggest]
                # set new look_ahead_days (function of time from largest event in cluster)
                look_ahead_days = self.clust_look_ahead_time(clusmaxmag[my_cluster],
                                                             days_since_biggest,
                                                             config['xk'],
                                                             config['xmeff'],
                                                             config['P'])
                
                # look_ahead_days should be > min and < max to prevent this running forever...
                look_ahead_days = np.clip(look_ahead_days, min_lookahead_days, max_lookahead_days)

            # extract eqs that fit interaction time window --------------

            max_elapsed = elapsed[i] + look_ahead_days
            next_event = i + 1
            # find location of last event between elapsed and max_elapsed
            last_event = bisect_left(elapsed, max_elapsed, lo=next_event)
            #print("last event", last_event, "i", i)
            # range from next event (i+1) to last event (end of the lookahead time)
            temporal_evs = np.arange(next_event, last_event)
            #print("temp_ev ", temporal_evs)
            if my_cluster != 0:
                # If we are in a cluster, consider only events that are not already in the cluster
                temporal_evs = temporal_evs[vcl[temporal_evs] != my_cluster]

            if len(temporal_evs) == 0:
                continue

            # ------------------------------------
            # one or more events have now passed the time window test. Now compare
            # this subcatalog in space to A) most recent and B) largest event in cluster
            # ------------------------------------

            my_biggest_idx = clus_biggest_idx[my_cluster]
            bg_ev_for_dist = i if not_classified else my_biggest_idx

            dist_to_recent = distance(catalogue.data['latitude'][i], catalogue.data['longitude'][i], depth[i], catalogue.data['latitude'][temporal_evs], catalogue.data['longitude'][temporal_evs], depth[temporal_evs])
            dist_to_biggest = distance(catalogue.data['latitude'][bg_ev_for_dist], catalogue.data['longitude'][bg_ev_for_dist], depth[bg_ev_for_dist], catalogue.data['latitude'][temporal_evs], catalogue.data['longitude'][temporal_evs], depth[temporal_evs])
            
            if look_ahead_days == min_lookahead_days:
                l_big = dist_to_biggest == 0  # all false
                l_recent = dist_to_recent <= zone_noclust[my_mag]

            else:
                l_big = dist_to_biggest <= zone_noclust[clusmaxmag[my_cluster]]
                l_recent = dist_to_recent <= zone_clust[my_mag]

            spatial_evs = np.logical_or(l_recent, l_big)

            if not any(spatial_evs):
                # self.debug_print()
                continue

            # ------------------------------------
            # one or more events have now passed both spatial and temporal window tests
            #
            # if there are events in this cluster that are already related to another
            # cluster, figure out the smallest cluster number. Then, assign all events
            # (both previously clustered and unclustered) to this new cluster number.
            # ------------------------------------

            # spatial events only include events AFTER i, not i itself
            # so vcl[events_in_any_cluster] is independent from vcl[i]

            candidates = temporal_evs[spatial_evs]  # eqs that fit spatial and temporal criterion
            events_in_any_cluster = candidates[vcl[candidates] != 0]  # eqs which are already related with a cluster
            events_in_no_cluster = candidates[vcl[candidates] == 0]  # eqs that are not already in a cluster

            # if this cluster overlaps with any other cluster, then merge them
            # assign every event in all related clusters to the same (lowest) cluster number
            # set this cluster's maximum magnitude "clusmaxmag" to the largest magnitude of all combined events
            # set this cluster's clus_biggest_idx to the (most recent ??) largest event of all combined events
            # Flag largest event in each cluster

            if len(events_in_any_cluster) > 0:
                if not_classified:
                    related_clust_nums = np.unique(vcl[events_in_any_cluster])
                else:
                    # include this cluster number in the reckoning
                    related_clust_nums = np.unique(np.hstack((vcl[events_in_any_cluster], my_cluster,)))

                # associate all related events with my cluster
                my_cluster = related_clust_nums[0]
                vcl[i] = my_cluster
                vcl[candidates] = my_cluster

                for clustnum in related_clust_nums:
                    vcl[vcl == clustnum] = my_cluster

                events_in_my_cluster = vcl == my_cluster
                biggest_mag = np.max(mags[events_in_my_cluster])

                biggest_mag_idx = np.flatnonzero(np.logical_and(mags == biggest_mag, events_in_my_cluster))[-1]

                # reset values for other clusters
                clusmaxmag[related_clust_nums] = -np.inf
                clus_biggest_idx[related_clust_nums] = 0

                # assign values for this cluster
                clusmaxmag[my_cluster] = biggest_mag
                clus_biggest_idx[my_cluster] = biggest_mag_idx

            elif my_cluster == 0:
                k += 1
                vcl[i] = my_cluster = k
                clusmaxmag[my_cluster] = my_mag
                clus_biggest_idx[my_cluster] = i
            else:
                pass  # no events found, and attached to existing cluster

            # attach clustnumber to catalogue yet unrelated to a cluster
            vcl[events_in_no_cluster] = my_cluster
            
            # set mainshock index for all events not in a cluster to be 1 also
            # i.e. an independent event counts as a mainshock
            msi[events_in_no_cluster] = 1
            
            # for each cluster, identify mainshock
            clusters = np.unique(vcl)
            for cluster_no in clusters:
                cluster_ids = ev_id[vcl == cluster_no]
                biggest_mag_idx = np.where(np.max(mags[vcl == cluster_no]))
                ms_id = cluster_ids[biggest_mag_idx]
                #ms_id = np.where(mags == biggest_mag, cluster_ids))[-1]
                #ms_id = np.asarray(np.max(mags[vcl = cluster_no]).nonzero()
                msi[ms_id] = 1
            
        return vcl, msi

    @staticmethod
    def get_zone_distances_per_mag(mags: np.ndarray, rfact: float, formula: Callable,
                                   max_interact_km: float = np.inf) -> Tuple[Dict, Dict]:
        """
        :param mags:
            list of magnitudes
        :param rfact:
            interaction distance scaling value for clusters
        :param formula:
            formula that takes magnitudes and returns interaction distances
        :param max_interact_km:
            if used, may refer to crustal thickness
        :returns:
            dictionaries keyed on sorted unique magnitudes.
            zone_noclust :
                dictionary of interaction distances when not in a cluster
                so, zone_noclust[mag] -> out-of-cluster interaction distance for mag
            zone_clust :
                dictionary of interaction distances when IN a cluster
                so, zone_noclust[mag] -> in-cluster interaction distance for mag
        """

        unique_mags = np.unique(mags)
        noclust_km = formula(unique_mags)
        clust_km = noclust_km * rfact

        # limit interaction distance [generally to one crustal thickness], in km
        noclust_km[noclust_km > max_interact_km] = max_interact_km
        clust_km[clust_km > max_interact_km] = max_interact_km

        zone_noclust = dict(zip(unique_mags, noclust_km))
        zone_clust = dict(zip(unique_mags, clust_km))
        return zone_noclust, zone_clust

    def debug_print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

def relative_time(years, months, days, hours=None, minutes=None, seconds=None, datetime_unit ='D', reference_date=None):
    """ Get elapsed days since first event in catalog

    :param reference_date
        use this array of [Y, M, D, h, m, s] instead of first event in catalog
    :type: Array
    :returns:
    **elapsed** number of days since reference_date (which defaults to the first event in catalog)
    :rtype: numpy.timedelta64 array
    """

    import datetime
    if hours is None and minutes is None and seconds is None:
        dates = [datetime.datetime(
            *[years[n], months[n], days[n]])
            for n in range(len(years))]
    else:
        hours = hours if minutes is not None else np.zeros_like(years)
        minutes = minutes if minutes is not None else np.zeros_like(years)
        seconds = seconds if seconds is not None else np.zeros_like(years)

        dates = [datetime.datetime(
            *[years[n], months[n], days[n],hours[n], minutes[n], seconds[n].astype(int)])
            for n in range(len(years))]

    dt64 = np.array([np.datetime64(v) for v in dates])
    if reference_date:
        from_day = np.datetime64(datetime.datetime(*reference_date))
    else:
        from_day = min(dt64)

    return (dt64 - from_day) / np.timedelta64(1, datetime_unit)


def days_from_first_event(catalog) -> relative_time:
    return relative_time(catalog['year'], catalog['month'], catalog['day'],
                         catalog['hour'], catalog['minute'],
                         catalog['second'].astype(int),
                         datetime_unit='D')


def get_distance_errors(directional_error, src_idx, targ_idxs) -> Tuple[float, np.ndarray]:
    """

    :param directional_error:
    :param src_idx:
    :param targ_idxs:
    :return:
    """
    if directional_error is None:
        directional_error = 0.

    if isinstance(directional_error, (np.ndarray,)):
        src_err = directional_error[src_idx]
        targ_err = directional_error[targ_idxs]
    else:
        src_err = directional_error
        targ_err = directional_error
    return src_err, targ_err
    

