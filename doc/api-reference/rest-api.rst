.. _rest-api:

OpenQuake Engine Server REST API
================================

Introduction
------------

oq engine server provides a series of REST API methods for running calculations, checking calculation status, and
browsing and downloading results.

All responses are JSON, unless otherwise noted. Binary endpoints
return the corresponding file or image content type.

Authentication
--------------

The public calculation and export endpoints are unauthenticated in
``PUBLIC`` mode. In modes with ``LOCKDOWN`` enabled (``RESTRICTED``,
``AELO``, and ``IMPACT``), those endpoints require a Django session;
the session can be created through ``POST /accounts/ajax_login/``.
Check ``GET /v1/authentication/status`` before attempting to log in.

Some routes use the internal API key independently of Django login. The
key is the ``authkey`` from the ``[dbserver]`` section of
``openquake.cfg`` and must be sent in the ``X-API-Key`` request header:

.. code-block:: console

    X-API-Key: <dbserver-authkey>

This applies to ``/v1/calc_info/:calc_id``,
``/v1/calc_list/count``, and ``/v1/on_same_fs``. ``/v1/ping`` does
not require authentication. The key is also required by every DbServer
route; see :ref:`dbserver-api`.

Application modes
-----------------

Routes are registered according to the Django ``APPLICATION_MODE``:

- ``PUBLIC`` and ``RESTRICTED`` register the generic calculation routes,
  including ``/v1/calc/run``, ``/v1/calc/run_ini``,
  ``/v1/calc/validate_ini``, ``/v1/calc/validate_zip``,
  ``/v1/calc/:calc_id/abort`` and ``/v1/calc/:calc_id/remove``;
- ``READ_ONLY`` does not register those six routes, but it keeps the
  sharing and tagging routes and the PAPERS route
  ``/v1/calc/run_scenario_calc_from_ses_rupture/:rup_id``;
- ``AELO`` and ``IMPACT`` keep only ``abort`` and ``remove`` among those
  six routes and add their own routes (``/v1/calc/aelo_run`` and the
  IMPACT routes respectively);
- ``TOOLS_ONLY`` exposes only ``/v1/valid/``, ``/v1/available_gsims``,
  ``/v1/ini_defaults`` and ``/v1/ping``.

A route omitted for the current mode returns HTTP 404.

*****************
GET /v1/calc/list
*****************

List the available calculations. The url in each item of the response can be
followed to retrieve complete calculation details.

Parameters: all are optional query-string filters:

- ``calculation_mode``: calculation mode, e.g. ``classical``
- ``is_running``: boolean; return only running or non-running jobs
- ``user_name_like``: case-insensitive owner-name pattern
- ``start_time``: ISO timestamp; jobs started at or after this value
- ``include_shared``: boolean, default true; include shared jobs
- ``relevant_only``: boolean; return only relevant jobs
- ``preferred_only``: boolean; return only preferred tagged jobs
- ``filter_by_tag``: tag name; return jobs associated with that tag
- ``limit``: maximum number of rows, default 100; use -1 for no limit
- ``offset``: row offset, default 0
- ``order_by``: one of ``id``, ``start_time``, ``user_name``,
  ``calculation_mode``, ``status``, ``description``, or ``size_mb``
- ``order_dir``: ``ASC`` or ``DESC``, default ``DESC``

Response::

	[{"description": "Hazard Calculation for end-to-end hazard+risk",
	  "id": 1,
	  "status": "executing",
	  "calculation_mode": "classical",
	  "is_running": true,
	  "owner": "michele",
	  "url": "http://localhost:8800/v1/calc/1",
	  "abortable": true,
	  "size_mb": 2.34,
	  "can_manage_sharing": true,
	  "parent_id": null,
	  "start_time": "2026-01-01, 12:00:00 UTC",
	  "relevant": 1,
	  "tags": null
	 }, ...]

The ``tags`` value is ``null`` for a job without tags, otherwise a
comma-separated string; a preferred job tag is suffixed with ``★``.

***********************
GET /v1/calc/list/count
***********************

Count the calculations visible to the current user and matching the same
filters as ``GET /v1/calc/list``; it returns a JSON number. This is an
ordinary session route: the route protected by ``X-API-Key`` is
``GET /v1/calc_list/count``.

****************************
POST /v1/calc/:calc_id/abort
****************************

Abort the given ``calc_id`` by sending SIGINT to its worker.

Parameters: None

Response::

	{'error': 'Unknown job <id>'}
	{'error': 'Job <id> is not running'}
	{'error': 'User <user> has no permission to abort job <id>'}
	{'error': 'PID for job <id> not found'}
	{'error': 'Unable to abort job <id>: <reason>'}
	{'success': 'Killing job <id>'}

The permission error is returned with HTTP 403, the other responses with
HTTP 200.

*****************************
POST /v1/calc/:calc_id/remove
*****************************

Remove the calculation and, when possible, its HDF5 datastore files.
The authenticated user must own the job. The response contains either
``success`` or ``error``.

****************************
GET /v1/calc/:calc_id/status
****************************

Return the same calculation-list item described above for ``calc_id``.

Parameters: None

Response::

	{"description": "Hazard Calculation for end-to-end hazard+risk",
	 "id": 1,
	 "status": "executing",
	 "calculation_mode": "classical",
	 "is_running": true,
	 "owner": "michele",
	 "parent_id": null,
	 "url": "http://localhost:8800/v1/calc/1",
	 "abortable": true,
	 "size_mb": 2.34,
	 "can_manage_sharing": true,
	 "start_time": "2026-01-01, 12:00:00 UTC",
	 "relevant": 1,
	 "tags": null}

*********************
GET /v1/calc/:calc_id
*********************

Get the fields of the job record of the given ``calc_id``, except
``ds_calc_dir`` and ``pid``; the times are returned as strings.

Parameters: None

Response::

	{"id": 1,
	 "description": "Classical PSHA",
	 "user_name": "michele",
	 "calculation_mode": "classical",
	 "hazard_calculation_id": null,
	 "status": "complete",
	 "is_running": 0,
	 "start_time": "2026-01-01 12:00:00",
	 "stop_time": "2026-01-01 12:01:28.575776",
	 "relevant": 1,
	 "size_mb": 2.34,
	 "host": null,
	 "workflow_id": null}

**************************************
GET /v1/calc/:calc_id/model_provenance
**************************************

Get the repository provenance snapshot stored in the calculation datastore.
The snapshot identifies the regional model repositories, their submodules,
``site-models``, commit hashes, branch or detached-head state, and whether the
working tree was dirty when the exposure HDF5 was built.

Parameters: None

Response when provenance is available::

	{"available": true,
	 "summary": {
	   "schema_version": 1,
	   "generated_at": "2026-06-25T14:32:10+00:00",
	   "repositories": []
	 }}

For old datastores without provenance metadata, the endpoint returns::

	{"available": false,
	 "reason": "Model provenance metadata is not available"}

*******************************
GET /v1/calc/:calc_id/traceback
*******************************

Get the calculation traceback for the given ``calc_id`` as a list of strings.

Parameters: None

Response:

A list of error lines extracted from the log. If the calculation was successful,
the list is empty.

****************************************
GET /v1/calc/:calc_id/download_png/:name
****************************************

Download a PNG stored in the datastore under ``png/:name``. The name may
contain letters, digits and the characters ``/``, ``.``, ``-``, ``_``,
``(`` and ``)``; other characters, such as ``=``, are not accepted, even
if URL-escaped. Returns HTTP 404 when the job does not exist, HTTP 403
when the user lacks permission and HTTP 500, with the traceback as text,
when the image does not exist.

****************************
POST /v1/calc/:calc_id/share
****************************

Make a completed calculation visible to all users by changing its status
to ``shared``. Requires user level at least 2, superuser status, or the
``auth.can_share_own_jobs`` permission.

******************************
POST /v1/calc/:calc_id/unshare
******************************

Revert a shared calculation to status ``complete``. The same sharing
permissions and status restrictions apply.

**********************
GET /v1/calc/list_tags
**********************

List all available tags. Response::

	{"success": "ok", "tags": ["tag-a", "tag-b"]}

*********************************
GET /v1/calc/create_tag/:tag_name
*********************************

Create a tag. Requires user level at least 2.

*********************************
GET /v1/calc/delete_tag/:tag_name
*********************************

Delete a tag. Requires user level at least 2.

***************************************
GET /v1/calc/:calc_id/add_tag/:tag_name
***************************************

Add an existing or new tag to a calculation. Requires user level at least 2.
The tag endpoints are registered as GET in this version.

******************************************
GET /v1/calc/:calc_id/remove_tag/:tag_name
******************************************

Remove a tag from a calculation. Requires user level at least 2.

*********************************************************
GET /v1/calc/:calc_id/set_preferred_job_for_tag/:tag_name
*********************************************************

Mark the calculation as the preferred job for the tag and clear the
preference on any previous job with that tag.

**************************************************
GET /v1/calc/unset_preferred_job_for_tag/:tag_name
**************************************************

Clear the preferred job for a tag.

************************************************
GET /v1/calc/get_preferred_job_for_tag/:tag_name
************************************************

Return ``{"success": "ok", "job_id": <id-or-null>}`` for a tag.

****************************
GET /v1/calc/:calc_id/impact
****************************

IMPACT mode only. Get impact results aggregated by tag, together with the
corresponding exposure values.

NB: this URL is valid only for risk calculations with an ``aggregate_by``
parameter. Otherwise it returns a ``BadRequest`` error with HTTP code 400.

Parameters: None

Response:

A JSON object containing:

- an ``impact`` key containing a pandas DataFrame; the names of the columns
  are ``ID_2``, ``loss_type``, ``value``, ``lossmea``, ``lossq05``, and
  ``lossq95``.
- a ``loss_type_description`` dictionary containing a description for each
  loss type.

*************************************
GET /v1/calc/:calc_id/exposure_by_mmi
*************************************

IMPACT mode only. Get exposure aggregated by MMI regions and tags.

NB: this URL is valid only for ShakeMap-based calculations downloading the
MMI regions from the USGS service. Otherwise it returns HTTP 400.

Response:

A JSON object with ``exposure_by_mmi`` (a pandas DataFrame) and
``column_descriptions``.

*************************************
GET /v1/calc/:calc_id/exposure_by_lse
*************************************

IMPACT mode only. Get exposure aggregated by secondary-peril LSE tiers
and tags.

Parameters:

- ``secondary_peril`` (string, required): exactly ``liquefaction`` or
  ``landslide``.
- ``discard_empty`` (boolean/integer, optional): pass 0 to keep empty bins;
  defaults to 1 (discard empty bins).

Response:

A JSON object with ``exposure_by_lse`` (a pandas DataFrame) and
``column_descriptions``. Invalid input returns HTTP 400; a missing job or
result returns HTTP 404; insufficient permission returns HTTP 403.

**************************************
GET /v1/calc/:calc_id/impact_resources
**************************************

IMPACT mode only. Describe available IMPACT plots, tables, reports, and
their retrieval URLs. Response keys include ``avg_gmf_plots``,
``assets``, ``aggrisk``, ``aggrisk_tags``, ``exposure_by_mmi``,
``exposure_by_lse``, and ``country_reports``.

**************************************
GET /v1/calc/:calc_id/download_aggrisk
**************************************

IMPACT mode only. Download aggregated risk CSV data for a calculation.

**********************************************
GET /v1/calc/:calc_id/extract_html_table/:name
**********************************************

IMPACT mode only. Extract an HTML table from the calculation datastore.
``name`` may be ``aggrisk_tags``, ``mmi_tags``, ``exposure_by_location``,
``exposure_by_lse?secondary_peril=liquefaction``, or
``exposure_by_lse?secondary_peril=landslide``. The optional
``summarize=1`` query parameter requests a summary table where supported.

***********************************
GET /v1/calc/:calc_id/impact_report
***********************************

IMPACT mode only. Return a country report embedded in the datastore.

Parameters:

- ``iso3`` (required): ISO3 country code.
- ``format``: ``pdf`` (default) or ``png``.
- ``page``: positive page number for PNG reports; defaults to 1.

Returns ``application/pdf`` or ``image/png`` inline. Invalid parameters or
missing report pages return HTTP 400.

***********************************
GET /v1/calc/:calc_id/extract/:spec
***********************************

Get an ``.npz`` file for the given object specification. If ``spec`` ends with
``.attrs`` the attributes of the underlying object (usually coming from an
HDF5 dataset) are used to build the ``.npz`` file, while the object itself is
not retrieved.

Response:

A single ``.npz`` file of Content-Type: application/octet-stream

*****************************
GET /v1/calc/:calc_id/results
*****************************

List a summary of results for the given ``calc_id``. The ``url`` in each
response item already includes the default ``export_type`` query parameter
and can be followed to retrieve the result artifact.

Parameters: None

Response::

	[{'id': 27,
	  'name': 'Full Report',
	  'outtypes': ['rst'],
	  'size_mb': None,
	  'type': 'fullreport',
	  'url': 'http://127.0.0.1:8800/v1/calc/result/27?export_type=rst'},
	 ...]

*********************************
GET /v1/calc/:calc_id/result/list
*********************************

Same as ``GET /v1/calc/:calc_id/results``.

******************************
GET /v1/calc/result/:result_id
******************************

Get the full content of a calculation result for the given ``result_id``.

Parameters::

	* export_type: the desired format, such as xml, csv or npz (default xml)

Response:

The requested result as a file, always sent as an attachment. If the
desired ``export_type`` is not
supported, HTTP 404 is returned. Export failures return HTTP 500.

******************************************
GET /v1/calc/:calc_id/log/[:start]:[:stop]
******************************************

Get a slice of the calculation log from ``start`` to ``stop``. An empty
``start`` means 0; an empty ``stop`` means all available lines. For instance
``http://host/v1/calc/123/log/0:`` gives the complete log for job 123.

Response:

The requested log slice as a JSON list of rows, where each row is
``[timestamp, level, process, message]``.

******************************
GET /v1/calc/:calc_id/log/size
******************************

Get the current number of lines of the calculation log as a JSON number.

*******************************
GET /v1/calc/:calc_id/datastore
*******************************

Download the HDF5 datastore for ``calc_id``. In modes with lockdown, user
level at least 2 or ``ALLOW_DATASTORE_DOWNLOAD = True`` is required;
IMPACT mode disables datastore downloads by default.

*****************************
GET /v1/calc/:calc_id/job_zip
*****************************

Download the input files for ``calc_id`` as ``job_<id>.zip``. Requires user
level at least 2.

*****************
POST /v1/calc/run
*****************

Run a new calculation with uploaded files (or a single ``job.zip``).

Parameters::

	* archive: the uploaded files, either a job.zip or the individual input
	  files, all sent in this field (repeat it for several files)
	* job_ini: text field with the name (or suffix) of the job file to use
	  among the uploaded files, default .ini (risk.ini when hazard_job_id
	  is given); if no file is uploaded, the path of a job.ini on the server
	* hazard_job_id: hazard calculation ID reused by a risk calculation
	* notify_to: optional HTTP(S) completion callback URL; the request must
	  be authenticated as the owner or as a superuser
	* job_owner: owner override, honored only for a superuser

Response: HTTP 200 with the new job information, including ``job_id`` and
``user_name``. Submission failures return HTTP 500 with a ``traceback`` and,
when available, ``job_id``; job-time failures are reported by the job status
and traceback endpoints.

*********************
POST /v1/calc/run_ini
*********************

Run a new calculation using an existing server-side ``job.ini``.

Parameters::

	* job_ini: full path to the job.ini file on the server
	* hazard_job_id: optional hazard calculation ID
	* notify_to: optional HTTP(S) completion callback URL; the request must
	  be authenticated as the owner or as a superuser
	* job_owner: owner override, honored only for a superuser

Response: HTTP 200 with the new job information, including ``job_id``.
Submission failures return HTTP 500 with a ``traceback`` and, when
available, ``job_id``.

**********************
POST /v1/calc/aelo_run
**********************

AELO mode only. Run a new AELO calculation.

Parameters::

	* lon: longitude in [-180, +180]
	* lat: latitude in [-90, +90]
	* vs30: shear-wave velocity in m/s; several values can be given,
	  separated by spaces
	* site_name: non-empty site name
	* asce_version: optional ASCE standard version (with a default)
	* site_class: site class, or custom; unless it is custom, vs30 must be
	  the value expected for the site class

Response::

	{"status": "created",
	 "job_id": 1,
	 "outputs_uri": "http://localhost:8800/v1/calc/1/results",
	 "log_uri": "http://localhost:8800/v1/calc/1/log/0:",
	 "traceback_uri": "http://localhost:8800/v1/calc/1/traceback"}

When the user has no email address the response also contains a
``WARNING`` key. Invalid input or an uncovered site returns HTTP 400 with
``error_msg`` and, for form validation, ``invalid_inputs``.

************************
POST /v1/calc/impact_run
************************

IMPACT mode only. Run a new IMPACT calculation. The form fields include the
rupture/ShakeMap parameters accepted by ``impact_validate``, station data,
calculation options, ``notify_to``, and related fields described by
``GET /v1/get_impact_form_defaults``. User level 0 is forbidden.

A successful response maps the job ID to an object containing ``status``,
``job_id``, ``outputs_uri_web``, ``outputs_uri``, ``log_uri``,
``traceback_uri`` and, when the user has no email address, ``WARNING``::

	{"1": {"status": "created", "job_id": 1, ...}}

Invalid input returns HTTP 400; invalid non-form input or
internal validation failures return HTTP 500.

*************************************
POST /v1/calc/impact_get_rupture_data
*************************************

IMPACT mode only. Build rupture data for the IMPACT form from a USGS ID or
uploaded rupture file. It accepts the rupture parameters used by
``impact_validate``, plus ``rupture_file``, ``user_level``, and optional
ShakeMap/station fields. The response includes rupture parameters and any
rendered rupture/ShakeMap PNG data.

**************************************
POST /v1/calc/impact_run_with_shakemap
**************************************

IMPACT mode only. Run an IMPACT calculation using a USGS ShakeMap selected
by ``usgs_id`` and optional ``shakemap_version``. Optional parameters include
``time_event``, ``maximum_distance``, report options, and form defaults.
User level 0 is forbidden.

**************************
POST /v1/calc/validate_ini
**************************

Check if a given job.ini is valid.

Parameters::

	* job_ini: uploaded file, or server-side path in the form field

Response: a JSON object containing ``valid`` and ``error_msg``.

**************************
POST /v1/calc/validate_zip
**************************

Check if a given job.zip archive is valid.

Parameters::

	* archive: the zip file to be validated

Response: a JSON object containing ``valid`` and ``error_msg``.

********************************************************
POST /v1/calc/run_scenario_calc_from_ses_rupture/:rup_id
********************************************************

PAPERS entry point: run a scenario calculation from the SES rupture ID.
The owner is the logged-in user (a superuser can set ``job_owner``); the
optional ``notify_to`` field is a completion callback and the other form
fields are passed to the PAPERS job context. Returns the new job
information, including ``job_id``.

***************
POST /v1/valid/
***************

Check if a given XML text is valid NRML.

Parameters::

	* xml_text: the text of the XML to be validated as NRML

Response: a JSON object with ``valid``, ``error_msg``, and ``error_line``.
Missing ``xml_text`` returns HTTP 400.

*******************
POST /v1/on_same_fs
*******************

Check whether a server-side filename exists and whether the first 32 bytes
match a supplied Adler-32 checksum. This internal route requires
``X-API-Key``.

Parameters::

	* filename: filename with path on the server
	* checksum: expected unsigned 32-bit checksum

Response::

	{"success": true}

A missing file, unreadable file, or checksum mismatch returns
``{"success": false}`` with HTTP 200. A missing or invalid API key returns
HTTP 403.

********************
GET /v1/ini_defaults
********************

Retrieve all default values for INI parameters. Parameters without a default
value are omitted.

Parameters: None

*****************************
GET /v1/authentication/status
*****************************

Return whether Django login is required::

	{"authentication_required": true}

**************************
GET /v1/calc_info/:calc_id
**************************

Internal route protected by ``X-API-Key``. Return the calculation-info
object for ``calc_id`` (the same data returned by ``GET /v1/calc/:calc_id``).

***********************
GET /v1/calc_list/count
***********************

Internal route protected by ``X-API-Key``. Count calculations matching
the same filters as ``GET /v1/calc/list``. The optional ``X-Valid-Users``
header is a JSON array of valid users and ``X-User-ACL-On`` controls ACL
filtering.

*************************
GET /v1/aelo_site_classes
*************************

Return the ASCE site-class definitions as a JSON object. The route is
served in all modes except ``TOOLS_ONLY`` and does not require login.

**********************
GET /v1/engine_version
**********************

Return the OpenQuake engine version as a text response.

*****************************
GET /v1/engine_latest_version
*****************************

Return a text message if a newer version of the engine has been
released, an empty body if the engine is up to date, and ``None`` when
the check could not be performed.

***********************
GET /v1/available_gsims
***********************

Return a JSON list of available GSIM names.

***************************
GET /v1/calc/jobs_from_inis
***************************

Given repeated ``ini`` query parameters containing server-side INI paths,
return a JSON object mapping each path to its existing calculation ID, or 0
if no matching calculation exists. A read/validation error returns HTTP 500
with an ``error`` field.

********************************
GET /v1/get_impact_form_defaults
********************************

Return the IMPACT form field defaults as a JSON object. The route is
served in all modes except ``TOOLS_ONLY`` and does not require login.

**************************************
POST /v1/impact_get_stations_from_usgs
**************************************

IMPACT mode only. Retrieve station data for a USGS ShakeMap.

Parameters::

	* usgs_id: USGS event identifier
	* shakemap_version: optional ShakeMap version

Response fields: ``station_data_file``, ``n_stations``, and
``station_data_issue``.

*************************************
POST /v1/impact_get_shakemap_versions
*************************************

IMPACT mode only. Return available ShakeMap versions for ``usgs_id``.

Response fields: ``shakemap_versions``, ``usgs_preferred_version``, and
``shakemap_versions_issue``.

*****************************************
POST /v1/impact_get_nodal_planes_and_info
*****************************************

IMPACT mode only. Return nodal planes and event information for a USGS ID.

Parameters::

	* usgs_id: USGS event identifier

Response fields: ``nodal_planes``, ``nodal_planes_issue``, and ``info``.

************
GET /v1/ping
************

Health check for the WebUI. ``GET`` and ``HEAD`` are accepted and the
response is the JSON string ``"ok"``; no authentication is required.

.. _dbserver-api:

OpenQuake DbServer API
----------------------

The DbServer is a separate Django service listening on the host and port
from the ``[dbserver]`` section of ``openquake.cfg``. It serves only the
internal ``/v0`` API; the WebUI serves the public ``/v1`` API. In server
installations, start the DbServer before the WebUI.

All DbServer routes except ``/v0/ping`` require the ``X-API-Key`` header
containing ``authkey`` from ``[dbserver]``. A missing or invalid key
returns HTTP 403.

************
GET /v0/ping
************

``GET`` and ``HEAD`` health check. Returns the JSON string ``"ok"`` and
does not require an API key.

*******************
POST /v0/db/:action
*******************

Execute an allowlisted database action. The JSON request body is::

	{"args": [<action arguments>]}

The ``args`` list is passed positionally to the action function and an
optional ``kwargs`` dictionary is passed as keyword arguments. Datetime
arguments are represented as::

	{"__oq_type__": "datetime", "value": "2026-01-01T12:00:00+00:00"}

Responses use the same encoding for dates, rows, and tables:
``{"__oq_type__": "row", "fields": [...], "values": [...]}`` and
``{"__oq_type__": "table", "fields": [...], "rows": [...]}``. Scalar,
list, and dictionary results are returned as ordinary JSON values.

An unknown action and a missing database record both return HTTP 404;
the client (``logs.dbcmd``) turns any 404 into a ``NotFound`` exception,
so it cannot tell the two cases apart. Other action failures return HTTP
500 with ``{"detail": "<error>"}``.

The allowlisted database action names currently include:

.. code-block:: text

	check_outdated, has_job_table, reset_is_running, keep, set_status,
	set_aborted, create_job, import_job, delete_uncompleted_calculations,
	get_job, get_jobs, get_uncompleted_jobs, get_running_jobs, get_weight,
	list_calculations, list_outputs, get_outputs, create_outputs, finish,
	del_calc, log, get_log, get_jobs_by_date, get_job_stats, engine_version,
	what_if_I_upgrade, db_version, upgrade_db, calc_info, get_calcs,
	update_job, share_job, add_tag_to_job, remove_tag_from_job,
	set_preferred_job_for_tag, unset_preferred_job_for_tag,
	get_preferred_job_for_tag, create_tag, delete_tag, list_tags,
	update_parent_child, get_log_slice, get_log_size, get_traceback,
	get_result, get_results, get_output, get_executing_jobs, get_calc_ids,
	get_longest_jobs, find, update_job_checksum,
	get_checksum_from_job, get_job_id_from_checksum,
	get_job_from_checksum

This API is an internal compatibility interface, not a general SQL endpoint.
The authoritative allowlist is ``openquake.server.db.registry``.

************************
POST /v0/worker\_:action
************************

Run an authenticated worker-control action. The JSON request body is::

	{"args": [<worker arguments>]}

Allowed actions are ``workers_start``, ``workers_stop``, ``workers_status``,
``workers_restart``, ``workers_wait``, ``workers_kill``, and
``workers_debug``. The route segment uses the action without the
``workers_`` prefix, for example ``POST /v0/worker_status`` with
``{"args": []}``. Unknown worker actions return HTTP 404. Every action
accepts one optional argument: the ``[zworkers]`` configuration as a
dictionary of strings (``host_cores``, ``ctrl_port``) or a job ID; with
an empty ``args`` list the job ID -1 is used. The engine calls only
``workers_start``, passing the ``[zworkers]`` section of
``openquake.cfg``.

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

``username`` and ``password`` can be left empty if Django authentication is not enabled in the server, which is the
recommended way, if the server is in your own secure LAN. Otherwise you must set the credentials of a Django account.
The ``[dbserver]`` ``authkey`` is a separate credential used by internal API clients; it is not a substitute for
Django login credentials in ``WebExtractor``. The difference between case 1 and case 2 is in where to put the
``openquake.cfg`` file: if you have a production installation, put it in your $HOME, if you have a development
installation, put it in your virtualenv directory.

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

If you have a scenario calculation you may want to extract the
``avg_gmf`` output. This can be done simply with a call like::

	>> extractor = WebExtractor(calc_id, server, username, password)
	>> imts = list(extractor.oqparam.imtls)  # list of available IMTs
	>> extractor.get(f'avg_gmf?imt={imts[0]}')
	>> aw.lons   # longitudes
	>> aw.lats   # latitudes
	>> aw[imts[0]] # array of values

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
