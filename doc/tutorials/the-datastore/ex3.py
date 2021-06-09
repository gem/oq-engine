from openquake.commonlib.datastore import read

# first run qa_tests_data/classical/case_1/job.ini

dstore = read(-1)
rup_df = dstore.read_df('rup')
print(rup_df)
