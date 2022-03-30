Risk profiles
=============

The OpenQuake engine can produce risk profiles, i.e. estimates of average losses
and maximum probable losses for all countries in the world. Even if you
are interested in a single country, you can still use this feature
to compute risk profiles for each province in your country.

However, the calculation of the risk profiles is tricky and there are
actually several different ways to do it.

1. The least-recommended way is to run independent calculations, one
   for each country. The issue with this approach is that even if the
   hazard model is the same for all the countries (say you are
   interested in the 13 countries of South America), due to the nature
   of event based calculations, different ruptures will be sampled in
   different countries. In practice, when comparing Chile with Peru you will
   see differences due to the fact that the random sampling picked
   different ruptures in the two contries and not real differences. In
   theory, the effect should disappear if the calculations have sufficiently
   long investigation times, when all possible ruptures are sampled, 
   but in practice, for finite investigation times there will always be 
   different ruptures.

2. To avoid such issues, the country-specific calculations should
   ideally all start from the same set of precomputed ruptures. You can
   compute the whole stochastic event set by running an event based
   calculation without specifying the sites and with the parameter
   ``ground_motion_fields`` set to false. Currently, one must specify
   a few global site parameters in the precalculation to make the
   engine checker happy, but they will not be used since the
   ground motion fields will not be generated in the
   precalculation. The ground motion fields will be generated on-the-fly  
   in the subsequent individual country calculations, but not stored 
   in the file system. This approach is fine if you do not have a lot of disk
   space at your disposal, but it is still inefficient since it is
   quite prone to the slow tasks issue.

3. If you have plenty of disk space it is better to also generate the
   ground motion fields in the precalculation, and then run the
   contry-specific risk calculations starting from there. This is
   particularly convenient if you foresee the need to run the risk
   part of the calculations multiple times, while the hazard part remains
   unchanged. Using a precomputed set of GMFs removes the need to rerun
   the hazard part of the calculations each time.

4. If you have a really powerful machine, the most efficient way is to
   run a single calculation considering all countries in a single
   job.ini file. The risk profiles can be obtained by using the
   ``aggregate_by`` and ``reaggregate_by`` parameters. This approach
   can be much faster than the previous ones. However, approaches #2
   and #3 are cloud-friendly and can be preferred if you have access
   to cloud-computing resources, since then you can spawn a different
   machine for each country and parallelize horizontally.

Here are some tips on how to prepare the required job.ini files:

When using approach #1 you will have 13 different files (in the example
of South America) with a format like the following::

 $ cat job_Argentina.ini
 calculation_mode = event_based_risk
 source_model_logic_tree_file = ssmLT.xml
 gsim_logic_tree_file = gmmLTrisk.xml
 site_model_file = Site_model_Argentina.csv
 exposure_file = Exposure_Argentina.xml
 ...
 $ cat job_Bolivia.ini
 calculation_mode = event_based_risk
 source_model_logic_tree_file = ssmLT.xml
 gsim_logic_tree_file = gmmLTrisk.xml
 site_model_file = Site_model_Bolivia.csv
 exposure_file = Exposure_Bolivia.xml
 ...

Notice that the ``source_model_logic_tree_file`` and ``gsim_logic_tree_file``
will be the same for all countries since the hazard model is the same;
the same sources will be read 13 times and the ruptures will be sampled
and filtered 13 times. This is inefficient. Also, hazard parameters like

::

 truncation_level = 3
 investigation_time = 1
 number_of_logic_tree_samples = 1000
 ses_per_logic_tree_path = 100
 maximum_distance = 300

must be the same in all 13 files to ensure the consistency of the
calculation. Ensuring this consistency can be prone to human error.

When using approach #2 you will have 14 different files: 13 files for
the individual countries and a special file for precomputing the ruptures::

 $ cat job_rup.ini 
 calculation_mode = event_based
 source_model_logic_tree_file = ssmLT.xml
 gsim_logic_tree_file = gmmLTrisk.xml
 reference_vs30_value = 760
 reference_depth_to_1pt0km_per_sec = 440
 ground_motion_fields = false
 ...

The files for the individual countries will be as before, except for
the parameter ``source_model_logic_tree_file`` which should be
removed. That will avoid reading 13 times the same source model files,
which are useless anyway, since the calculation now starts from
precomputed ruptures. There are still a lot of repetitions in the
files and the potential for making mistakes.

Approach #3 is very similar to approach #2: the only differences will be
in the initial file, the one used to precompute the GMFs. Obviously it
will require setting ``ground_motion_fields = true``; moreover, it will
require specifying the full site model as follows::

  site_model_file =
    Site_model_Argentina.csv
    Site_model_Bolivia.csv
    ...

The engine will automatically concatenate the site model files for all
13 countries and produce a single site collection. The site parameters
will be extracted from such files, so the dummy global parameters
``reference_vs30_value``, ``reference_depth_to_1pt0km_per_sec``, etc
can be removed.

It is FUNDAMENTAL FOR PERFORMANCE to have reasonable site model files,
i.e. the number of sites must be relatively small, let's say below
100,000 sites. For calculations with large high-definition exposure models,
trying to calculate the hazard at the location of every single asset
can easily generate millions of sites, making the calculation intractable
in terms of both memory and disk space occupation.

The engine provides a command ``oq prepare_site_model``
which is meant to generate sensible site model files starting from
the country exposures and the global USGS vs30 grid.
It works by using a hazard grid so that the number of sites
can be reduced to a manageable number. Please refer to the manual in
the section about the oq commands to see how to use it, or try
``oq prepare_site_model --help``.

Approach #4 is the best, since there is only a single file,
thus avoiding entirely the possibily of having inconsistent parameters
in different files. It is also the faster approach, not to mention the
most convenient one, since you have to manage a single calculation and
not 13. That makes the task of managing any kind of post-processing a lot
simpler. Unfortunately, it is also the option that requires more
memory and it can be infeasable if the model is too large and you do not
have enough computing resources. In that case your best bet might be to
go back to options #2 or #3. If you have access to multiple small machines,
approaches #2 and #3 can be more attractive than #4, since then you 
can scale horizontally. If you decide to use approach #4, 
in the single file you must specify the ``site_model_file`` as done in
approach #3, and also the ``exposure_file`` as follows::

 exposure_file =
   Exposure_Argentina.xml
   Exposure_Bolivia.xml
   ...

The engine will automatically build a single asset collection for the
entire continent of South America. In order to use this approach, you need to
collect all the vulnerability functions in a single file and the
taxonomy mapping file must cover the entire exposure for all countries. 
Moreover, the exposure must contain the associations between 
asset<->country; in GEM's exposure models, this is typically encoded 
in a field called ``ID_0``. Then the aggregation by country can be done with the option

::

   aggregate_by = ID_0

Sometimes, one is interested in finer aggregations, for instance by country
and also by occupancy (Residential, Industrial or Commercial); then you have
to set

::

 aggregate_by = ID_0, OCCUPANCY
 reaggregate_by = ID_0

``reaggregate_by` is a new feature of engine 3.13 which allows to go
from a finer aggregation (i.e. one with more tags, in this example 2)
to a coarser aggregation (i.e. one with fewer tags, in this example 1).
Actually the command ``oq reaggregate`` has been there for more than one
year; the new feature is that it is automatically called at the end of
a calculation, by spawning a subcalculation to compute the reaggregation.
Without ``reaggregate_by`` the aggregation by country would be lost,
since only the result of the finer aggregation would be stored.

Single-line commands
--------------------

When using approach #1 your can run all of the required calculations
with the command::

 $ oq engine --multi --run job_Argentina.csv job_Bolivia.csv ...

When using approach #2 your can run all of the required calculations
with the command::

 $ oq engine --run job_rup.ini job_Argentina.csv job_Bolivia.csv ...

When using approach #3 your can run all of the required calculations
with the command::

 $ oq engine --run job_gmf.ini job_Argentina.csv job_Bolivia.csv ...

When using approach #4 your can run all of the required calculations
with the command::

 $ oq engine --run job_all.ini

Here ``job_XXX.ini`` are the country specific configuration files,
``job_rup.ini`` is the file generating the ruptures, ``job_rup.ini``
is the file generating the ruptures, ``job_gmf.ini`` is the file
generating the ground motion files and ``job_all.ini`` is the
file encompassing all countries.

Finally, if you have a file ``job_haz.ini`` generating the full GMFs,
a file ``job_weak.ini`` generating the losses with a weak building code
and a file ``job_strong.ini`` generating the losses with a strong building
code, you can run the entire an analysis with a single command as follows::

 $ oq engine --run job_haz.ini job_weak.ini job_strong.ini

This will generate three calculations and the GMFs will be reused.
This is as efficient as possible for this kind of problem.

Caveat: GMFs are split-dependent
--------------------------------

You should not expect the results of approach #4 to match exactly the
results of approaches #3 or #2, since splitting a calculation by
countries is a tricky operation. In general, if you have a set of
sites and you split it in disjoint subsets, and then you compute the
ground motion fields for each subset, you will get different results
than if you do not split.

To be concrete, if you run a calculation for Chile and then one for
Argentina, you will get different results than running a single
calculation for Chile+Argentina, *even if you have precomputed the
ruptures for both countries, even if the random seeds are the same and
even if there is no spatial correlation*. Many users are surprised but
this fact, but it is obvious if you know how the GMFs are
computed. Suppose you are considering 3 sites in Chile and 2 sites in
Argentina, and that the value of the random seed in 123456: if you
split, assuming there is a single event, you will produce the
following 3+2 normally distributed random numbers:

>>> numpy.random.default_rng(123456).normal(size=3)  # for Chile
array([ 0.1928212 , -0.06550702,  0.43550665])
>>> numpy.random.default_rng(123456).normal(size=2)  # for Argentina
array([ 0.1928212 , -0.06550702])

If you do not split, you will generate the following 5 random numbers
instead:

>>> numpy.random.default_rng(123456).normal(size=5)
array([ 0.1928212 , -0.06550702,  0.43550665,  0.88235875,  0.37132785])

They are unavoidably different. You may argue that not splitting is
the correct way of proceeding, since the splitting causes some
random numbers to be repeated (the numbers 0.1928212 and -0.0655070
in this example) and actually breaks the normal distribution.

In practice, if there is a sufficiently large event-set and if you are
interested in statistical quantities, things work out and you should
see similar results with and without splitting. But you will
*never produce identical results*. Only the classical calculator does
not depend on the splitting of the sites, for event based and scenario
calculations there is no way out.
