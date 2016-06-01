List of official CSV outputs
============================================

One of the most important features of the engine version 2.0 is that
finally the CSV output format has become officially supported.
For several releases the engine was able to export CSV files,
but the feature was always considered experimental and not
documented.

With engine 2.0 several CSV outputs have become official.
This changes simplifies the workflow. Before engine 2.0 an user
had to

1. run a computation with the engine
2. export the results she was interested in NRML format
3. use a NRML converter to produce a CSV file
4. plot the CSV file

Now one can directly export in CSV format and skip point 3.
If you want to export all of the results you can simply run

  `$ oq-engine --run job.ini --exports csv`

hazard-curve
lon lat,PGA,SA(0.1)
0.00000 0.00000,4.5701349E-01 5.8626788E-02 6.8661644E-03,6.0867476E-01 3.3083046E-01 2.0147122E-01

hazard-map
lon,lat,PGA~0.1,SA(0.2)~0.1
-1.223400E+02,3.772000E+01,2.840000E-01,2.840000E-01

uhs
lon,lat,poe~0.01-PGA,poe~0.01-SA(0.1),poe~0.1-PGA,poe~0.1-SA(0.1),poe~0.2-PGA,poe~0.2-SA(0.1)
-1.000000E-01,0.000000E+00,2.000000E-01,8.000000E-01,2.000000E-01,8.000000E-01,2.000000E-01,8.000000E-01

gmf one file per IMT
lon,lat,000,001,002,003,004,005,006,007,008,009
0.00000,0.00000,0.44089,0.55028,0.30690,0.41737,0.73927,0.74373,0.23636,0.27041,0.20602,0.37917
