import sqlalchemy

from openquake import java


def create_engine(
    dbname, user, password='', host='localhost', engine='postgres'):
    """
    Function wrapper for :py:func:`sqlalchemy.create_engine` which helps
    generate a db connection string.
    """

    conn_str = '%s://%s:%s@%s/%' % (engine, user, password, host, dbname)
    db = sqlalchemy.create_engine(conn_str)
    return db


class SourceModelLoader(object):
    """
    Uses parsers (written in Java) to read a source model data from a file and
    injects the data into the appropriate database tables.
    """

    SRC_DATA_PKG = 'org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData'
    # Java class names, with simple keys
    # Makes comparisons easy
    SRC_DATA_MAP = {
        '%s.GEMFaultSourceData' % SRC_DATA_PKG: {
            'si_type': 'simple', 'fn': _read_simple_fault_src},
        '%s.GEMSubductionFaultSourceData' % SRC_DATA_PKG: {
            'si_type': 'complex', 'fn': _read_complex_fault_src},
        '%s.GEMAreaSourceData' % SRC_DATA_PKG: {
            'si_type': 'area', 'fn': _read_area_src},
        '%s.GEMPointSourceData' % SRC_DATA_PKG: {
            'si_type': 'point', 'fn': _read_point_src},}

    def __init__(self, src_model_path, engine, mfd_bin_width=0.1):
        """
        :param src_model_path: path to a source model file
        :type src_model_path: str

        :param engine: db engine to provide connectivity and reflection
        :type engine: :py:class:`sqlalchemy.engine.base.Engine`

        :param mfd_bin_width: Magnitude Frequency Distribution bin width
        :type mfd_bin_width: float
        """
        self.src_model_path = src_model_path
        self.engine = engine

        # Java SourceModelReader object
        self.src_reader = java.jclass('SourceModelReader')(
            src_model_path, mfd_bin_width)

    def serialize(self):
        """
        Read the source model and inject it into the database.

        :returns: number of rows inserted TODO: dict of insertions, keyed by
            tablename?
        """
        insert_data = self.read_model()
        self.write_to_db(insert_data)

    def read_model(self):
        """
        Read the source model data.

        Return a dict of stuff.
        TODO: explain me better, fool
        """

        data_dicts = []

        source_data = self.src_reader.read()  # ArrayList of source data types
        for src in source_data:
            # first, figure out what type we're dealing with
            src.__javaclass__.getName()
            source_type = src.__javaclass__.getName()
            if source_type == SRC_DATA_MAP['simple']:
                pass
            elif source_type == SRC_DATA_MAP['complex']:
                pass
            elif source_type == SRC_DATA_MAP['area']:
                pass
            elif source_type == SRC_DATA_MAP['point']:
                pass
            else:
                pass
                # TODO: raise an error; unknown type

    def write_to_db(self, insert_data):
        pass

def _read_simple_fault_src():
    pass

def _read_complex_fault_src():
    pass

def _read_area_src():
    pass

def _read_point_src():
    pass
        
        


if __name__ == "__main__":
    pass
