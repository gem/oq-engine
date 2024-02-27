Probabilistic Damage Outputs
============================

Probabilistic Damage Distribution
---------------------------------

The Classical Probabilistic Damage calculator provides the expected damage distribution per asset as a csv file, an 
example of which is shown in the table below.

Example of a probabilistic damage distribution output file

+---------------+---------------+------------+--------------+-------------+--------------+
| **asset_ref** | **no_damage** | **slight** | **moderate** | **extreme** | **complete** |
+===============+===============+============+==============+=============+==============+
| a1            | 4.436E-06     | 6.3482E-03 | 3.4851E-01   | 4.7628E-01  | 1.6884E-01   |
+---------------+---------------+------------+--------------+-------------+--------------+
| a2            | 1.0391E-05    | 9.1856E-03 | 3.7883E-01   | 4.6140E-01  | 1.5056E-01   |
+---------------+---------------+------------+--------------+-------------+--------------+
| ...           | ...           | ...        | ...          | ...         | ...          |
+---------------+---------------+------------+--------------+-------------+--------------+
| a998          | 6.9569E-02    | 6.4106E+00 | 7.4108E+01   | 5.7563E+01  | 1.7848E+01   |
+---------------+---------------+------------+--------------+-------------+--------------+
| a999          | 1.2657E-01    | 8.1294E+00 | 7.6249E+01   | 5.4701E+01  | 1.6792E+01   |
+---------------+---------------+------------+--------------+-------------+--------------+

This file lists the expected number of structural units in each damage state for each asset, for the time period specified by the parameter ``risk_investigation_time``.