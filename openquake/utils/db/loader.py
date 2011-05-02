import sqlalchemy

from openquake import java
from openquake.utils import db

MFD_PACKAGE = 'org.opensha.sha.magdist'

def read_simple_fault_src(source_data):
    """
    :param source_data:
    :type source_data: jpype-wrapped java object of type `GEMFaultSourceData`
    """
    # We'll need to insert into the following tables, in this order:
    #   mfd_evd or mfd_tgr
    #   simple_fault
    #   source

    mfd_java = source_data.getMfd()
    mfd_type = mfd_java.__javaclass__.getName()
    if mfd_type == '%s.IncrementalMagFreqDist' % MFD_PACKAGE:
        # this is an 'evenly discretized' mfd
        mfd = db.MFD_EVD.copy()

        # TODO: this is going to be removed. empty string is fine for now
        mfd['gid'] = ''

        # magnitude_type is default

        mfd['min_val'] = mfd_java.getMinX()
        mfd['bin_size'] = mfd_java.getDelta()

        # TODO: this needs to be a list of values
        # fix the schema, fool
        mfd['mfd_values'] = [mfd_java.getY(x) for x in range(mfd_java.getNum())]

        surface = java.jclass('StirlingGriddedSurface')(
            mfd_java.getTrace(), source_data.getDip(), source_data.getSeismDepthUpp(),
            source_data.getSeismDepthLow(), 1.0)  # TODO: 1.0 is grid spacing.. make this a constant?

        surface_area = surface.getSurfaceArea()

        # TODO: divide these two rates by the surface area to normalize
        mfd['total_cumulative_rate'] = mfd_java.getCumRate(mfd_java.getMinX()) / surface_area  # could change schema to be incremental, ! cumulative
        mfd['total_moment_rate'] = mfd_java.getTotalMomentRate() / surface_area

        # wrap the insert data in dict keyed by table name
        mfd_insert = {'%s.mfd_evd' % db.PSHAI_TS: mfd} 

    elif mfd_type == '%s.GutenbergRichterMagFreqDist' % MFD_PACKAGE:
        mfd = db.MFD_TGR.copy()

        # TODO: this is going to be removed.
        mfd['gid'] = ''

        # mangnitude_type is default

        mfd['min_val'] = None
        mfd['max_val'] = None
        mfd['a_val'] = None
        mfd['b_val'] = None
        mfd['total_cumulative_rate'] = None
        mfd['total_moment_rate'] = None

        mfd_insert = {'%s.mfd_tgr' % db.PSHAI_TS: mfd}

    else:
        raise ValueError("Unsupported MFD type: %s" % mfd_type)

    simple_fault = db.SIMPLE_FAULT.copy()
    source = db.SOURCE.copy()

    simple_fault_insert = {'%s.simple_fault' % db.PSHAI_TS: simple_fault}
    source_insert = {'%s.source' % db.PSHAI_TS: source}

    return mfd_insert, simple_fault_insert, source_insert

def read_complex_fault_src(source_data):
    """
    :param source_data:
    :type source_data: jpype-wrapped java object of type
        `GEMSubductionFaultSourceData`
    """

def read_area_src(source_data):
    """
    :param source_data:
    :type source_data: jpype-wrapped java object of type `GEMAreaSourceData`
    """


def read_point_src(source_data):
    """
    :param source_data:
    :type source_data: jpype-wrapped java object of type `GEMPointSourceData`
    """


def unknown_source_data_type(source_data):
    raise Exception
    # TODO: more detailed error


class SourceModelLoader(object):
    """
    Uses parsers (written in Java) to read a source model data from a file and
    injects the data into the appropriate database tables.
    """

    SRC_DATA_PKG = 'org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData'
    # Java class names, with simple keys
    # Makes comparisons easy
    SRC_DATA_FN_MAP = {
        '%s.GEMFaultSourceData' % SRC_DATA_PKG: {
            'fn': read_simple_fault_src},
        '%s.GEMSubductionFaultSourceData' % SRC_DATA_PKG: {
            'fn': read_complex_fault_src},
        '%s.GEMAreaSourceData' % SRC_DATA_PKG: {
            'fn': read_area_src},
        '%s.GEMPointSourceData' % SRC_DATA_PKG: {
            'fn': read_point_src},}

    def __init__(self, src_model_path, engine, mfd_bin_width=0.1, owner_id=1):
        """
        :param src_model_path: path to a source model file
        :type src_model_path: str

        :param engine: db engine to provide connectivity and reflection
        :type engine: :py:class:`sqlalchemy.engine.base.Engine`

        :param mfd_bin_width: Magnitude Frequency Distribution bin width
        :type mfd_bin_width: float

        :param owner_id: ID of an admin.organization entity in the database. By
            default, the default 'GEM Foundation' group will be used.
            Note(LB): This is kind of ugly and needs to be revisited later.
        """
        self.src_model_path = src_model_path
        self.engine = engine
        self.mfd_bin_width = mfd_bin_width
        self.owner_id = owner_id

        # Java SourceModelReader object
        self.src_reader = java.jclass('SourceModelReader')(
            self.src_model_path, self.mfd_bin_width)

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
            source_type_class = src.__javaclass__.getName()

            # now get the proper parsing function
            read_fn = SRC_DATA_FN_MAP.get(
                source_type_class, unknown_source_data_type)['fn']
            
            data_dicts.append(read_fn(src))

    def write_to_db(self, insert_data):
        pass

        
        


if __name__ == "__main__":
    pass
