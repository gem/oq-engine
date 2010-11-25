"""
Core computation methods for the risk 'engine'
These include Classical PSHA-based risk analysis,
and deterministic analysis based on either a set of GMF files,
or a single GMF file."""

from openquake import kvs

# risk tokens
CONDITIONAL_LOSS_KEY_TOKEN = 'LOSS_AT_'
EXPOSURE_KEY_TOKEN = 'ASSET'
GMF_KEY_TOKEN = 'GMF'
LOSS_RATIO_CURVE_KEY_TOKEN = 'LOSS_RATIO_CURVE'
LOSS_CURVE_KEY_TOKEN = 'LOSS_CURVE'

def LOSS_TOKEN(poe):
    return "%s%s" % (CONDITIONAL_LOSS_KEY_TOKEN, str(poe))

def vuln_key(job_id):
    """Generate the key used to store vulnerability curves."""
    return kvs.generate_product_key(job_id, "VULN_CURVES")

def asset_key(job_id, row, col):
    return kvs._generate_key([job_id, row, col, EXPOSURE_KEY_TOKEN])

def loss_ratio_key(job_id, row, col, asset_id):
    return kvs._generate_key([job_id, row, col, LOSS_RATIO_CURVE_KEY_TOKEN, asset_id]) 

def loss_curve_key(job_id, row, col, asset_id):
    return kvs._generate_key([job_id, row, col, LOSS_CURVE_KEY_TOKEN, asset_id]) 

def loss_key(job_id, row, col, asset_id, poe):
    return kvs._generate_key([job_id, row, col, LOSS_TOKEN(poe), asset_id]) 
    
# def asset_list_key(job_id, ):
#    return kvs._generate_key([job_id, ])