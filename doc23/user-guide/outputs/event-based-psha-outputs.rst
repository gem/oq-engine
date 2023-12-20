Event-Based PSHA Outputs
========================

The Event Based PSHA calculator computes and stores stochastic event sets and the corresponding ground motion fields. 
This calculator can also produce hazard curves and hazard maps, similar to the Classical PSHA calculator. The inset 
below shows an example of the list of results provided by the OpenQuake engine at the end of an event-based PSHA 
calculation::

	user@ubuntu:~$ oq engine --lo <calc_id>
	id | name
	10 | Ground Motion Fields
	11 | Hazard Curves
	12 | Hazard Maps
	13 | Realizations
	14 | Earthquake Ruptures
	15 | Events
	16 | Uniform Hazard Spectra

Exporting the outputs from the ruptures will produce a CSV file with the following columns:

1. ``rup_id``: incremental number identifying the rupture
2. ``multiplicity``: how many times the rupture occurs in the effective investigation time
3. ``mag``: float specifying the magnitude of the rupture
4. ``centroid_lon``: longitude of the centroid of the rupture
5. ``centroid_lat``: latitude of the centroid of the rupture
6. ``centroid_depth``: depth (in km) of the centroid of the rupture
7. ``trt``: string specifying the tectonic region type
8. ``strike``: strike angle of the rupture surface
9. ``dip``: dip angle of the rupture surface
10. ``rake``: rake angle of the rupture surface

The outputs from the Ground Motion Fields can be exported in the csv format. Exporting the outputs from the Ground 
Motion Fields in the csv format results in two csv files illustrated in the example files in this document. 
The sites csv file provides the association between the site ids in the Ground Motion Fields csv file with their 
latitude and longitude coordinates.

Example of a ground motion fields csv output file for an event based hazard calculation

+------------+-------------+--------------+-------------+-----------------+-----------------+
| **rlz_id** | **site_id** | **event_id** | **gmv_PGA** | **gmv_SA(0.3)** | **gmv_SA(1.0)** |
+============+=============+==============+=============+=================+=================+
| 0          | 0           | 48           | 0.0089      | 0.0686          | 0.0065          |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| 0          | 0           | 54           | 0.0219      | 0.0325          | 0.0164          |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| ...        | ...         | ...          | ...         | ...             | ...             |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| 0          | 6           | 75           | 0.0246      | 0.0244          | 0.0036          |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| 1          | 0           | 76           | 0.0189      | 0.0327          | 0.0094          |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| 1          | 0           | 77           | 0.0286      | 0.0683          | 0.0471          |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| ...        | ...         | ...          | ...         | ...             | ...             |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| ...        | ...         | ...          | ...         | ...             | ...             |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| 7          | 6           | 1754         | 0.3182      | 1.2973          | 0.6127          |
+------------+-------------+--------------+-------------+-----------------+-----------------+
| 7          | 6           | 1755         | 0.2219      | 0.6200          | 0.5069          |
+------------+-------------+--------------+-------------+-----------------+-----------------+

The ``Events`` output produces a csv file with fields ``event_id``, ``rup_id`` and ``rlz_id``. The ``event_id`` is a 32 
bit integer that identifies uniquely the event; the ``rup_id`` is a 64 bit integer that identifies uniquely the rupture; 
the ``rlz_id`` is a 16 bit integer that identifies uniquely the realization. The association between the ``event_id`` and 
the ``rup_id`` is stored inside the ``Events`` output.

The ``Realizations`` output produces a csv file listing the source model and the combination of ground shaking intensity 
models for each path sampled from the logic tree. An example of such a file is shown below in the table below.

Example of a realizations file

+-------------+-----------------+------------+
| **ordinal** | **branch_path** | **weight** |
+=============+=================+============+
| 0           | b1~b11_b21      | 0.1125     |
+-------------+-----------------+------------+
| 1           | b1~b11_b22      | 0.075      |
+-------------+-----------------+------------+
| 2           | b1~b12_b21      | 0.0375     |
+-------------+-----------------+------------+
| 3           | b1~b12_b22      | 0.025      |
+-------------+-----------------+------------+
| 4           | b2~b11_b21      | 0.3375     |
+-------------+-----------------+------------+
| 5           | b2~b11_b22      | 0.225      |
+-------------+-----------------+------------+
| 6           | b2~b12_b21      | 0.1125     |
+-------------+-----------------+------------+
| 7           | b2~b12_b22      | 0.075      |
+-------------+-----------------+------------+