.. _rest-api:

OpenQuake Engine Server REST API
================================

Introduction
------------

oq engine server provides a series of REST API methods for running calculations, checking calculation status, and 
browsing and downloading results.

All responses are JSON, unless otherwise noted.

*****************
GET /v1/calc/list
*****************

List the available calculations. The url in each item of the response can be followed to retrieve complete calculation 
details.

Parameters: None

Response::

	[{"description": "Hazard Calculation for end-to-end hazard+risk",
	  "id": 1,
	  "status": "executing",
	  "calculation_mode": "classical",
	  "is_running": true,
	  "owner: "michele",
	  "url": "http://localhost:8800/v1/calc/1",
	  "abortable": true,
	  "size_mb": 2.34},
	 {"description": "Event based calculation",
	  "id": 2,
	  "status": "complete",
	  "calculation_mode": "event_based",
	  "is_running": false,
	  "owner: "armando",
	  "url": "http://localhost:8800/v1/calc/2",
	  "abortable": false,
	  "size_mb": 12.34},
	 {"description": "ScenarioRisk calculation",
	  "id": 3,
	  "status": "complete",
	  "calculation_mode": "scenario_risk",
	  "is_running": false,
	  "owner: "armando",
	  "url": "http://localhost:8800/v1/calc/3",
	  "abortable": false,
	  "parent_id": null,
	  "size_mb": 1.23}
	  ]

****************************
POST /v1/calc/:calc_id/abort
****************************

Abort the given ``calc_id`` by sending to the corresponding job a SIGTERM.

Parameters: None

Response::

	{'error': 'Job <id> is not running'}
	{'error': 'User <user> has no permission to kill job <id>'}
	{'error': 'PID for job <id> not found in the database'}
	{'success': 'Killing job <id>'}

****************************
GET /v1/calc/:calc_id/status
****************************

Return the calculation status (the same content of ``/v1/calc/list``) for the given ``calc_id``.

Parameters: None

Response::

	{"description": "Hazard Calculation for end-to-end hazard+risk",
	  "id": 1,
	  "status": "executing",
	  "calculation_mode": "classical",
	  "is_running": true,
	  "owner: "michele",
	  "parent_id": "42",
	  "url": "http://localhost:8800/v1/calc/1"}

*********************
GET /v1/calc/:calc_id
*********************

Get calculation status and times for the given ``calc_id``.

Parameters: None

Response::

	{"user_name": "michele",
	"is_running": 0,
	"stop_time": "2017-06-05 12:01:28.575776",
	"status": "failed",
	"start_time": "2017-06-05 12:01:26"}

*******************************
GET /v1/calc/:calc_id/traceback
*******************************

Get the calculation traceback for the given ``calc_id`` as a list of strings.

Parameters: None

Response:

A list of error lines extracted from the log. If the calculation was successfull, the list is empty.

***********************************
GET /v1/calc/:calc_id/extract/:spec
***********************************

Get an .npz file for the given object specification. If ``spec`` ends with the extension ``.attrs`` the attributes of the 
underlying object (usually coming from an HDF5 dataset) are used to build the .npz file, while the object itself is not 
retrieved.

Response:

A single .npz file of Content-Type: application/octet-stream

*****************************
GET /v1/calc/:calc_id/results
*****************************

List a summary of results for the given ``calc_id``. The url in each response item can be followed to retrieve the full 
result artifact.

Parameters: None

Response::

	   [{'id': 27,
	     'name': 'Full Report',
	     'outtypes': ['rst'],
	     'size_mb': None,
	     'type': 'fullreport',
	     'url': 'http://127.0.0.1:8800/v1/calc/result/27'},
	    {'id': 28,
	     'name': 'Ground Motion Fields',
	     'outtypes': ['xml', 'csv', 'npz'],
	     'size_mb': 0.00884246826171875,
	     'type': 'gmf_data',
	     'url': 'http://127.0.0.1:8800/v1/calc/result/28'},
	    {'id': 29,
	     'name': 'Hazard Curves',
	     'outtypes': ['csv', 'xml', 'npz'],
	     'size_mb': 0.027740478515625,
	     'type': 'hcurves',
	     'url': 'http://127.0.0.1:8800/v1/calc/result/29'},
	    {'id': 30,
	     'name': 'Earthquake Ruptures',
	     'outtypes': ['xml', 'csv'],
	     'size_mb': 0.008056640625,
	     'type': 'ruptures',
	     'url': 'http://127.0.0.1:8800/v1/calc/result/30'},
	    {'id': 31,
	     'name': 'Events',
	     'outtypes': ['csv'],
	     'size_mb': None,
	     'type': 'events',
	     'url': 'http://127.0.0.1:8800/v1/calc/result/31'}]

*********************************
GET /v1/calc/:calc_id/result/list
*********************************

Same as GET /v1/calc/:calc_id/results

******************************
GET /v1/calc/result/:result_id
******************************

Get the full content of a calculation result for the given ``result_id``.

Parameters::

	* export_type: the desired format for the result (`xml`, `geojson`, etc.)
	* dload: `true` to force download, not `true` try to open in browser window

Response:

The requested result as a blob of text. If the desired ``export_type`` is not supported, an HTTP 404 error is returned.

******************************************
GET /v1/calc/:calc_id/log/[:start]:[:stop]
******************************************

Get a slice of the calculation log for the given ``calc_id``, from ``start`` to ``stop``. If start is the empty string, 
consider it ``0`` and starts from the beginning. If ``stop`` is the empty string, gives all the available lines. For 
instance ``http://host/v1/calc/123/log/:`` gives the complete log for calculation 123.

Parameters: None

Response:

The requested log slice as a JSON list of rows

******************************
GET /v1/calc/:calc_id/log/size
******************************

Get the (current) number of lines of the calculation log for the given ``calc_id``.

Parameters: None

Response:

The number of lines of log

******************************
GET v1/calc/:calc_id/datastore
******************************

Get the HDF5 datastore for the calculation identified by the parameter ``calc_id``.

*****************************
POST /v1/calc/:calc_id/remove
*****************************

Remove the calculation specified by the parameter ``calc_id``.

*****************
POST /v1/calc/run
*****************

Run a new calculation with the specified job config file, input models, and other parameters.

Files::

	* job_config: an oq engine job config INI-style file
	* input_model_1 - input_model_N: any number (including zero) of input model files

Parameters::

	* hazard_job_id: the hazard calculation ID upon which to run the risk calculation; specify this or hazard_result (only for risk calculations)
	* hazard_result: the hazard results ID upon which to run the risk calculation; specify this or hazard_job_id (only for risk calculations)

Response: Redirects to /v1/calc/:calc_id, where ``calc_id`` is the ID of the newly created calculation.

**********************
POST /v1/calc/aelo_run
**********************

Run a new aelo calculation for a site with the specified parameters.

Parameters::

	* lon: the longitude of the site (a float in the interval [-180, +180])
	* lat: the latitude of the site (a float in the interval [-90.0, +90.0])
	* vs30: the time-averaged shear-wave velocity from the surface to a depth of 30 meters (a positive float)
	* siteid: an ID to assign to the site (the only accepted chars are a-zA-Z0-9_-:)

Response::

	The input values are validated and a `400 Bad Request` response is returned
	in case any invalid input is found, specifying the reason of the failure.
	If inputs are valid, the engine will first attempt to identify a Mosaic
	model that covers the given site, returning a `400 Bad Request` response in
	case the site does not belong to any of the Mosaic models. Otherwise, a new
	job is created and a `200 OK` response is returned, like:
	
	{"status": "created",
	 "job_id": 1,
	 "outputs_uri": "http://localhost:8800/v1/calc/1/results",
	 "log_uri": "http://localhost:8800/v1/calc/1/log/0:",
	 "traceback_uri": "http://localhost:8800/v1/calc/1/traceback"}
	
	`outputs_uri` can be used later to retrieve calculation results, after the job is complete.
	`log_uri` can be called to get the log of the calculation, either while it is still running or after its completion.
	`traceback_uri` can be called in case of job failure (and only after it occurs), to retrieve a full traceback of the error.

As soon as the job is complete, a notification is automatically sent via email to the user who launched it. In case of 
success, the message will contain a link to the web page showing the outputs of the calculation; otherwise, it will 
describe the error that occurred.

**************************
POST /v1/calc/validate_zip
**************************

Check if a given job.zip archive is valid

Parameters::

	* archive: the zip file to be validated

Response:

a JSON object, containing::

	* valid: a boolean indicating if the provided archive is a valid job.zip
	* error_msg: the error message, if any error was found (None otherwise)

***************
POST /v1/valid/
***************

Check if a given XML text is a valid NRML.

Parameters::

	* xml_text: the text of the xml to be validated as nrml

Response:

a JSON object, containing::

	* valid: a boolean indicating if the provided text is a valid NRML
	* error_msg: the error message, if any error was found (None otherwise)
	* error_line: line of the given XML where the error was found (None if no error was found or if it was not a validation error)

*******************
POST /v1/on_same_fs
*******************

Check if a given filename exists and if the first 32 bytes of its content have the same checksum passed as argument of POST.

*(developed for internal purposes)*

Parameters::

	* filename: filename (with path) of file to be checked
	* checksum: expected checksum of first 32 bytes of the file

Response:

a JSON object, containing::

	* success: a boolean indicating that filename is accessible by engine server and that calculated checksum matches passed parameter

********************
GET /v1/ini_defaults
********************

Retrieve all default values for ini file parameters (parameters without a default value are not returned).

*(developed for internal purposes)*

Parameters: None

Response::

	{"aggregate_by": [],
	 "area_source_discretization": null,
	 "ash_wet_amplification_factor": 1.0,
	 "asset_correlation": 0,
	 "asset_hazard_distance": {"default": 15},
	 "asset_loss_table": false,
	 "assets_per_site_limit": 1000,
	 "avg_losses": true,
	 "base_path": ".",
	 "calculation_mode": "",
	 ...
	 }

**************************
POST /accounts/ajax_login/
**************************

Attempt to login, given the parameters ``username`` and ``password``.


***************************
POST /accounts/ajax_logout/
***************************

Logout

********************
GET /reset_password/
********************

The user is asked to submit a web form with the email address associated to his/her Django account. Then a "Reset 
Password" email is sent to the user. By clicking on the link received via email, the user is redirected to a web form to 
specify a new password.

**********************
GET /v1/engine_version
**********************

Return a string with the OpenQuake engine version

*****************************
GET /v1/engine_latest_version
*****************************

Return a string with if new versions have been released. Return 'None' if the version is not available

***********************
GET /v1/available_gsims
***********************

Return a list of strings with the available GSIMs

Extracting data from calculations
---------------------------------

The engine has a relatively large set of predefined outputs, that you can get in various formats, like CSV, XML or HDF5. 
They are all documented in the manual and they are the recommended way of interacting with the engine, if you are not 
tech-savvy.

However, sometimes you must be tech-savvy: for instance if you want to post-process hundreds of GB of ground motion 
fields produced by an event based calculation, you should not use the CSV output, at least if you care about efficiency. 
To manage this case (huge amounts of data) there is a specific solution, which is also able to manage the case of data 
lacking a predefined exporter: the ``Extractor`` API.

There are actually two different kind of extractors: the simple ``Extractor``, which is meant to manage large data sets 
(say > 100 MB) and the ``WebExtractor``, which is able to interact with the WebAPI and to extract data from a remote machine. 
The WebExtractor is nice, but cannot be used for large amount of data for various reasons; in particular, unless your 
Internet connection is ultra-fast, downloading GBs of data will probably send the web request in timeout, causing it to 
fail. Even if there is no timeout, the WebAPI will block, everything will be slow, the memory occupation and disk space 
will go up, and at certain moment something will fail.

The ``WebExtractor`` is meant for small to medium outputs, things like the mean hazard maps - an hazard map containing 
100,000 points and 3 PoEs requires only 1.1 MB of data at 4 bytes per point. Mean hazard curves or mean average losses 
in risk calculation are still small enough for the ``WebExtractor``. But if you want to extract all of the realizations you 
must go with the simple ``Extractor``: in that case your postprocessing script must run in the remote machine, since it 
requires direct access to the datastore.

Here is an example of usage of the ``Extractor`` to retrieve mean hazard curves::

	>> from openquake.calculators.extract import Extractor
	>> calc_id = 42  # for example
	>> extractor = Extractor(calc_id)
	>> obj = extractor.get('hcurves?kind=mean&imt=PGA')  # returns an ArrayWrapper
	>> obj.mean.shape  # an example with 10,000 sites, 20 levels per PGA
	(10000, 1, 20)
	>> extractor.close()

If in the calculation you specified the flag ``individual_rlzs=true``, then it is also possible to retrieve a specific 
realization

	>> dic = vars(extractor.get(‘hcurves?kind=rlz-0’)) >> dic[‘rlz-000’] # array of shape (num_sites, num_imts, num_levels)

or even all realizations:

	>> dic = vars(extractor.get(‘hcurves?kind=rlzs’))

Here is an example of using the *WebExtractor* to retrieve hazard maps. Here we assume that in a remote machine there is 
a WebAPI server running, a.k.a. the Engine Server. The first thing to is to set up the credentials to access the WebAPI. 
There are two cases:

1. you have a production installation of the engine in ``/opt``
2. you have a development installation of the engine in a virtualenv

In both case you need to create a file called ``openquake.cfg`` with the following format::

	[webapi]
	server = http(s)://the-url-of-the-server(:port)
	username = my-username
	password = my-password

``username`` and ``password`` can be left empty if the authentication is not enabled in the server, which is the 
recommended way, if the server is in your own secure LAN. Otherwise you must set the right credentials. The difference 
between case 1 and case 2 is in where to put the ``openquake.cfg`` file: if you have a production installation, put it in 
your $HOME, if you have a development installation, put it in your virtualenv directory.

The usage then is the same as the regular extractor::

	>> from openquake.calculators.extract import WebExtractor
	>> extractor = WebExtractor(calc_id)
	>> obj = extractor.get('hmaps?kind=mean&imt=PGA')  # returns an ArrayWrapper
	>> obj.mean.shape  # an example with 10,000 sites and 4 PoEs
	(10000, 1, 4)
	>> extractor.close()

If you do not want to put your credentials in the ``openquake.cfg`` file, you can do so, but then you need to pass them 
explicitly to the WebExtractor::

	>> extractor = WebExtractor(calc_id, server, username, password)

********
Plotting
********

The (Web)Extractor is used in the oq plot command: by configuring ``openquake.cfg`` it is possible to plot things like 
hazard curves, hazard maps and uniform hazard spectra for remote (or local) calculations. Here are three examples of use::

	$ oq plot 'hcurves?kind=mean&imt=PGA&site_id=0' <calc_id>
	$ oq plot 'hmaps?kind=mean&imt=PGA' <calc_id>
	$ oq plot 'uhs?kind=mean&site_id=0' <calc_id>

The ``site_id`` is optional; if missing, only the first site (``site_id=0``) will be plotted. If you want to plot all 
the realizations you can do::

	$ oq plot 'hcurves?kind=rlzs&imt=PGA' <calc_id>

If you want to plot all statistics you can do::

	$ oq plot 'hcurves?kind=stats&imt=PGA' <calc_id>

It is also possible to combine plots. For instance if you want to plot all realizations and also the mean the command to 
give is::

	$ oq plot 'hcurves?kind=rlzs&kind=mean&imt=PGA' <calc_id>

If you want to plot the median and the mean the command is::

	$ oq plot 'hcurves?kind=quantile-0.5&kind=mean&imt=PGA' <calc_id>

assuming the median (i.e. *quantile-0.5*) is available in the calculation. If you want to compare say rlz-0 with rlz-2 
and rlz-5 you can just just say so::

	$ oq plot 'hcurves?kind=rlz-0&kind=rlz-2&kind=rlz-5&imt=PGA' <calc_id>

You can combine as many kinds of curves as you want. Clearly if your are specifying a kind that is not available you 
will get an error.

*********************************
Extracting disaggregation outputs
*********************************

Disaggregation outputs are particularly complex and they are stored in the datastore in different ways depending on the 
engine version. Here we will give a few examples for the Disaggregation Demo, which has the flag individual_rlzs set. 
If you run the demos with a recent enough version of the engine (>=3.17) you will see two disaggregation outputs:

1. Disaggregation Outputs Per Realization
2. Statistical Disaggregation Outputs

Such outputs can be exported as usual in CSV format and will generate several files. Users can be interested in 
extracting a subset of the outputs programmatically, thus avoiding the overhead of exporting more data than needed and 
having to read the CSV. The way to go is to define an extractor::

	>> extractor = Extractor(calc_id)

and five parameters:

1. kind: the kind of outputs, like Mag, Mag_Dist, Mag_Dist_Eps, etc
2. imt: the IMT, like PGA, SA(1.0), etc
3. site_id: the site ordinal number, like 0, 1, etc
4. poe_id: the ordinal of the PoE, like 0, 1, etc
5. spec: the specifier string, one of “rlzs”, “stats”, “rlzs-traditional”, “stats-traditional”

Here is an example::

	>> ex = 'disagg?kind=Mag_Dist&imt=PGA&site_id=0&poe_id=0&spec=rlzs-traditional'
	>> dic = extractor.get(ex)

The dictionary here contains the following keys::

	>> dic["mag"] # lenght 4
	array([5., 6., 7., 8.])
	>> dic["dist"] # lenght 21
	array([  0.,  10.,  20.,  30.,  40.,  50.,  60.,  70.,  80.,  90., 100.,
	       110., 120., 130., 140., 150., 160., 170., 180., 190., 200.])
	>> dic["array"].shape
	(4, 21, 1, 1)

*******************
Extracting ruptures
*******************

Here is an example for the event based demo::

	$ cd oq-engine/demos/hazard/EventBasedPSHA/
	$ oq engine --run job.ini
	$ oq shell
	IPython shell with a global object "o"
	In [1]: from openquake.calculators.extract import Extractor
	In [2]: extractor = Extractor(calc_id=-1)
	In [3]: aw = extractor.get('rupture_info?min_mag=5')
	In [4]: aw
	Out[4]: <ArrayWrapper(1511,)>
	In [5]: aw.array
	Out[5]:
	array([(   0, 1, 5.05, 0.08456118,  0.15503392, 5., b'Active Shallow Crust', 0.0000000e+00, 90.      , 0.),
	       (   1, 1, 5.05, 0.08456119,  0.15503392, 5., b'Active Shallow Crust', 4.4999969e+01, 90.      , 0.),
	       (   2, 1, 5.05, 0.08456118,  0.15503392, 5., b'Active Shallow Crust', 3.5999997e+02, 49.999985, 0.),
	       ...,
	       (1508, 2, 6.15, 0.26448786, -0.7442877 , 5., b'Active Shallow Crust', 0.0000000e+00, 90.      , 0.),
	       (1509, 1, 6.15, 0.26448786, -0.74428767, 5., b'Active Shallow Crust', 2.2499924e+02, 50.000004, 0.),
	       (1510, 1, 6.85, 0.26448786, -0.74428767, 5., b'Active Shallow Crust', 4.9094699e-04, 50.000046, 0.)],
	      dtype=[('rup_id', '<i8'), ('multiplicity', '<u2'), ('mag', '<f4'), ('centroid_lon', '<f4'),
	             ('centroid_lat', '<f4'), ('centroid_depth', '<f4'), ('trt', 'S50'), ('strike', '<f4'),
	             ('dip', '<f4'), ('rake', '<f4')])
	In [6]: extractor.close()

Reading outputs with pandas
---------------------------

If you are a scientist familiar with Pandas, you will be happy to know that it is possible to process the engine outputs 
with it. Here we will give an example involving hazard curves.

Suppose you ran the AreaSourceClassicalPSHA demo, with calculation ID=42; then you can process the hazard curves as 
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

***************************************
Example: how many events per magnitude?
***************************************

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