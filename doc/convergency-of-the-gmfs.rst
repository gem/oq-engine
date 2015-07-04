Event based computations with complex logic trees
-------------------------------------------------

Previously_ we discussed the concept of effective realizations and
logic tree reduction. All we said was correct for the case of
classical calculations. However, in the case of event based calculations
there is an additional complication:

*because of the stochasticity of the rupture-generation process, a tectonic
region type which contains sources, could produce zero ruptures*.

In other words, depending on the parameters of the calculation, notably
the investigation time and the number of stochastic event sets, a logic
tree could be further reduced with respect to the logic tree of the
equivalent classical calculation.

This has substantial performance implications; for instance a logic
tree that on the surface looks complex, could actually be simple or
even trivial, thus computationally much less intensive. This can be
good or bad: for instance, if you are running a simplified calculation
with a small number of stochastic event sets, as a prototype of a
larger calculation, you may run into logic tree reduction and having
a smaller runtime than expected: the prototype will not be significant
for the performance of the real computation.

For an event based calculation it is impossible to assess the
complexity of a logic tree without having computed the ruptures first.
The `oq-lite info` command does that only if you use it in conjunction
with the ``-d`` flag. In other words, in the case of an event based
calculation you should always run

`$ oq-lite info -d job.ini`

to get the correct reduced logic tree and effective realizations.
It will be slower than just filtering the sources but reliable.
As an additional bonus, you will also get some information about
the expected data transfer.

__ Previously_: effective-realizations.rst


The concept of rupture collection
-----------------------------------------------------------

Event based calculations differ from classical calculations because
they produce visible ruptures, which can be exported and
made accessible to the user. On the contrary, in a classical calculation
the underlying ruptures only live in memory and are never saved in
the datastore, nor are exportable. The limitation is fundamentally
a technical one: in the case of an event based calculation only
a small fraction of the ruptures contained in a source are actually
generated, so it is possible to store them. In a classical calculation
*all* ruptures are generated and there are so many millions of them
that it is impractical to save them. For this reason they live in memory, they
are used to produce the hazard curves and immediately discarded
right after. Perhaps in the future we will be able to overcome the
technical limitations and to store the ruptures also for classical
calculations; at the moment it is not so. Therefore here we will
only document how the ruptures are stored for event based calculations.

Because the computation is organized by tectonic region model
the ruptures are naturally organized by tectonic region model.
In the case of full enumeration there is a one-to-one
correspondence between rupture collections and tectonic region
models. In the case of sampling, instead, there is a many-to-one
correspondence, i.e. multiple rupture collections are associated
to the same tectonic region model. The number is given by the
number of samples for the source model to which the tectonic region
model belongs. The total number of rupture collections is

 `sum(num_tectonic_region_models * num_samples for sm in source_models)`

The number of collections is greater (or equal) than the number of
realizations; it is equal only when the number of tectonic region
models per source model is 1.

An example with a large logic tree (full enumeration)
-----------------------------------------------------

Here we will show the concept of rupture collection works in practice
in a SHARE-like calculation. We will consider the example of our QA
test *qa_tests_data.event_based_risk.case_4*. This is an artificial
test, obtained by a real computation for Turkey by reducing a lot
the source model and the parameters (for instance the investigation
time is 10 years whereas originally it was 10,000 years) so that
it can run in less than a minute but still retains some of the
complexities of the original calculation. It is also a perfect
example to explain the intricacies of the logic tree reduction.

If you run `oq-lite info -d` on that example you will get a number of
warning messages, such as::
  
  WARNING:root:Could not find sources close to the sites in models/src/as_model.xml sm_lt_path=('AreaSource',), maximum_distance=200.0 km, TRT=Shield
  WARNING:root:Could not find sources close to the sites in models/src/as_model.xml sm_lt_path=('AreaSource',), maximum_distance=200.0 km, TRT=Subduction Interface
  WARNING:root:Could not find sources close to the sites in models/src/as_model.xml sm_lt_path=('AreaSource',), maximum_distance=200.0 km, TRT=Subduction IntraSlab
  WARNING:root:Could not find sources close to the sites in models/src/as_model.xml sm_lt_path=('AreaSource',), maximum_distance=200.0 km, TRT=Volcanic
  WARNING:root:Could not find sources close to the sites in models/src/as_model.xml sm_lt_path=('AreaSource',), maximum_distance=200.0 km, TRT=Stable Shallow Crust

Such warnings comes from the source filtering routine. They simply tell us that
a lot of tectonic region types will not contribute to the logic tree because
they are being filtered away. Later warnings are even more explicit::
  
   WARNING:root:Reducing the logic tree of models/src/as_model.xml from 640 to 4 realizations
   WARNING:root:Reducing the logic tree of models/src/fsbg_model.xml from 40 to 4 realizations
   WARNING:root:Reducing the logic tree of models/src/ss_model.xml from 4 to 0 realizations
   WARNING:root:No realizations for SeiFaCrust, models/src/ss_model.xml
   WARNING:root:Some source models are not contributing, weights are being rescaled


This is a case where an apparently complex logic tree has been reduced
to a simple one. The full logic tree is composed by three GMPE logic
trees, one for each source model. The first one (for sources coming
from the file *as_model.xml*) has been reduced from 640 potential
realizations to 4 effective realizations; the second one (for sources
coming from the file *fsbg_model.xml*) has been reduced from 40
potential realizations to 4 effective realizations; the last one (for
sources coming from the file *ss_model.xml*) has been completely
removed, since after filtering there are no sources compling from
*ss_model.xml*, aka the SeiFaCrust model. So, there are no effective
realizations belonging to it and the weights of the source model logic
tree have to be rescaled, otherwise their sum would not be one. The
composition of the composite source model, after filtering and rupture
generation becomes::

  <CompositionInfo
  AreaSource, models/src/as_model.xml, trt=[0, 1, 2, 3, 4, 5], weigth=0.500: 4 realization(s)
  FaultSourceAndBackground, models/src/fsbg_model.xml, trt=[6, 7, 8, 9], weigth=0.200: 4 realization(s)
  SeiFaCrust, models/src/ss_model.xml, trt=[10], weigth=0.300: 0 realization(s)>


An example with sampling
---------------------------------------------------
  
To explain how it works, I will show as an example our test
`event_based/case_7`_.

This is a rather simple test. There are two source models; both
of them contain a single source, which actually is the same area source with
two different magnitudes. The GMPE logic tree is trivial since
each model has a single tectonic region type ("Active Shallow Crust").
The reduction of the complete logic tree can happen if one
of the source models is not sampled or if one of the source models
produces no ruptures for some configuration of the parameters.

Given the parameters in the test (number_of_logic_tree_samples=100,
random_seed=23, weight of the first model 0.6, weight of the second
model 0.4), the first source model is sampled 63 times and the second
one 37 times. With 10 stochastic event sets (
ses_per_logic_tree_path=10) we are generating the following ruptures
per source model:

source_model1.xml: 30,457
source_model2.xml: 1,772

Actually there are 100 SES collections, each one generating different
number of ruptures:

first model: {480,535,462,457,473,524,510,512,448,463,486,471,529,515,473,464,457,467,498,483,477,477,462,470,489,476,489,471,466,478,449,484,531,471,483,493,506,461,465,477,481,509,483,491,470,488,451,480,461,470,524,501,504,471,501,495,461,490,498,449,484,497,516} # 63 col_ids
second model: {47,57,57,57,48,55,47,50,46,45,45,53,56,35,35,52,41,51,52,36,54,48,46,47,49,49,34,48,43,48,44,44,55,42,52,51,53}  # 37 col_ids



.. _event_based/case_7: https://github.com/gem/oq-risklib/tree/master/openquake/qa_tests_data/event_based/case_7

Reduction of the logic tree when sampling is enabled
----------------------------------------------------

There are real life examples of very complex logic trees, even with
more than 400,000 branches. In such situations it is impossible to perform
a full computation. However, the engine allows to
sample the branches of the complete logic tree. More precisely,
for each branch sampled from the source model logic
tree a branch of the GMPE logic tree is chosen randomly,
by taking into account the weights in the GMPE logic tree file.

Suppose for instance that we set

  `number_of_logic_tree_samples = 4000`

to sample 4,000 branches instead of 400,000. The expectation is that
the computation will be 100 times faster. This is indeed the case for
the classical calculator. However, for the event based calculator
things are different. The point is that each sample of the source
model must produce different ruptures, even if there is only one
source model repeated 4,000 times, because of the inherent
stochasticity of the process. Therefore the time spent in generating
the needed amount of ruptures could make the calculator slower than
using full enumeration: remember than when using full enumeration the
ruptures of a given source model are generated exactly once, since
each path is taken exactly once.

Notice that even if source model path is sampled several times, the
model is parsed and sent to the workers *only once*. In particular if
there is a single source model and `number_of_logic_tree_samples =
4000`, we generate effectively 1 source model realization and not
4,000 equivalent source model realizations, as we did in past
(actually in the engine version 1.3).  Then engine keeps track of how
many times a model has been sampled (say `N`) and in the event based
case it produce ruptures (*with different seeds*) by calling the
appropriate hazardlib function `N` times. This is done inside the
worker nodes. In the classical case, all the ruptures are identical
and there are no seeds, so the computation is done only once, in an
efficient way.


Convergency of the GMFs for non-trivial logic trees
---------------------------------------------------------------------------

In theory, the hazard curves produced by an event based calculation
should converge to the curves produced by an equivalent classical
calculation. In practice, if the parameters
`number_of_logic_tree_samples` and `ses_per_logic_tree_path` (the
product of them is the relevant one) are not large enough they may be
different. The `oq-lite` version of the engine is able to compare
the mean hazard curves and to see how well they converge. This is
done automatically if the option `mean_hazard_curves = true` is set.
Here is an example of how to generate and plot the curves for one
of our QA tests (a case with bad convergence was chosen on purpose)::

 $ oq-lite run event_based/case_7/job.ini
 <snip>
 WARNING:root:Relative difference with the classical mean curves for IMT=SA(0.1): 51%
 WARNING:root:Relative difference with the classical mean curves for IMT=PGA: 49%
 <snip>
 $ oq-lite plot /tmp/cl/hazard.pik /tmp/hazard.pik --sites=0,1,2

.. image:: ebcl-convergency.png

The relative different between the classical and event based curves is
computed by computing the relative difference between each point of
the curves for each curve, and by taking the maximum, at least
for probabilities of exceedence larger than 1% (for low values of
the probability the convergency may be bad). For the details I
suggest you `to look at the code`_.

.. _to look at the code: ../openquake/commonlib/util.py

As we said before, the effective realizations produced by an
event based calculation are not necessarily the same as the one
produced by an equivalent classical calculation. If you are unlucky,
for a given set of parameter, a tectonic region type producing
ruptures in the classical calculation could *not* produce ruptures in the
corresponding event based calculation.  The consequence is the event
based calculation can have less effective realizations than the
classical calculation. However, in the limit of many samples/many SES,
all tectonic regions which are relevant for the classical calculation
should produce ruptures for the event based calculation too.
