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

#### GET /v1/calc/:calc_id/oqparam

Get the parameters of the given `calc_id`.

Parameters: None

Response:

    {"area_source_discretization": 10.0,
     "calculation_mode": "classical",
     "description": "Hazard Calculation for end-to-end hazard+risk",
     "intensity_measure_types_and_levels": {"PGA": [0.01, 0.04, 0.07, 0.1]},
     "investigation_time": 50.0,
     "maximum_distance": 300.0,
     "mean_hazard_curves": true,
     "number_of_logic_tree_samples": 0,
     "poes": [0.1, 0.2],
     "is_running": false,
     "quantile_hazard_curves": [0.15, 0.5, 0.85],
     "random_seed": 1024,
     "reference_depth_to_1pt0km_per_sec": 50.0,
     "reference_depth_to_2pt5km_per_sec": 2.5,
     "reference_vs30_type": "measured",
     "reference_vs30_value": 800.0,
     "rupture_mesh_spacing": 20.0,
     "sites": {"coordinates": [[-78.182, 15.615]], "type": "MultiPoint"},
     "truncation_level": 4.0,
     "uniform_hazard_spectra": false,
     "width_of_mfd_bin": 0.2}


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
     'name': 'Seismic Source Groups',
     'outtypes': ['csv'],
     'size_mb': None,
     'type': 'sourcegroups',
     'url': 'http://127.0.0.1:8800/v1/calc/result/31'}]
```
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

Parameters:

    * filename: filename (with path) of file to be checked
    * checksum: expected checksum of first 32 bytes of the file

Response:

a JSON object, containing:

    * success: a boolean indicating that filename is accessible by engine server and that calculated checksum matches passed parameter


#### POST /accounts/ajax_login/

Attempt to login, given the parameters `username` and `password`


#### POST /accounts/ajax_logout/

Logout


#### GET /v1/engine_version

Return a string with the OpenQuake engine version


#### GET /v1/engine_latest_version

Return a string with if new versions have been released.
Return 'None' if the version is not available


#### GET /v1/available_gsims

Return a list of strings with the available GSIMs
