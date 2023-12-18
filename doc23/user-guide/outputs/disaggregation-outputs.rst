Hazard Disaggregation Outputs
=============================

The OpenQuake engine output of a disaggregation analysis corresponds to the
combination of a hazard curve and a multidimensional matrix containing
the results of the disaggregation. For a typical disaggregation
calculation the list of outputs are the following:

::

   user@ubuntu:~$ oq engine --lo <calc_id>
   id | name
   **3** | Disaggregation Outputs
   5 | Full Report
   6 | Realizations

Running ``--export-output`` to export the disaggregation results will
produce individual files for each site. In presence of a nontrivial
logic tree the user can specify the realization on which to perform
the disaggregation by setting the ``rlz_index`` parameter in the
``job.ini`` file. If not specified, the engine will compute the mean
disaggregation across all realizations. NB: before version 3.17 the
default algorithm used was different: only the realization closest to
the mean hazard curve was selected and used perform the
disaggregation. This was a choice forced by performance limitations
that do not apply to recent versions of the disaggregation calculator.