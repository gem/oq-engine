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
      "job_type": "hazard",
      "is_running": true,
      "url": "http://localhost:8000/v1/calc/1"},
     {"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 2,
      "status": "complete",
      "job_type": "hazard",
      "is_running": true,
      "url": "http://localhost:8000/v1/calc/2"},
     {"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 3,
      "status": "complete",
      "job_type": "hazard",
      "is_running": false,
      "url": "http://localhost:8000/v1/calc/3"}]


#### GET /v1/calc/:calc_id/status

Return the calculation status (the same content of `/v1/calc/list`) for the given `calc_id`.

Parameters: None

Response:

    {"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 1,
      "status": "executing",
      "job_type": "hazard",
      "is_running": true,
      "url": "http://localhost:8000/v1/calc/1"}


#### GET /v1/calc/:calc_id

Get calculation status and parameter summary for the given `calc_id`.

Parameters: None

Response:

    {"area_source_discretization": 10.0,
     "calculation_mode": "classical",
     "description": "Hazard Calculation for end-to-end hazard+risk",
     "id": 2,
     "intensity_measure_types_and_levels": {"SA(0.1)": [0.01, 0.04, 0.07, 0.1, 0.13, 0.16, 0.19, 0.22, 0.25, 0.28, 0.31, 0.34, 0.37, 0.4, 0.43, 0.46, 0.49, 0.52, 0.55, 0.58, 0.61, 0.64, 0.67, 0.7, 0.73, 0.77, 0.8, 0.83, 0.86, 0.89, 0.92, 0.95, 0.98, 1.01, 1.04, 1.07, 1.1, 1.13, 1.16, 1.19, 1.22, 1.25, 1.28, 1.31, 1.34, 1.37, 1.4, 1.43, 1.46, 1.5]},
     "investigation_time": 50.0,
     "maximum_distance": 300.0,
     "mean_hazard_curves": true,
     "no_progress_timeout": 3600,
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
     "status": "complete",
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


#### GET /v1/calc/:calc_id/results

List a summary of results for the given `calc_id`. The [url](#get-v1calchazardresultresult_id) in each response item can be followed to retrieve the full result artifact.

Parameters: None

Response:

    [{"url": "http://localhost:8000/v1/calc/hazard/result/12", "type": "hazard_curve", "outtypes": [ "xml" ], "name": "hc-rlz-22", "id": 12},
     {"url": "http://localhost:8000/v1/calc/hazard/result/14", "type": "hazard_curve", "outtypes": [ "xml" ], "name": "hc-rlz-23", "id": 14},
     {"url": "http://localhost:8000/v1/calc/hazard/result/16", "type": "hazard_curve", "outtypes": [ "xml" ], "name": "hc-rlz-24", "id": 16},
     {"url": "http://localhost:8000/v1/calc/hazard/result/18", "type": "hazard_curve", "outtypes": [ "xml" ], "name": "hc-rlz-25", "id": 18}]


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

Remove the calculation specified by the parameter `calc_id`, by setting the field oq_job.relevant to False.


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

Leverage oq-risklib to check if a given XML text is a valid NRML.

Parameters:

    * xml_text: the text of the xml to be validated as nrml

Response:

a JSON object, containing:
    * valid: a boolean indicating if the provided text is a valid NRML
    * error_msg: the error message, if any error was found (None otherwise)
    * error_line: line of the given XML where the error was found (None if no error was found or if it was not a validation error)


#### POST /v1/ajax_login/

Attempt to login, given the parameters `username` and `password`


#### POST /v1/ajax_logout/

Logout


#### GET /v1/version/

Return a string with the openquake.engine version

