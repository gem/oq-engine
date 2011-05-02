import sqlalchemy
import geoalchemy

from sqlalchemy.databases import postgres

# This allows us to reflect 'geometry' columns from PostGIS tables.
# This is slightly hack-ish, but it's either this or we have to declare
# columns with the appropriate type manually (yuck).
postgres.ischema_names['geometry'] = geoalchemy.Geometry

# Tablespaces
PSHAI_TS = 'pshai'
ADMIN_TS = 'admin'
EQCAT_TS = 'eqcat'


# Table/column dicts.
# These can be used as a template for doing db inserts.
SIMPLE_FAULT = dict.fromkeys(
    # required:
    'owner_id', 'gid', 'dip', 'upper_depth', 'lower_depth', 'geom',
    # xor:
    'mfd_tgr_id', 'mgf_evd_id',
    # optional:
    'name', 'description', 'outline')
SOURCE = dict.fromkeys(
    # required:
    'owner_id', 'simple_fault_id', 'gid', 'si_type', 'tectonic_region',
    # optional:
    'name', 'description', 'rake', 'hypocentral_depth')
MFD_EVD = dict.fromkeys(
    # required:
    'owner_id', 'gid', 'magnitude_type', 'min_val', 'bin_size', 'mfd_values'
    # optional:
    'name', 'description', 'total_cumulative_rate', 'total_moment_rate')
MFD_TGR = dict.fromkeys(
    # required:
    'owner_id', 'gid', 'magnitude_type', 'min_val', 'max_val', 'a_val', 'b_val'
    # optional:
    'name', 'description', 'total_cumulative_rate', 'total_moment_rate')


def create_engine(
    dbname, user, password='', host='localhost', engine='postgresql'):
    """
    Function wrapper for :py:func:`sqlalchemy.create_engine` which helps
    generate a db connection string.
    """

    conn_str = '%s://%s:%s@%s/%s' % (engine, user, password, host, dbname)
    db = sqlalchemy.create_engine(conn_str)
    return db
