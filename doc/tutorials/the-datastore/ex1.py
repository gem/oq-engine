import pandas
# requires tables too

rup_df = pandas.DataFrame({
    'rup_id': [0, 1, 2],
    'mag': [4.5, 5.5, 6.5]})
rup_df.to_hdf('ex1.hdf5', 'rup')
