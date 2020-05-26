Reading outputs with pandas
================================

If you are a scientist familiar with Pandas, you will be happy to know that
it is possible to process the engine outputs with it.
Here we will give an example involving hazard curves.

Suppose you ran the AreaSourceClassicalPSHA demo, with calculation ID=42;
then you can process the hazard curves as follows::

  >>> from openquake.baselib.datastore import read
  >>> dstore = read(42)
  >>> df = dstore.read_df('hcurves-stats', index='lvl',
  ...                     sel=dict(imt='PGA', stat='mean', sid=0))
       sid     stat     imt     value
  lvl                                
  0      0  b'mean'  b'PGA'  0.999982
  1      0  b'mean'  b'PGA'  0.999949
  2      0  b'mean'  b'PGA'  0.999850
  3      0  b'mean'  b'PGA'  0.999545
  4      0  b'mean'  b'PGA'  0.998634
  ..   ...      ...     ...       ...
  44     0  b'mean'  b'PGA'  0.000000

The dictionary ``dict(imt='PGA', stat='mean', sid=0)`` is used to select
subsets of the entire dataset.
