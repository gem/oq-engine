# OpenQuake Engine Server REST API

## Introduction

oq-engine-server provides a series of REST API methods for running calculations, checking calculation status, and browsing and downloading results.

All responses are JSON, unless otherwise noted.

#### GET /v1/calc/hazard

List a summary of hazard calculations. The [url](#get-v1calchazardcalc_id) in each item of the response can be followed to retrieve complete calculation details.

Parameters: None

Response:

    [{"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 1,
      "status": "executing",
      "url": "http://localhost:8000/v1/calc/hazard/1"},
     {"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 2,
      "status": "complete",
      "url": "http://localhost:8000/v1/calc/hazard/2"},
     {"description": "Hazard Calculation for end-to-end hazard+risk",
      "id": 3,
      "status": "complete",
      "url": "http://localhost:8000/v1/calc/hazard/3"}]

#### GET /v1/calc/risk

List a summary of risk calculations. The [url](#get-v1calcriskcalc_id) in each item of the response can be followed to retrieve complete calculation details.

Parameters: None

Response:

    [{"description": "Risk Calculation for end-to-end hazard+risk",
      "id": 1,
      "status": "complete",
      "url": "http://localhost:8000/v1/calc/risk/1"},
     {"description": "Risk Calculation for end-to-end hazard+risk",
      "id": 2,
      "status": "complete",
      "url": "http://localhost:8000/v1/calc/risk/2"}]

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

#### GET /v1/calc/:calc_id/results

List a summary of results for the given `calc_id`. The [url](#get-v1calchazardresultresult_id) in each response item can be followed to retrieve the full result artifact.

Parameters: None

Response:

    [{"url": "http://localhost:8000/v1/calc/hazard/result/12", "type": "hazard_curve", "name": "hc-rlz-22", "id": 12},
     {"url": "http://localhost:8000/v1/calc/hazard/result/14", "type": "hazard_curve", "name": "hc-rlz-23", "id": 14},
     {"url": "http://localhost:8000/v1/calc/hazard/result/16", "type": "hazard_curve", "name": "hc-rlz-24", "id": 16},
     {"url": "http://localhost:8000/v1/calc/hazard/result/18", "type": "hazard_curve", "name": "hc-rlz-25", "id": 18}]


#### GET /v1/calc/result/:result_id

Get the full content of a calculation result for the given `result_id`.

Parameters:

    * export_type: the desired format for the result (`xml`, `geojson`, etc.)

Response:

The requested result as a blob of text. If the desired `export_type` is not supported, an HTTP 404 error is returned.


#### POST /v1/calc/run

Run a new calculation with the specified job config file, input models, and other parameters.

Files:

    * job_config: an oq-engine job config INI-style file
    * input_model_1 - input_model_N: any number (including zero) of input model files

Parameters:

    * migration_callback_url: optional; post to this URL to initiate post-calculation migration of results; see documentation for the oq-platform Icebox (TODO: link) for more information
    * foreign_calculation_id: optional, required with migration_callback_url; specifies the id of the calculation on the icebox side
    * hazard_calc: the hazard calculation ID upon which to run the risk calculation; specify this or hazard_result (only for risk calculations)
    * hazard_result: the hazard results ID upon which to run the risk calculation; specify this or hazard_calc (only for risk calculations)

Response: Redirects to [/v1/calc/:calc_id](#get-v1calchazardcalc_id), where `calc_id` is the ID of the newly created calculation.
