Event-Based PSHA
================

The Event Based PSHA calculator computes and stores stochastic event
sets and the corresponding ground motion fields.  This calculator can
also produce hazard curves and hazard maps, similar to the Classical
PSHA calculator. The inset below shows an example of the list of
results provided by the OpenQuake engine at the end of an event-based
PSHA calculation::

	user@ubuntu:~$ oq engine --lo <calc_id>
	id | name
	10 | Ground Motion Fields
	11 | Hazard Curves
	12 | Hazard Maps
	13 | Realizations
	14 | Earthquake Ruptures
	15 | Events
	16 | Uniform Hazard Spectra

Exporting the outputs from the ruptures will produce a CSV file with
the following columns:

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

The outputs from the Ground Motion Fields can be exported in the csv
format. Exporting the outputs from the Ground Motion Fields in the csv
format results in three csv files, where XXX is a placeholder for the
calculation ID:

1. ``gmf_data_XXX.csv``
2. ``sigma_epsilon_XXX.csv``
3. ``sitemesh_XXX.csv``

Here is an example of the ``gmf_data_XXX.csv`` file for the EventBasedPSHA
demo:

+---------+----------+---------+
| site_id | event_id | gmv_PGA |
+---------+----------+---------+
| 0       | 99       | 0.06888 |
+---------+----------+---------+
| 0       | 125      | 0.06498 |
+---------+----------+---------+
| 0       | 142      | 0.05881 |
+---------+----------+---------+
| 0       | 151      | 0.05569 |
+---------+----------+---------+
| 0       | 156      | 0.06918 |
+---------+----------+---------+
| 0       | 161      | 0.06629 |
+---------+----------+---------+
| 0       | 179      | 0.10528 |
+---------+----------+---------+
| 0       | 184      | 0.05503 |
+---------+----------+---------+
| 0       | 200      | 0.06455 |
+---------+----------+---------+
| ...     | ...      | ...     |
+---------+----------+---------+

The ``sitemesh_XXX.csv`` file provides the association between
the site ids in the Ground Motion Fields csv file with their latitude
and longitude coordinates, as in the following example:

+---------+---------+------+
| site_id | lon     | lat  |
+---------+---------+------+
| 0       | 0.50000 | -0.5 |
+---------+---------+------+

The ``sigma_epsilon_XXX.csv`` file provides the inter event
residuals and inter event standard deviations for each event, as
in the following example:

+----------+--------+---------------+---------------+
| event_id | rlz_id | sig_inter_PGA | eps_inter_PGA |
+----------+--------+---------------+---------------+
| 0        | 1      | 2.600000E-01  | 0.84923       |
+----------+--------+---------------+---------------+
| 1        | 1      | 2.600000E-01  | 0.25794       |
+----------+--------+---------------+---------------+
| 2        | 2      | NAN           | 0.84894       |
+----------+--------+---------------+---------------+
| 3        | 2      | NAN           | 0.00495       |
+----------+--------+---------------+---------------+
| 4        | 2      | NAN           | -0.8094396    |
+----------+--------+---------------+---------------+
| 5        | 2      | NAN           | 1.30782       |
+----------+--------+---------------+---------------+
| 6        | 3      | NAN           | 0.89407       |
+----------+--------+---------------+---------------+
| 7        | 0      | 2.600000E-01  | -1.723876     |
+----------+--------+---------------+---------------+
| 8        | 2      | NAN           | -0.4926568    |
+----------+--------+---------------+---------------+
| ...      | ...    | ...           | ...           |
+----------+--------+---------------+---------------+

Users wanting to know exactly how ``sigma`` and ``epsilon`` are computed
should look at the implementation in the file
``openquake/hazardlib/calc/gmf.py``. For instance the event based
demo uses the GMPEs BooreAtkinson2008 and ToroEtAl2002, with the
latter being defined only for the total standard deviation, and that
explains the NAN in the sigmas for some events.

The ``Events`` output produces a csv file with fields ``event_id``,
``rup_id``, ``rlz_id``, ``year`` and ``ses_id``. The ``event_id`` is a
32 bit integer that identifies uniquely the event; the ``rup_id`` is a
64 bit integer that identifies uniquely the rupture; the ``rlz_id`` is
a 16 bit integer that identifies uniquely the realization.  The
``year`` field is a random number from 0 to the effective
investigation time while the ``ses_id`` field is a random number from
0 to ``ses_per_logic_tree_path``.  Notice that in previous versions of
the engine (before engine-3.11) the semantic of those fields was
different. Here is an example:

+----------+--------+--------+--------+--------+
| event_id | rup_id | rlz_id | year   | ses_id |
+----------+--------+--------+--------+--------+
| 0        | 0      | 1      | 14_337 | 35     |
+----------+--------+--------+--------+--------+
| 1        | 0      | 1      | 14_729 | 99     |
+----------+--------+--------+--------+--------+
| 2        | 0      | 2      | 26_309 | 53     |
+----------+--------+--------+--------+--------+
| 3        | 0      | 2      | 34_672 | 219    |
+----------+--------+--------+--------+--------+
| 4        | 0      | 2      | 27_925 | 180    |
+----------+--------+--------+--------+--------+
| 5        | 0      | 2      | 31_655 | 152    |
+----------+--------+--------+--------+--------+
| 6        | 0      | 3      | 37_509 | 170    |
+----------+--------+--------+--------+--------+
| 7        | 0      | 0      | 4_784  | 225    |
+----------+--------+--------+--------+--------+
| 8        | 0      | 2      | 25_462 | 84     |
+----------+--------+--------+--------+--------+
| ...      | ...    | ...    | ...    | ...    |
+----------+--------+--------+--------+--------+

The ``Realizations`` output produces a csv file listing the source
model and the combination of ground shaking intensity models for each
path sampled from the logic tree. An example of such a file is shown
below in the table below:

+--------+-------------+---------+
| rlz_id | branch_path | weight  |
+--------+-------------+---------+
| 0      | A~AA        | 0.36000 |
+--------+-------------+---------+
| 1      | A~AB        | 0.24000 |
+--------+-------------+---------+
| 2      | A~BA        | 0.24000 |
+--------+-------------+---------+
| 3      | A~BB        | 0.16000 |
+--------+-------------+---------+

The ``branch_path`` field is used to determine which GMPEs are
being used for each tectonic region type, as explained in
the logic tree section of the documentation.
