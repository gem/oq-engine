# OpenQuake Engine Server REST API

## Introduction

oq engine server provides a series of REST API methods for running calculations, checking calculation status, and browsing and downloading results.

All responses are JSON, unless otherwise noted.


#### GET /v1/calc/list

List the available calculations. The [url](#get-v1calccalc_id) in each item of the response can be followed to retrieve complete calculation details.

Parameters: None

Response:

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


#### POST /v1/calc/:calc_id/abort

Abort the given `calc_id` by sending to the corresponding job a SIGTERM.

Parameters: None

Response:

    {'error': 'Job <id> is not running'}
    {'error': 'User <user> has no permission to kill job <id>'}
    {'error': 'PID for job <id> not found in the database'}
    {'success': 'Killing job <id>'}

#### GET /v1/calc/:calc_id/status

Return the calculation status (the same content of `/v1/calc/list`) for the given `calc_id`.

Parameters: None

Response:

    {"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 1,
      "status": "executing",
      "calculation_mode": "classical",
      "is_running": true,
      "owner: "michele",
      "parent_id": "42",
      "url": "http://localhost:8800/v1/calc/1"}


#### GET /v1/calc/:calc_id

Get calculation status and times for the given `calc_id`.

Parameters: None

Response:

    {"user_name": "michele",
    "is_running": 0,
    "stop_time": "2017-06-05 12:01:28.575776",
    "status": "failed",
    "start_time": "2017-06-05 12:01:26"}


#### GET /v1/calc/:calc_id/traceback

Get the calculation traceback for the given `calc_id` as a list of
strings.

Parameters: None

Response:

A list of error lines extracted from the log. If the calculation was
successfull, the list is empty.


#### GET /v1/calc/:calc_id/extract/:spec

Get an .npz file for the given object specification. If `spec` ends with
the extension `.attrs` the attributes of the underlying object (usually
coming from an HDF5 dataset) are used to build the .npz file, while the
object itself is not retrieved.

Response:

A single .npz file of Content-Type: application/octet-stream


#### GET /v1/calc/:calc_id/results

List a summary of results for the given `calc_id`. The [url](#get-v1calchazardresultresult_id) in each response item can be followed to retrieve the full result artifact.

Parameters: None

Response:
```
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
```

#### GET /v1/calc/:calc_id/result/list

Same as GET /v1/calc/:calc_id/results


#### GET /v1/calc/result/:result_id

Get the full content of a calculation result for the given `result_id`.

Parameters:

    * export_type: the desired format for the result (`xml`, `geojson`, etc.)
    * dload: `true` to force download, not `true` try to open in browser window

Response:

The requested result as a blob of text. If the desired `export_type` is not supported, an HTTP 404 error is returned.


#### GET /v1/calc/:calc_id/log/[:start]:[:stop]

Get a slice of the calculation log for the given `calc_id`, from `start`
to `stop`. If `start` is the empty string, consider it `0` and starts
from the beginning. If `stop` is the empty string, gives all the
available lines. For instance `http://host/v1/calc/123/log/:` gives the
complete log for calculation 123.

Parameters: None

Response:

The requested log slice as a JSON list of rows


#### GET /v1/calc/:calc_id/log/size

Get the (current) number of lines of the calculation log for the given
`calc_id`.

Parameters: None

Response:

The number of lines of log


#### GET v1/calc/:calc_id/datastore

Get the HDF5 datastore for the calculation identified by the parameter `calc_id`.


#### POST /v1/calc/:calc_id/remove

Remove the calculation specified by the parameter `calc_id`.


#### POST /v1/calc/run

Run a new calculation with the specified job config file, input models, and other parameters.

Files:

    * job_config: an oq engine job config INI-style file
    * input_model_1 - input_model_N: any number (including zero) of input model files

Parameters:

    * hazard_job_id: the hazard calculation ID upon which to run the risk calculation; specify this or hazard_result (only for risk calculations)
    * hazard_result: the hazard results ID upon which to run the risk calculation; specify this or hazard_job_id (only for risk calculations)

Response: Redirects to [/v1/calc/:calc_id](#get-v1calchazardcalc_id), where `calc_id` is the ID of the newly created calculation.


#### POST /v1/calc/aelo_run

Run a new aelo calculation for a site with the specified parameters.

Parameters:
    * lon: the longitude of the site (a float in the interval [-180, +180])
    * lat: the latitude of the site (a float in the interval [-90.0, +90.0])
    * vs30: the time-averaged shear-wave velocity from the surface to a depth of 30 meters (a positive float)
    * siteid: an ID to assign to the site (the only accepted chars are a-zA-Z0-9_-:)

Response:
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

    As soon as the job is complete, a notification is automatically sent via email to the user
    who launched it. In case of success, the message will contain a link to the web page showing
    the outputs of the calculation; otherwise, it will describe the error that occurred.


#### POST /v1/calc/validate_zip

Check if a given job.zip archive is valid

Parameters:

    * archive: the zip file to be validated

Response:

a JSON object, containing:

    * valid: a boolean indicating if the provided archive is a valid job.zip
    * error_msg: the error message, if any error was found (None otherwise)


#### POST /v1/valid/

Check if a given XML text is a valid NRML.

Parameters:

    * xml_text: the text of the xml to be validated as nrml

Response:

a JSON object, containing:

    * valid: a boolean indicating if the provided text is a valid NRML
    * error_msg: the error message, if any error was found (None otherwise)
    * error_line: line of the given XML where the error was found (None if no error was found or if it was not a validation error)


#### POST /v1/on_same_fs

Check if a given filename exists and if the first 32 bytes of its content have the same checksum passed as argument of POST.

*(developed for internal purposes)*

Parameters:

    * filename: filename (with path) of file to be checked
    * checksum: expected checksum of first 32 bytes of the file

Response:

a JSON object, containing:

    * success: a boolean indicating that filename is accessible by engine server and that calculated checksum matches passed parameter


#### GET /v1/ini_defaults

Retrieve all default values for ini file parameters (parameters without a default value are not returned).

*(developed for internal purposes)*

Parameters: None

Response:
```json
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
```

#### POST /accounts/ajax_login/

Attempt to login, given the parameters `username` and `password`


#### POST /accounts/ajax_logout/

Logout


#### GET /reset_password/

The user is asked to submit a web form with the email address associated to
his/her Django account. Then a "Reset Password" email is sent to the user. By
clicking on the link received via email, the user is redirected to a web form
to specify a new password.


#### GET /v1/engine_version

Return a string with the OpenQuake engine version


#### GET /v1/engine_latest_version

Return a string with if new versions have been released.
Return 'None' if the version is not available


#### GET /v1/available_gsims

Return a list of strings with the available GSIMs
