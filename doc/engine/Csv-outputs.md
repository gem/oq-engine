Engine 2.0: enter CSV outputs
============================================

One of the most important features of the engine version 2.0 is that
the CSV output format has become officially supported at last.
For several releases the engine was able to export CSV files,
but the feature was always considered experimental and not
documented. With engine 2.0 the CSV outputs have become official:
there are still some rought edges (outputs for which there is no
CSV exporter, or output for which the CSV exporter will change
in the future) but most CSV exports are now stable.

This changes simplifies the workflow. Before engine 2.0 an user
had to

1. run a computation with the engine
2. export the results she was interested in NRML format
3. use a NRML converter to produce a CSV file
4. plot the CSV file

Now one can directly export in CSV format and skip point 3.
If you want to export all of the results you can simply run

  `$ oq-engine --run job.ini --exports csv`

and that's all. There are certain conversions on the names of the exported
files and on the headers that the user should be aware of.


Names of the CSV files
------------------------

When you run a computation you will see an output like the following:

Calculation 24589 finished correctly in 15 seconds
  id | name
   2 | hcurves
   3 | uhs

The first column (the `id` column) contains the output ID, which is used
to export the output with the command

`$ oq-engine --eo <output_id> <output_dir>` --exports csv

The second column (the `name` column) contains the name of the output in
the datastore. This is usually very similar to the name of the exported file.
For instance you could get something like this::

 $ oq-engine --eo 2 /tmp/ --exports csv
 Files exported:
 /tmp/hazard_curve-mean_24589.csv
 /tmp/hazard_curve-rlz-000_24589.csv
 /tmp/hazard_curve-rlz-001_24589.csv
 /tmp/hazard_curve-rlz-002_24589.csv
 /tmp/hazard_curve-rlz-003_24589.csv
 /tmp/hazard_curve-rlz-004_24589.csv
 /tmp/hazard_curve-rlz-005_24589.csv
 /tmp/hazard_curve-rlz-006_24589.csv
 /tmp/hazard_curve-rlz-007_24589.csv

In this example there were 8 realizations. There is one file per realization
and the filename ends with the suffix

`-rlz-<ordinal>_<calc_id>.csv`

The header of the files has a format like the following::

lon,lat,IMT11, ... , IMT1N, ..., IMTN1, ... IMTNN
lon,lat,PGA-0.0001,PGA-0.001,PGA-0.01,PGA-0.05,PGA-0.1,PGA-0.15,PGA-0.2,SA(0.1)-0.0001,SA(0.1)-0.001,SA(0.1)-0.01,SA(0.1)-0.05,SA(0.1)-0.1,SA(0.1)-0.15,SA(0.1)-0.2,SA(0.1)-0.3,SA(0.1)-0.5,SA(0.1)-0.8

/tmp/hazard_uhs-mean_24589.csv
/tmp/hazard_uhs-rlz-000_24589.csv
/tmp/hazard_uhs-rlz-001_24589.csv
/tmp/hazard_uhs-rlz-002_24589.csv
/tmp/hazard_uhs-rlz-003_24589.csv
/tmp/hazard_uhs-rlz-004_24589.csv
/tmp/hazard_uhs-rlz-005_24589.csv
/tmp/hazard_uhs-rlz-006_24589.csv
/tmp/hazard_uhs-rlz-007_24589.csv

- here is an example hazard curve:

lon          |lat         |PGA-0.001   |PGA-0.005   |PGA-0.01   |PGA-0.05     |SA(0.1)-0.001|SA(0.1)-0.005|SA(0.1)-0.01|SA(0.1)-0.05|SA(0.1)-0.1 |SA(0.1)-0.15
-------------|------------|------------|------------|-----------|-------------|-------------|-------------|------------|------------|------------|------------
-1.000000E-01|0.000000E+00|6.559523E-01|6.559523E-01|6.556640E-01|6.135122E-01|5.289103E-01 |4.375274E-01 |3.509940E-01|6.559523E-01|6.559523E-01|6.559503E-01


- here is an example of UHS:

lon          |lat         |0.01~PGA    |0.01~SA(0.1)|0.1~PGA     |0.1~SA(0.1) |0.2~PGA     |0.2~SA(0.1)
-------------|------------|------------|------------|------------|------------|------------|------------
-1.000000E-01|0.000000E+00|2.000000E-01|8.000000E-01|2.000000E-01|8.000000E-01|2.000000E-01|6.835696E-01
 0.000000E+00|0.000000E+00|2.000000E-01|8.000000E-01|2.000000E-01|6.670024E-01|2.000000E-01|4.285911E-01
 1.000000E-01|0.000000E+00|2.000000E-01|8.000000E-01|2.000000E-01|8.000000E-01|2.000000E-01|6.735378E-01
