#!/usr/bin/env python
# coding: utf-8

import numpy as np


def get_site_indexes(analysis):
    """
    This function produces a dictionary with key the site index and value a
    list constaining the IDs of the sources continuting to its hazard.

    :param:
        An instance of :class:`openquake._unc.analysis.Analysis`
    :returns:
        A dictionary with keys the site indexes and with value a list of the
        source IDs contributing to the hazard
    """

    # Get a dictionary with keys the source IDs
    dstores = analysis.dstores

    sites_per_src = {}
    for src_id in sorted(dstores):
        dstore = dstores[src_id]
        sites_per_src[src_id] = list(np.unique(dstore['_rates/sid'][:]))

    srcs_per_site = {}
    for key, sid_list in sites_per_src.items():
        for sid in sid_list:
            if sid in srcs_per_site:
                srcs_per_site[sid].append(key)
            else:
                srcs_per_site[sid] = [key]

    for sid, val in srcs_per_site.items():
        print(f'site {sid}: {val}')

    return srcs_per_site
