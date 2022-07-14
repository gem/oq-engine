Secondary perils: a case study
==============================

Secondary perils (such as liquefaction and landslides) are a new
feature of the engine. In this section we will give an example of how
to use the feature by considering a model for the city of Cali in
Colombia.

The exposure and all the relevant files are in the repository
https://gitlab.openquake.org/risk/risk_projects/treq/treq-city-scenarios.git/
in the branch fix_liquefaction, commit
5479f19b6eee56ed59beed030c0cb31de6d7298b

The .ini file is called job_Cali_liquefaction.ini and corresponds to a
scenario_damage calculation starting from a rupture which parameters
are stored in a CSV file::

 seed,mag,rake,lon,lat,dep,multiplicity,trt,kind,mesh,extra
 2288985983,8.45,90,-77.80971,3.61968,19.75614,1,Subduction Interface,ParametricProbabilisticRupture ComplexFaultSurface,...,...

The rupture was obtained from a pre-existing event based hazard calculation.

There is also a site model file containing 4,168 sites: these are the
sites where the GMFs will be computed (actually only 4,152 sites will
be considered since on some of them there are no assets within the
``asset_hazard_distance``, which has a default of 15 km).

Since the parameter `number_of_ground_motion_fields` is set to 100 and
there are 3 GMPEs in the GMPE logic tree (AbrahamsonEtAl2015SInter,
ZhaoEtAl2006SInterNSHMP2008, MontalvaEtAl2016SInter) the engine will
produce 300 events.

The exposure contains 348,471 assets of 813 distinct taxonomies.

The .ini file contains two secondary perils::

  secondary_perils = HazusLiquefaction, HazusDeformation

On the hazard side such perils are managed as additional columns in
the GMF table, named ``LiqProb`` and ``PGDMax`` respectively. The
liquefaction fragility functions are associated to ``PGDMax`` and
contain a single damage state called "complete", meaning complete
distruction of the asset. All the rest is considered in "no damage"
state.

On the risk side the engine implements two different strategies,
depending on the parameter ``discrete_damage_distribution``. If false
(the default) we simply multiply the damage distributions computed
from the fragility functions for the liquefaction probabilities,
event by event.

If true, then for each site the engine performs a number of secondary
simulations, specified in the job.ini as

``secondary_simulations = {'LiqProb': 10}``

and builds an array of booleans of size (E, S) where E is the number
of events (primary simulations) and S the number of secondary
simulations (the array would have a size of 300x10 in our case).  The
true values in the array will be determined by the master seed and the
liquefaction probabilities; for instance, if a site has liquefaction
probability of 0.2 an you run 10 simulations, you will produce around
2 ones and 8 zeros for each event. The mean damage distributions
across the secondary simulations are computed and stored for each
event. At the present, for performance and storage considerations, the
secondary simulations are not stored. In the future this may change as
storing the secondary simulations is needed in order to compute
consequence curves in event_based_damage calculations. In such an
extension the ``risk_by_event`` table will have an additional column
with a simulation ID on top of the event ID.

If you want to know more, the original specs for the calculator are here:
https://github.com/gem/oq-engine/issues/6081

Understanding the hazard
------------------------

The first thing to do in order to assess the reliability of the
results is to assess the reliability of the hazard. Running the
calculation with ``calculation_mode=scenario`` will generate and store
a set of 100x3 GMFs, one for each simulated event. Unfortunately the
engine will give the following scary warning::

  [WARNING] Your results are expected to have a large dependency from ses_seed (or the rupture seed in scenarios): 11%

It means that the variability in the GMFs will be
large, i.e. that the parameter `number_of_ground_motion_fields=100` is
set to a value too small for having statistical significance. *This
does not mean that you should blindly increase it*: since the
precision in a Montecarlo calculation goes with the inverse square
root of the number of simulations, it is very difficult to improve the
precision without making the calculation too large to be tractable,
especially on the risk side. For instance in this example a call to
``oq show performance`` gives::

 | calc_3901, maxmem=1.5 GB | time_sec  | memory_mb | counts |
 |--------------------------+-----------+-----------+--------|
 | total compute_gmfs       | 25.2      | 89.5      | 1      |

i.e. computing the GMFs took 25.2 seconds and 89.5 MB of RAM. In order
to increase by 10 times the precision we will have to use 100 times
more time and 100 times more memory and then the risk will probably
become intractable. Also the size of the GMFs table will increase 100
times (and it has already 1_245_600 rows) increasing the probability
of running out of disk space.

So, it is better to keep ``number_of_ground_motion_fields`` small and
to go on. The number of simulations should be increased *only as last
step*, when the calculation is understood, not before starting the
analysis. The first step, knowing that there will be a large
variability in the GMFs is to understand how big the variability will
be. The engine provided such information in the output called
``avg_gmf`` which as actually computing mean and standard deviations
with respect to the events for the GMFs in logspace. Exporting such
output in CSV will give the following results::

 site_id,lon,lat,gmv_PGA,gsd_PGA
 0,-7.65409E+01,3.35016E+00,2.02698E-01,2.10337E+00
 1,-7.65448E+01,3.35064E+00,1.95601E-01,2.17038E+00
 2,-7.65281E+01,3.34655E+00,1.68315E-01,1.86514E+00
 3,-7.65299E+01,3.35663E+00,1.78430E-01,2.09011E+00
 4,-7.65279E+01,3.35160E+00,1.85109E-01,1.97229E+00
 ...

The field ``gmv_PGA`` is the exponential of the mean ground motion in
log space (i.e. the geometric mean) and the field ``gsd_PGA`` is the
exponential of the standard deviation in log space (called the
geometric standard deviation). In practice for site 0 the geometric
mean of the ground motion is 0.202698 g with a huge gsd of
2.010337 g. It means that changing the seed will produce very
different GMFs. Indeed, if we modify the rupture file, change the seed
slightly

``seed = 2288985983 -> 2288985984``

and repeat the calculation will will get for ``avg_gmf`` the following results::

 site_id,lon,lat,gmv_PGA,gsd_PGA
 0,-7.65409E+01,3.35016E+00,1.85170E-01,2.13215E+00
 1,-7.65448E+01,3.35064E+00,1.86119E-01,1.97122E+00
 2,-7.65281E+01,3.34655E+00,1.74637E-01,2.07151E+00
 3,-7.65299E+01,3.35663E+00,1.76338E-01,2.12016E+00
 4,-7.65279E+01,3.35160E+00,1.86024E-01,2.17961E+00

The site 0 that had a value of 0.202698 g has now a value of 0.18517 g, a ~10% difference.

If we increase the ``number_of_ground_motion_fields`` by 100 times
(i.e. to 10,000) we would expect to increase the precision by 10
times. Actually by performing the calculation and by exporting the
``avg_gmf`` output we will see that is the case indeed. Here are
the results of two runs with seed 22889859843 and 2288985984 respectively::

 site_id,lon,lat,gmv_PGA,gsd_PGA
 0,-7.65409E+01,3.35016E+00,1.88047E-01,2.07915E+00
 1,-7.65448E+01,3.35064E+00,1.87098E-01,2.09691E+00
 2,-7.65281E+01,3.34655E+00,1.86678E-01,2.10286E+00
 3,-7.65299E+01,3.35663E+00,1.86075E-01,2.12381E+00
 4,-7.65279E+01,3.35160E+00,1.85069E-01,2.09404E+00

 site_id,lon,lat,gmv_PGA,gsd_PGA
 0,-7.65409E+01,3.35016E+00,1.87952E-01,2.10219E+00
 1,-7.65448E+01,3.35064E+00,1.90115E-01,2.09527E+00
 2,-7.65281E+01,3.34655E+00,1.87923E-01,2.08300E+00
 3,-7.65299E+01,3.35663E+00,1.88070E-01,2.09264E+00
 4,-7.65279E+01,3.35160E+00,1.86382E-01,2.08344E+00

The seed-dependency is indeed ~10 times smaller, however notice how bad the performance is (100x slower)::

 | calc_3909, maxmem=2.2 GB | time_sec  | memory_mb | counts |
 |--------------------------+-----------+-----------+--------|
 | total compute_gmfs       | 2_391     | 3_815     | 1      |

Moreover the memory occupation is much worse (the calculation requires
~30 GB of RAM) and that make impossible to run the calculation on most
laptops/desktops.

Understanding the risk
------------------------

Since this is a ``scenario_damage`` calculation, the best way to
understand the reliabily of the results due to the Montecarlo errors
is to look at the seed-dependency of the portfolio damage
distributions (there will be three of them, one for each GMPE).  They
can be obtained by exporting the output "aggrisk"::

 loss_type,rlz_id,no_damage,complete
 structural,0,3.46780E+05,1.91884E+03
 structural,1,3.46960E+05,1.73882E+03
 structural,2,3.45961E+05,2.73800E+03

Then after changing the seed 2288985983 -> 2288985984 and re-running
the same command we will get::

 loss_type,rlz_id,no_damage,complete
 structural,0,3.46964E+05,1.73549E+03
 structural,1,3.47112E+05,1.58696E+03
 structural,2,3.46181E+05,2.51764E+03

For instance for the first realization (i.e. the first GMPE) the
estimated number of destroyed buildings changes from ~1919 to ~1735,
which is a difference around ~10%.

This is consistent with the hazard analysis and it is good news: a 10%
Montecarlo error is quite acceptable. It could be reduced to a 5% buy
increasing by 4 times the number of simulations; more than that is
probably not worth the effort, since the calculation would become too
expensive to run for a minor benefit.

NB: in order to obtain the correspondence between the realization ID
and the associated GMPE you can use the command

::
   
 $ oq show branches
 | branch_id | abbrev | gsim                          |
 |-----------+--------+-------------------------------|
 | b0        | 0      | [AbrahamsonEtAl2015SInter]    |
 | b1        | 1      | [ZhaoEtAl2006SInterNSHMP2008] |
 | b2        | 2      | [MontalvaEtAl2016SInter]      |
