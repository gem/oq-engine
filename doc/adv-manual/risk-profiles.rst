Risk profiles
=======================

GEM is able to produce risk profiles, i.e. estimates of average losses
and maximum probable losses for all countries in the world. Even if you
are interested in a single country, you can still use this feature
to compute risk profiles for each province in your country.

However, the calculation of the risk profiles is tricky and there are
actually several different ways to do it.

1. The least-recommended way is to run indipendent calculations, one
   for each country. The issue with this approach is that even if the
   hazard model is the same for all the countries (say you are
   interested in the 13 countries in South America) due to the nature
   of event based calculations different ruptures will be sampled in
   different countries. In practice, when comparing Chile with Peru you will
   see differences due to the fact that the random sampling picked
   different ruptures in the two contries and not real differences. In
   theory the effect should disappear for long investigation times,
   when all possible ruptures are samples, but in practice for finite
   investigation times there will always be different ruptures.

2. To avoid such issue the contry-specific calculation must all start
   from the same set of ruptures, precomputed in advance. You can
   compute the whole stochastic event set by running an event based
   calculation without specifying the sites and with the parameter
   ``ground_motion_fields`` set to false. Currently one must specify
   a few global site parameters in the precalculation to make the
   engine checker happy, but they will not be used since since the
   ground motion fields will not be generated in the
   precalculation. They will be generated in the subsequent
   individual calculations, but on-the-fly and not stored in the file
   system. This approach is fine if you do not have a lot of disk
   space at your disposal, but it is still inefficient since it is
   more prone to the slow task issue.

3. If you have plenty of disk space it is better to generate the
   ground motion fields in the precalculation and then run the
   contry-specific calculations starting from there. This is
   particularly convenient if you have to run the risk part of the
   calculations multiple times. A typical use case is to use
   different vulnerability functions (for instance to compare a
   strong building code versus a weak building code). Having
   precomputed the GMFs means that you do not have to recompute them
   twice.

4. If you have a really powerful machine the most efficient way is to
   run a single calculation considering all countries in a single job.ini
   file. The risk profiles can be obtained by using the ``aggregate_by``
   and ``reaggregate_by`` parameters. This approach can be much faster than the
   previous ones. However, approaches #2 and #3 are cloud-friendly and
   can be preferred if you have access to cloud-computing resources,
   since then you can spawn a different machine for each country and
   parallelize horizontally.

Here are some tips on how to prepare the required job.ini files.

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
 ses_per_logic_tree_path = 1
 maximum_distance = 300

must be the same in all 13 files to ensure the consistency of the
calculation. This is error prone.

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
the parameters ``source_model_logic_tree_file`` and ``gsim_logic_tree_file``,
that should be removed. That will avoid reading 13 times the same source
model files, which are useless anyway, since the calculation now starts from
precomputed ruptures. There are still a lot of repetitions in the files
and the potential for making mistakes.

Approach #3 is very similar to approach #2: the only differences will be
in the initial file, the one used to precompute the GMFs. Obviously it
will require setting ``ground_motion_fields = true``; moreover, it will
require specifying the full site model as follows::

  site_model_file =
    Site_model_Argentina.csv
    Site_model_Bolivia.csv
    ...

The engine will automatically concatenate the site model files for all
13 countries a produce a single site collection. The site parameters
will be extracted from such files, so the dummy global parameters
``reference_vs30_value``, ``reference_depth_to_1pt0km_per_sec``, etc
can be removed.

It is FUNDAMENTAL FOR PERFORMANCE to have reasonable site model files,
i.e. the number of sites must be relatively small, let's say below
100,000 sites. The most common error is wanting to use the sites of
the exposure, but this can easily generate tens of millions of sites
making the calculation impossible in terms of both memory and disk space
occupation.

The engine provides a command ``oq prepare_site_model``
which is meant to generate sensible site model files starting from
the country exposures and the USGS vs30 file for the entire world.
It works by using a hazard grid so that the number of sites
can be reduced to a manageable number. Please look in the manual in
the section about the oq commands to see how to use it.

Approach #4 is the best, since there is only a single file,
thus avoiding entirely the possibily of having inconsistent parameters
in different files. It is also the faster approach, not to mention the
most convenient one, since you have to manage a single calculation and
not 13. That makes any kind of post-processing analysis a lot
simpler. Unfortunately, it is also the option that requires more
memory and it can be unfeasable if the model is too big and you do not
have enough IT resources: in that case you must go back to options #2
or #3. If you have access to multiple small machines approaches #2 and
#3 can be more attractive than #4, since then you can scale horizontally.
If you decide to use approach #4, in the single file you must specify
the ``site_model_file`` as done in the approach #3, and also the
``exposure_file`` as follows::

 exposure_file =
   Exposure_Argentina.xml
   Exposure_Bolivia.xml
   ...

The engine will automatically build a single asset collection for the
entire South America; the associations asset->country are normally
encoded in a field in the exposure called ``ID_0`` and the aggregation
by country can be done with the option

::

   aggregate_by = ID_0

Sometimes one is interested in finer aggregations, for instance by country
and also by occupancy (Residential, Industrial or Business); then you have
to set

::

 aggregate_by = ID_0, OCCUPANCY
 reaggregate_by = ID_0

``reaggregate_by` is a new feature of engine 3.13 which allows to go
from a fine aggregation (i.e. one with more tags, in this example 2)
to a raw aggregation (i.e. one with less tags, in this example 1).
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
