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
