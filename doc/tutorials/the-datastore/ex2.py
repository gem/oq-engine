import pandas
from openquake.baselib import hdf5

rup_df = pandas.DataFrame({
    'rup_id': [0, 1, 2],
    'mag': [4.5, 5.5, 6.5]})

with hdf5.File('ex2.hdf5', 'w') as f:
    f.create_df('rup', rup_df)
    # stores one dataset per column, plus an attribute __pdcolumns__
