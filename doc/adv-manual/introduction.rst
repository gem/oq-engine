Introduction
=======================================

If you have just started using the OpenQuake engine, and the only thing
you have tried are the OpenQuake demos, this manual is NOT for you. Beginners
should study the `official manual <https://www.globalquakemodel.org/single-post/OpenQuake-Engine-Manual>`_. This manual is for advanced users, i.e.
people that already know how to use the engine, but are running *large*
calculations and have trouble performing them.

For the purposes of this manual a calculation is large if it cannot be run,
i.e. if it runs out of memory, it fails with strange errors (rabbitmq
errors, pickling errors, ...) or it just takes too long to complete.

There are various reasons way a calculation can be too large. 99% of the
times it is because the user is making some mistakes and he is trying to
run a calculation larger than he really needs. In the remaining 1% of the
times the calculation is genuinely large and the only solution is to
buy a larger machine, or to ask the OpenQuake developers to optimize the
engine for the specific calculation that is giving issues.

The most common mistakes are the following:

1. trying to run the calculation directly without a run of
   ``oq info --report job.ini`` first. The first things to do when
   do when you have a large calculation is to generate the report,
   that will tell you essential information to estimate the size of the
   full calculation, in particular the number of hazard sites,
   the number of ruptures, the number of assets and the most relevant
   parameters you are using. If generating the report is slow, it means
   that there is something very wrong with your calculation and you will
   never be able to run it unless you reduce it.

2. Using bad parameters in the job.ini file, like too fine discretization
   parameters. Then your source model with contains millions and millions
   of ruptures and the computation will become impossibly slow if it is
   a classical calculation, while it will run out of memory if it is an
   event based one.

3. Using an exposure which is not aggregated enough. You can easily gain
   orders of magnitude in speed while doing a risk calculation
   if you aggregate the assets on a small number of hazard sites. For
   instance, an exposure with 1 million assets aggregated on 2000 sites
   is not a problem; but if you do not aggregate, you will have a computation
   with 1 million hazard sites that will likely be impossible.
