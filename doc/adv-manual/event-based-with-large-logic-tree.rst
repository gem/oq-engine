Extra tips specific to event based calculations
===============================================

Event based calculations differ from classical calculations because
they produce visible ruptures, which can be exported and made
accessible to the user. In classical calculations, instead,
the underlying ruptures only live in memory and are normally not saved
in the datastore, nor are exportable. The limitation is fundamentally
a technical one: in the case of an event based calculation only a
small fraction of the ruptures contained in a source are actually
generated, so it is possible to store them. In a classical calculation
*all* ruptures are generated and there are so many millions of them
that it is impractical to save them, unless there are very few sites.
For this reason they live in memory, they are used to produce the
hazard curves and immediately discarded right after. The exception if
for the case of few sites, i.e. if the number of sites is less than
the parameter ``max_sites_disagg`` which by default is 10.


Sampling of the logic tree
----------------------------------------------------

There are real life examples of very complex logic trees, like the model
for South Africa which features 3,194,799,993,706,229,268,480 branches.
In such situations it is impossible to perform
a full computation. However, the engine allows to
sample the branches of the complete logic tree. More precisely,
for each branch sampled from the source model logic
tree a branch of the GMPE logic tree is chosen randomly,
by taking into account the weights in the GMPE logic tree file.

The details of how the sampling works are `documented here`_:

.. _documented here: sampling.hmtl

It should be noticed that even if source model path is sampled several
times, the model is parsed and sent to the workers *only once*. In
particular if there is a single source model (like for South America)
and ``number_of_logic_tree_samples =100``, we generate effectively 1
source model realization and not 100 equivalent source model
realizations, as we did in past (actually in the engine version 1.3).
The engine keeps track of how many times a model has been sampled (say
`Ns`) and in the event based case it produce ruptures (*with different
seeds*) by calling the appropriate hazardlib function `Ns` times. This
is done inside the worker nodes. In the classical case, all the
ruptures are identical and there are no seeds, so the computation is
done only once, in an efficient way.


Convergency of the GMFs for non-trivial logic trees
---------------------------------------------------------------------------

In theory, the hazard curves produced by an event based calculation
should converge to the curves produced by an equivalent classical
calculation. In practice, if the parameters
``number_of_logic_tree_samples`` and ``ses_per_logic_tree_path`` (the
product of them is the relevant one) are not large enough they may be
different. The engine is able to compare
the mean hazard curves and to see how well they converge. This is
done automatically if the option ``mean_hazard_curves = true`` is set.
Here is an example of how to generate and plot the curves for one
of our QA tests (a case with bad convergence was chosen on purpose)::

 $ oq engine --run event_based/case_7/job.ini
 <snip>
 WARNING:root:Relative difference with the classical mean curves for IMT=SA(0.1): 51%
 WARNING:root:Relative difference with the classical mean curves for IMT=PGA: 49%
 <snip>
 $ oq plot /tmp/cl/hazard.pik /tmp/hazard.pik --sites=0,1,2

.. image:: ebcl-convergency.png

The relative difference between the classical and event based curves is
computed by computing the relative difference between each point of
the curves for each curve, and by taking the maximum, at least
for probabilities of exceedence larger than 1% (for low values of
the probability the convergency may be bad). For the details I
suggest you to look at the code.
