Outputs from Scenario Hazard Analysis
=====================================

By default, the scenario hazard calculator computes and stores Ground Motion Fields for each GMPE specified in the job 
configuration file. The Ground Motion Fields will be computed at each of the sites and for each of the intensity measure 
types specified in the job configuration file.

Exporting the outputs from the Ground Motion Fields in the csv format results in two csv files illustrated in the 
example files in the following tables. The sites csv file provides the association between the site ids in the Ground 
Motion Fields csv file with their latitude and longitude coordinates.

.. _gmf-csv:
.. table:: Example of a ground motion fields csv output file for a scenario

+----------+---------+---------+-------------+-----------------+-----------------+
| **rlzi** | **sid** | **eid** | **gmv_PGA** | **gmv_SA(0.3)** | **gmv_SA(1.0)** |
+==========+=========+=========+=============+=================+=================+
| 0        | 0       | 0       | 0.062       | 0.119           | 0.157           |
+----------+---------+---------+-------------+-----------------+-----------------+
| 0        | 1       | 0       | 0.086       | 1.533           | 0.260           |
+----------+---------+---------+-------------+-----------------+-----------------+
| 0        | 2       | 0       | 0.223       | 1.647           | 0.232           |
+----------+---------+---------+-------------+-----------------+-----------------+
| ...      | ...     | ...     | ...         | ...             | ...             |
+----------+---------+---------+-------------+-----------------+-----------------+
| 1        | 4       | 99      | 2.467       | 0.750           | 1.918           |
+----------+---------+---------+-------------+-----------------+-----------------+
| 1        | 5       | 99      | 0.601       | 0.828           | 2.272           |
+----------+---------+---------+-------------+-----------------+-----------------+
| 1        | 6       | 99      | 0.514       | 0.340           | 1.202           |
+----------+---------+---------+-------------+-----------------+-----------------+

In this example, the gmfs have been computed using two different GMPEs (and without conditioning the ground shaking to 
observations), so the realization indices (’rlzi’) in the first column of the example gmfs file are either 0 or 1. The 
gmfs file lists the ground motion values for 100 simulations of the scenario, so the event indices (’eid’) in the third 
column go from 0–99. There are seven sites with indices 0–6 (’sid’) which are repeated in the second column for each of 
the 100 simulations of the event and for each of the two GMPEs. Finally, the subsequent columns list the ground motion 
values for each of the intensity measure types specified in the job configuration file.

.. _sites-csv:
.. table:: Example of a sites csv output file for a scenario

+-------------+------------+----------+
| **site_id** | **lon**    | **lat**  |
+=============+============+==========+
| 0           | -122.57000 | 38.11300 |
+-------------+------------+----------+
| 1           | -122.11400 | 38.11300 |
+-------------+------------+----------+
| 2           | -122.00000 | 37.91000 |
+-------------+------------+----------+
| 3           | -122.00000 | 38.00000 |
+-------------+------------+----------+
| 4           | -122.00000 | 38.11300 |
+-------------+------------+----------+
| 5           | -122.00000 | 38.22500 |
+-------------+------------+----------+
| 6           | -121.88600 | 38.11300 |
+-------------+------------+----------+

For scenario hazard calculations that consider the conditioning of the ground shaking to siesmic station or macroseismic 
observations, the nominal event bias, one bias value for each IMT, and for every GSIM used in the calculation is 
displayed and stored in the calculation log. The calculation log can be obtained using ``oq engine --show-log CALC_ID`` 
in the terminal.