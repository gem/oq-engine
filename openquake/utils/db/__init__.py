from sqlalchemy.databases import postgres
import geoalchemy

# This allows us to reflect 'geometry' columns from PostGIS tables.
# This is slightly hack-ish, but it's either this or we have to declare
# columns with the appropriate type manually (yuck).
postgres.ischema_names['geometry'] = geoalchemy.Geometry



def create_engine(
    dbname, user, password='', host='localhost', engine='postgresql'):
    """
    Function wrapper for :py:func:`sqlalchemy.create_engine` which helps
    generate a db connection string.
    """

    conn_str = '%s://%s:%s@%s/%s' % (engine, user, password, host, dbname)
    db = sqlalchemy.create_engine(conn_str)
    return db
