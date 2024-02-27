Scenario Risk Outputs
=====================

The Scenario Risk Calculator produces the following set of output files:

1. ``Aggregate Asset Losses``: this file contains the aggregated scenario loss statistics for the entire portfolio of assets defined in the *Exposure Model*. The mean (``mean``) and standard deviation (``stddev``) of the total loss for the portfolio of assets are listed in this file.
2. ``Average Asset Losses``: this file contains mean (``mean``) and associated standard deviation (``stddev``) of the scenario loss for all assets at each of the unique locations in the *Exposure Model*.
3. ``Aggregate Event Losses``: this file contains the total loss for the portfolio of assets defined in the *Exposure Model* for each realization of the scenario generated in the Monte Carlo simulation process.

In addition, if the OpenQuake-QGIS plugin is used for visualizing or exporting the results from a Scenario Risk 
Calculation, the following additional outputs can be exported:

4. ``losses_by_tag``: this file contains the scenario loss statistics for each of the tags defined in the *Exposure Model*. For each tag, the mean (``mean``) and associated standard deviation (``stddev``) of the losses for each tag are listed in this file.

If the calculation involves multiple Ground Motion Prediction Equations, separate output files are generated for each 
of the above outputs, for each of the different Ground Motion Prediction Equations used in the calculation.

These different output files for Scenario Risk calculations are described in more detail in the following subsections.

Scenario loss statistics
------------------------

*********************
Asset loss statistics
*********************

This output is always produced for a Scenario Risk calculation and comprises a mean total loss and associated standard 
deviation for each of the individual assets defined in the *Exposure Model* that fall within the ``region`` and have a 
computed Ground Motion Field value available within the defined ``asset_hazard_distance``. These results are stored in a 
comma separate value (.csv) file as illustrated in the example shown in the table below.

Example of a scenario asset loss distribution output file

+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| **asset_ref** | **taxonomy** | **lon**    | **lat**  | **structural_mean** | **structural_stddev** | ... |
+===============+==============+============+==========+=====================+=======================+=====+
| a3            | wood         | -122.57000 | 38.11300 | 686,626             | 1,070,680             | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| a2            | concrete     | -122.11400 | 38.11300 | 1,496,360           | 2,121,790             | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| a5            | wood         | -122.00000 | 37.91000 | 3,048,910           | 4,339,480             | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| a4            | steel        | -122.00000 | 38.00000 | 9,867,070           | 15,969,600            | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| a1            | wood         | -122.00000 | 38.11300 | 12,993,800          | 22,136,700            | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| a6            | concrete     | -122.00000 | 38.22500 | 5,632,180           | 9,508,760             | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+
| a7            | wood         | -121.88600 | 38.11300 | 2,966,190           | 5,270,480             | ... |
+---------------+--------------+------------+----------+---------------------+-----------------------+-----+

*******************
Tag loss statistics
*******************

If the OpenQuake-QGIS plugin is used for visualizing or exporting the results from a Scenario Risk Calculation, the 
total expected losses for assets of each tag will be computed and made available for export as a csv file. This 
distribution of losses per asset tag is depicted in the example output file snippet in the table below.

Example of a scenario loss distribution per tag output file

+----------+--------------+-------------------+----------------+
| **tag**  | **contents** | **nonstructural** | **structural** |
+==========+==============+===================+================+
| wood     | 526,754.0    | 759,653.0         | 393,912.0      |
+----------+--------------+-------------------+----------------+
| concrete | 587,773.0    | 1,074,620.0       | 142,571.0      |
+----------+--------------+-------------------+----------------+
| steel    | 407,821.0    | 923,281.0         | 197,341.0      |
+----------+--------------+-------------------+----------------+

The output file lists the mean loss aggregated for each tags present in the exposure model and selected by the for all 
loss types (amongst “structural”, “nonstructural”, “contents”, or “business_interruption”) for which a *Vulnerability Model* 
file was provided in the configuration file.

*********************
Total loss statistics
*********************

If the OpenQuake-QGIS plugin is used for visualizing or exporting the results from a Scenario Risk Calculation, the 
mean total loss and associated standard deviation for the selected earthquake rupture will be computed and made 
available for export as a csv file, as illustrated in the example shown in the table below.

Example of a scenario total loss output file

+----------------+----------+---------------+----------------+
| **loss_type**  | **unit** | **mean**      | **stddev**     |
+================+==========+===============+================+
| structural     | USD      | 8717775315.66 | 2047771108.36  |
+----------------+----------+---------------+----------------+

Scenario losses by event
------------------------

The losses by event output lists the total losses for each realization of the scenario generated in the Monte Carlo 
simulation process for all loss types for which a Vulnerability Model file was provided in the configuration file. 
These results are exported in a comma separate value (.csv) file as illustrated in the example shown in the table below.

Example of a scenario losses by event output file

+-----------+----------------+-------------------+
| **event** | **structural** | **nonstructural** |
+===========+================+===================+
| 1         | 2,194.74       | 20,767.00         |
+-----------+----------------+-------------------+
| 2         | 4,037.57       | 20,905.00         |
+-----------+----------------+-------------------+
| 3         | 2,950.80       | 18,635.50         |
+-----------+----------------+-------------------+
| 4         | 7,787.75       | 19,041.40         |
+-----------+----------------+-------------------+
| 5         | 3,964.19       | 30,982.80         |
+-----------+----------------+-------------------+
| 6         | 19,394.60      | 40,274.60         |
+-----------+----------------+-------------------+
| ...       | ...            | ...               |
+-----------+----------------+-------------------+