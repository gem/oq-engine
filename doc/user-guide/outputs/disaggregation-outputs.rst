Hazard Disaggregation
=====================

The OpenQuake engine outputs for a disaggregation analysis correspond
to projections of the multidimensional probability matrix containing
the results of the disaggregation. The currently available projections
are 11:

1. Mag
2. Dist
3. Mag_Dist
4. Mag_Dist_Eps
5. Lon_Lat
6. Mag_Lon_Lat
7. TRT
8. TRT_Mag
9. TRT_Lon_Lat
10. TRT_Mag_Dist
11. TRT_Mag_Dist_Eps

The user can specify the desired projects in the job.ini file by
setting the parameter `disagg_outputs`. In the disaggregation demo the
parameter is not set, so all possible outputs are generated.
The demo specifies the parameter `individual_rlzs = true`, therefore
the results are available for each realization. This is fine for
the demo, where there are only 2 realizations, but in general
specifying `individual_rlzs` is a *bad* idea, since most models have
thousands of realizations and you would end up exporting a huge
amount of data, with the risk of running out of memory.

By default the engine only export the mean disaggregation. However,
when interested to a specific realization, the user can specify the
realization on which to perform the disaggregation by setting the
``rlz_index`` parameter in the ``job.ini`` file.

NB: before version 3.17 the default algorithm used was different: only
the realization closest to the mean hazard curve was selected and used
perform the disaggregation. This was a choice forced by performance
limitations that do not apply to recent versions of the disaggregation
calculator, which instead is able to compute all realizations and
then perform a weighted mean of the probabilities.

For the disaggregation demo the list of outputs are the following:

::

   user@ubuntu:~$ oq engine --lo <calc_id>
   id | name
   1156 | Disaggregation Outputs Per Realization
   1157 | Statistical Disaggregation Outputs
   1158 | Full Report
   1159 | Hazard Curves
   1160 | Realizations

Running ``--export-output`` to export the disaggregation results will
produce individual files for each site. Since the demo considers 2 sites
you will get 2 x 11 = 22 files for the statistical outputs:

1. Dist-mean-0_<calc_id>.csv
2. Dist-mean-1_<calc_id>.csv
3. Lon_Lat-mean-0_<calc_id>.csv
4. Lon_Lat-mean-1_<calc_id>.csv
5. Mag-mean-0_<calc_id>.csv
6. Mag-mean-1_<calc_id>.csv
7. Mag_Dist-mean-0_<calc_id>.csv
8. Mag_Dist-mean-1_<calc_id>.csv
9. Mag_Dist_Eps-mean-0_<calc_id>.csv
10. Mag_Dist_Eps-mean-1_<calc_id>.csv
11. Mag_Lon_Lat-mean-0_<calc_id>.csv
12. Mag_Lon_Lat-mean-1_<calc_id>.csv
13. TRT-mean-0_<calc_id>.csv
14. TRT-mean-1_<calc_id>.csv
15. TRT_Lon_Lat-mean-0_<calc_id>.csv
16. TRT_Lon_Lat-mean-1_<calc_id>.csv
17. TRT_Mag-mean-0_<calc_id>.csv
18. TRT_Mag-mean-1_<calc_id>.csv
19. TRT_Mag_Dist-mean-0_<calc_id>.csv
20. TRT_Mag_Dist-mean-1_<calc_id>.csv
21. TRT_Mag_Dist_Eps-mean-0_<calc_id>.csv
22. TRT_Mag_Dist_Eps-mean-1_<calc_id>.csv

Alternatively, you can use the commands

::

   user@ubuntu:~$ oq export disagg-rlzs <calc_id>
   user@ubuntu:~$ oq export disagg-stats <calc_id>

which will produce the same files as the usual ``--export-outputs``.
For instance the disaggregation by magnitude will produce files
like the following for the realizations:

.. container:: listing

   .. code:: csv
      :name: lst:output_disagg_rlzs_Mag

      #,,,,,"generated_by='OpenQuake engine 3.20.0-git41d16a6e0a'...
      imt,iml,poe,mag,rlz1,rlz0
      PGA,2.22492E-01,1.00000E-01,5.50000E+00,4.30692E-02,4.30692E-02
      PGA,2.22492E-01,1.00000E-01,6.50000E+00,5.97611E-02,5.98033E-02
      PGA,2.22492E-01,1.00000E-01,7.50000E+00,2.44507E-04,4.68981E-04
      PGA,1.69922E-01,2.00000E-01,5.50000E+00,1.05186E-01,1.05186E-01
      PGA,1.69922E-01,2.00000E-01,6.50000E+00,1.06652E-01,1.06838E-01
      PGA,1.69922E-01,2.00000E-01,7.50000E+00,7.87177E-04,1.41027E-03

The demo contains 3 magnitude bins and ``poes_disagg = 0.1 0.2``, so there
are 6 lines in the CSV. There is a column for each realization but they
are not ordered.

The statistical exporter will produce the following for the means:

.. container:: listing

   .. code:: csv
      :name: lst:output_disagg_mean_Mag

      ,,,,"generated_by='OpenQuake engine 3.20.0-git41d16a6e0a'...
      imt,iml,poe,mag,mean
      PGA,2.22492E-01,1.00000E-01,5.50000E+00,4.30692E-02
      PGA,2.22492E-01,1.00000E-01,6.50000E+00,5.97864E-02
      PGA,2.22492E-01,1.00000E-01,7.50000E+00,3.79197E-04
      PGA,1.69922E-01,2.00000E-01,5.50000E+00,1.05186E-01
      PGA,1.69922E-01,2.00000E-01,6.50000E+00,1.06764E-01
      PGA,1.69922E-01,2.00000E-01,7.50000E+00,1.16108E-03

Most users will expect the disaggregation results to be in the traditional
form of Bazzurro and Cornell, 1999. However, the engine does not
follow that tradition, as explained in the :ref:`science manual <underlying-science/PSHA-with-OQ-engine:Comparison between OpenQuake engine disaggregation and traditional disaggregation>`.
Still, we provide a command to export the
disaggregation results in the traditional form. Simply write

::

   user@ubuntu:~$ oq export disagg-rlzs-traditional <calc_id>

For instance for the realization magnitude output you will get

.. container:: listing

   .. code:: csv
      :name: lst:output_disagg_rlzs_traditional_Mag

      #,,,,,"generated_by='OpenQuake engine 3.20.0-git41d16a6e0a'...
      imt,iml,poe,mag,rlz1,rlz0
      PGA,2.22492E-01,1.00000E-01,5.50000E+00,4.15754E-01,4.14699E-01
      PGA,2.22492E-01,1.00000E-01,6.50000E+00,5.81937E-01,5.80882E-01
      PGA,2.22492E-01,1.00000E-01,7.50000E+00,2.30935E-03,4.41874E-03
      PGA,1.69922E-01,2.00000E-01,5.50000E+00,4.94599E-01,4.92775E-01
      PGA,1.69922E-01,2.00000E-01,6.50000E+00,5.01897E-01,5.00967E-01
      PGA,1.69922E-01,2.00000E-01,7.50000E+00,3.50451E-03,6.25733E-03

In the traditional format the probabilities compose to 1.0 while in
the engine format the probabilities compose to the PoE listed
in ``poes_disagg``.
