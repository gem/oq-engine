Event based computations with complex logic trees and sampling
---------------------------------------------------------------------------

Let me give a few formal definitions: a logic tree is *trivial* if it has a
single GSIM per tectonic region type; it is *simple* if has more than one
GSIM but only one tectonic region type per source model;
it is *complex* if it has more than one tectonic region type and more
than one GSIM.

If the GMPE logic tree is simple there one-to-one correspondence
between ses collections and realizations; otherwise there
a correspondence many-to-one, i.e. many different collections
correspond to the same realization or, in other terms, a realization
has contributions from different ses collections.

The case of an event based calculation with sampling of the logic
tree is particularly difficult. To explain how it works, I will
show a couple of examples. Let's start from our test
`event_based/case_7`_.

This is a rather simple test. There are two source models; both
of them contain a single source, which actually is the same area source with
two different magnitudes. The GMPE logic tree is trivial since
each model has a single tectonic region type ("Active Shallow Crust");
still, the reduction of the complete logic tree can happen if one
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

I should also notice that the effective realizations produced by an
event based calculation are not necessarily the same as the one
produced by an equivalent classical calculation. If you are unlucky,
for a given set of parameter, a tectonic region type producing
ruptures in the classical calculation could *not* produce ruptures in the
corresponding event based calculation.  The consequence is the event
based calculation can have less effective realizations than the
classical calculation. However, in the limit of many samples/many SES,
all tectonic regions which are relevant for the classical calculation
should produce ruptures for the event based calculation too.
