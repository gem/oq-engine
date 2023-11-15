.. _working-with-the-dstore:

Working with the dstore
=======================

Advanced users could find useful to work directly with the dstore*.
The use of the dstore is consider experimental as the structure may change across versions.
Here we document some of the most common operations for end-users.

Read dstore with python
-----------------------

Read the dstore for a given calculation id::

	>> from openquake.commonlib.datastore import read
	>> dstore = read(calc_id)   # Read a given calculation id
    >> list(dstore)             # See availabe datastore keys

Extract the parameters used in the calculation::

	>> oq = dstore["oqparam"]
    >> list(oq)                 # See available parameters
    >> oq.rupture_mesh_spacing
    2.0
    >> oq.ses_per_logic_tree_path
    1000


Reading outputs with pandas
---------------------------

If you are a scientist familiar with Pandas, you will be happy to know that it is possible to process the engine outputs 
with it. Here we will give a couple of examples

Hazard curves
~~~~~~~~~~~~~
Suppose you ran the hazard **AreaSourceClassicalPSHA** demo, with calculation ID=42; then you can process the hazard curves as 
follows::

	>> from openquake.commonlib.datastore import read
	>> dstore = read(42)
	>> df = dstore.read_df('hcurves-stats', index='lvl',
	..                     sel=dict(imt='PGA', stat='mean', site_id=0))
	     site_id stat     imt     value
	lvl
	0      0  b'mean'  b'PGA'  0.999982
	1      0  b'mean'  b'PGA'  0.999949
	2      0  b'mean'  b'PGA'  0.999850
	3      0  b'mean'  b'PGA'  0.999545
	4      0  b'mean'  b'PGA'  0.998634
	..   ...      ...     ...       ...
	44     0  b'mean'  b'PGA'  0.000000

The dictionary ``dict(imt='PGA', stat='mean', site_id=0)`` is used to select subsets of the entire dataset: in this case 
hazard curves for mean PGA for the first site.

If you do not like pandas, or for some reason you prefer plain numpy arrays, you can get a slice of hazard curves by 
using the ``.sel`` method::

	>> arr = dstore.sel('hcurves-stats', imt='PGA', stat='mean', site_id=0)
	>> arr.shape  # (num_sites, num_stats, num_imts, num_levels)
	(1, 1, 1, 45)

Notice that the ``.sel`` method does not reduce the number of dimensions of the original array (4 in this case), it just 
reduces the number of elements. It was inspired by a similar functionality in xarray.

Event loss table
~~~~~~~~~~~~~~~~
Suppose you ran the risk **EventBasedRisk** demo, with calculation ID=50; then you can process the event loss table
(dstore key ``risk-by-event``) as follows::

    >> from openquake.commonlib.datastore import read
    >> dstore = read(50)
    >> df = dstore.read_df('risk_by_event')
        event_id  agg_id  loss_id      variance          loss
    0          217       5        2  1.334203e+14  4.602987e+08
    1          217       5        3  5.384151e+14  7.817219e+08
    2          218       5        2  4.987701e+11  3.446305e+07
    3          218       5        3  1.859565e+12  5.651559e+07
    4          219       5        2  6.985281e+10  6.659544e+06
    ...        ...     ...      ...           ...           ...
    7389      1739       1        3  2.229089e+11  2.603723e+06
    7390      1740       1        2  4.362298e+11  1.359160e+07
    7391      1740       1        3  1.462301e+12  2.110337e+07
    7392      1741       1        2  7.072199e+11  2.098369e+07
    7393      1741       1        3  4.615159e+12  3.818096e+07

It is possible to extract the ``agg_key`` with::

    >> agg_key = pd.DataFrame({'agg_key':dstore['agg_keys']})
    >> agg_key['agg_id'] = agg_key.index

To get the corresponding ``loss_id``, users need::

    >> from openquake.risklib.scientific import LOSSID
    >> pd.DataFrame.from_dict(LOSSID, orient='index')
                                                        0
    business_interruption                                0
    contents                                             1
    nonstructural                                        2
    structural                                           3
    ...                                                 ...

    structural_ins+contents_ins+business_interrupti...  40
    nonstructural_ins+contents_ins+business_interru...  41
    structural_ins+nonstructural_ins+contents_ins+b...  42


Example: how many events per magnitude?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When analyzing an event based calculation, users are often interested in checking the magnitude-frequency distribution, 
i.e. to count how many events of a given magnitude are present in the stochastic event set for a fixed investigation 
time and a fixed ``ses_per_logic_tree_path.`` You can do that with code like the following::

	def print_events_by_mag(calc_id):
	    # open the DataStore for the current calculation
	    dstore = datastore.read(calc_id)
	    # read the events table as a Pandas dataset indexed by the event ID
	    events = dstore.read_df('events', 'id')
	    # find the magnitude of each event by looking at the 'ruptures' table
	    events['mag'] = dstore['ruptures']['mag'][events['rup_id']]
	    # group the events by magnitude
	    for mag, grp in events.groupby(['mag']):
	        print(mag, len(grp))   # number of events per group

If you want to know the number of events per realization and per stochastic event set you can just refine the *groupby* 
clause, using the list ``['mag', 'rlz_id', 'ses_id']`` instead of simply ``['mag']``.

Given an event, it is trivial to extract the ground motion field generated by that event, if it has been stored 
(warning: events producing zero ground motion are not stored). It is enough to read the ``gmf_data`` table indexed by 
event ID, i.e. the ``eid`` field::

	>> eid = 20  # consider event with ID 20
	>> gmf_data = dstore.read_df('gmf_data', index='eid') # engine>3.11
	>> gmf_data.loc[eid]
	     sid     gmv_0
	eid
	20    93   0.113241
	20   102   0.114756
	20   121   0.242828
	20   142   0.111506

The ``gmv_0`` refers to the first IMT; here I have shown an example with a single IMT, in presence of multiple IMTs you 
would see multiple columns ``gmv_0, gmv_1, gmv_2, ....`` The ``sid`` column refers to the site ID.

As a following step, you can compute the hazard curves at each site from the ground motion values by using the function 
*gmvs_to_poes*, available since engine 3.10::

	>> from openquake.commonlib.calc import gmvs_to_poes
	>> gmf_data = dstore.read_df('gmf_data', index='sid')
	>> df = gmf_data.loc[0]  # first site
	>> gmvs = [df[col].to_numpy() for col in df.columns
	..         if col.startswith('gmv_')]  # list of M arrays
	>> oq = dstore['oqparam']  # calculation parameters
	>> poes = gmvs_to_poes(gmvs, oq.imtls, oq.ses_per_logic_tree_path)

This will return an array of shape (M, L) where M is the number of intensity measure types and L the number of levels 
per IMT. This works when there is a single realization; in presence of multiple realizations one has to collect 
together set of values corresponding to the same realization (this can be done by using the relation ``event_id -> rlz_id``) 
and apply ``gmvs_to_poes`` to each set.

NB: another quantity one may want to compute is the average ground motion field, normally for plotting purposes. In 
that case special care must be taken in the presence of zero events, i.e. events producing a zero ground motion value 
(or below the ``minimum_intensity``): since such values are not stored you have to enlarge the gmvs arrays with the 
missing zeros, the number of which can be determined from the ``events`` table for each realization. The engine is able 
to compute the ``avg_gmf`` correctly, however, since it is an expensive operation, it is done only for small 
calculations.