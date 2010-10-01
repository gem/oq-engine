# -*- coding: utf-8 -*-
"""
In this module, we collect functions that are used in the context
of identifiers used in opengem (e.g., memcached keys).
"""

# using '!' as separator in keys, because it is not used in numbers
MEMCACHE_KEY_SEPARATOR = '!'
INTERNAL_ID_SEPARATOR = ':'

SITES_KEY_TOKEN = 'sites'

HAZARD_CURVE_KEY_TOKEN = 'hazard_curve'
EXPOSURE_KEY_TOKEN = 'exposure'
VULNERABILITY_CURVE_KEY_TOKEN = 'vulnerability_curves'

LOSS_RATIO_CURVE_KEY_TOKEN = 'loss_ratio_curve'
LOSS_CURVE_KEY_TOKEN = 'loss_curve'
CONDITIONAL_LOSS_KEY_TOKEN = 'loss_conditional'

def get_sequence():
    """generator for sequence IDs"""
    counter = 0
    while(True):
        counter += 1
        yield counter

def get_id(prefix):
    """generator for task IDs (prefix+sequence number)"""
    counter = 0
    while(True):
        counter += 1
        yield INTERNAL_ID_SEPARATOR.join((str(prefix), str(counter)))

def get_product_key(job_id, block_id, site, product):
    """construct memcached key from several part IDs"""
    if site is not None:
        return MEMCACHE_KEY_SEPARATOR.join((str(job_id), str(block_id),
                                            str(site), str(product)))
    else:
        return MEMCACHE_KEY_SEPARATOR.join((str(job_id), str(block_id),
                                            str(product)))

