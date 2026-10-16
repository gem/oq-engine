.. _risk-calculations:

Risk Calculations
=================

Risk profiles
-------------

The OpenQuake engine can produce risk profiles, i.e. estimates of average
losses and maximum probable losses for all countries in the world. Even if you
are interested in a single country, you can still use this feature
to compute risk profiles for each province in your country.

However, the calculation of the risk profiles is tricky. Starting from
version 3.25 the recommended way is to first generate a common stochastic
event set and then run all calculations starting from it. In this way
events and ruptures are consistent for all countries.

You can compute the common stochastic event set by running an event
based calculation without specifying the sites and with the
parameter ``ground_motion_fields`` set to false. Currently, one
must specify a few global site parameters in the precalculation to
make the engine checker happy, but they will not be used since the
ground motion fields will not be generated in the
precalculation. The ground motion fields will be generated
on-the-fly in the subsequent individual country calculations, but
not stored in the file system.

Here are some tips on how to prepare the required job.ini files.
To be concrete, let's consider the 13 countries of South America.
You will have a hazard file to generate the Stochastic Event Set (SES)
as follows::

 $ cat job_SAM.ini 
 calculation_mode = event_based
 source_model_logic_tree_file = ssmLT.xml
 gsim_logic_tree_file = gmmLTrisk.xml
 site_model_file =
    Site_model_Argentina.csv
    Site_model_Bolivia.csv
    ...
 ground_motion_fields = false
 number_of_logic_samples = 2000
 ses_per_logic_tree_path = 1
 investigation_time = 50
 truncation_level = 3
 maximum_distance = 300

Notice that the site model files will not be used directly, since there
is no calculation of the GMFs involved in this phase. However, the
site model files will be imported and then the subsequent risk calculations
will be able to associate the exposure sites to the hazard sites and
to use the closest site parameters.

The engine will automatically concatenate the site model files for all
13 countries and produce a single site collection. It is FUNDAMENTAL
FOR PERFORMANCE to have reasonable site model files, i.e. you should
not compute the hazard at the location of every single asset, but
rather you should use a variable-size grid fitting the exposure.

The engine provides a command ``oq prepare_site_model``
which is meant to generate sensible site model files starting from
the country exposures and the global USGS vs30 grid.
It works by using a hazard grid so that the number of sites
can be reduced to a manageable number. Please refer to the manual in
the section about the oq commands to see how to use it, or try
``oq prepare_site_model --help``.

For reference, we were able to compute the hazard for all of South
America on a grid of half million sites and 1 million years of effective time
in a few hours in a machine with 120 cores, generating half terabyte of GMFs.

Then you will have 13 different risk files with a format like the following::

 $ cat job_Argentina.ini
 calculation_mode = event_based_risk
 exposure_file = Exposure_Argentina.xml
 structural_vulnerability_file = vulnerability.xml
 ...
 $ cat job_Bolivia.ini
 calculation_mode = event_based_risk
 exposure_file = Exposure_Bolivia.xml
 structural_vulnerability_file = vulnerability.xml
 ...

It should be mentioned that you are not forced to use a risk file
for each contry. In theory you could run the entire South America
in a single calculation, by simply specifying
the ``exposure_file`` as follows::

 exposure_file =
   Exposure_Argentina.xml
   Exposure_Bolivia.xml
   ...

The engine will automatically build a single asset collection for the
entire continent of South America. In order to use this approach, you
need to collect all the vulnerability functions in a single file and
the taxonomy mapping file must cover the entire exposure for all
countries. Moreover, the exposure must contain a field specifying
the country (in GEM's exposure models, this is typically
encoded in a field called ``ID_0``). Then the aggregation by country
can be done with the option

::

   aggregate_by = ID_0

There are however disadvantages of the single file approach:

1. if only the exposure of a country change, and not the others, you
   still have to recompute everything
2. for continental scale calculations it is very likely to run out of memory,
   so splitting by contry can be the only viable option.

Sometimes, one is interested in finer aggregations, for instance by country
and also by occupancy (Residential, Industrial or Commercial); then you have
to set

::

 aggregate_by = ID_0, OCCUPANCY
 reaggregate_by = ID_0

``reaggregate_by`` is a new feature of engine 3.13 which allows to go
from a finer aggregation (i.e. one with more tags, in this example 2)
to a coarser aggregation (i.e. one with fewer tags, in this example 1).
Actually the command ``oq reaggregate`` has been there for more than one
year; the new feature is that it is automatically called at the end of
a calculation, by spawning a subcalculation to compute the reaggregation.
Without ``reaggregate_by`` the aggregation by country would be lost,
since only the result of the finer aggregation would be stored.

Caveat: GMFs are split-dependent
--------------------------------

You should understand that splitting a calculation by
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

>>> np.random.default_rng(123456).normal(size=3)  # for Chile
array([ 0.1928212 , -0.06550702,  0.43550665])
>>> np.random.default_rng(123456).normal(size=2)  # for Argentina
array([ 0.1928212 , -0.06550702])

If you do not split, you will generate the following 5 random numbers
instead:

>>> np.random.default_rng(123456).normal(size=5)
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

For instructions on generating, reusing, and inspecting an SES datastore,
see :ref:`ses-workflows`.
