Correlation of Ground Motion Fields
=========================================

There are multiple different kind of correlation on the engine, so it
is extremely easy to get confused. Here I will list all possibilities,
in historical order.

1. Spatial correlation of ground motion fields has been a feature of
   the engine from day one. The available models are JB2009 and HM2018.
2. Cross correlation in ShakeMaps has been available for a few years.
   The model used there is hard-coded an the user cannot change it,
   only disable it. The models list below (3. and 4.) *have no effect
   on ShakeMaps*.
3. Since version 3.13 the engine provides the BakerJayaram2008 cross
   correlation model, however at the moment it is used only in the conditional
   spectrum calculator.
4. Since version 3.13 the engine provides the GodaAtkinson2009 cross
   correlation model and the FullCrossCorrelation model which can be
   used in scenario and event based calculations.

Earthquake theory tells us that ground motion fields depend on two
different lognormal distributions with parameters (:math:`\mu`,
:math:`\tau`) and (:math:`\mu`, :math:`\phi`) respectively, which are
determined by the GMPE (Ground Motion Prediction Equal). Given a
rupture, a set of M intensity measure types and a collection of N
sites, the parameters :math:`\mu`, :math:`\tau` and :math:`\phi` are
arrays of shape (M, N). :math:`\mu` is the mean of the logarithms and
:math:`\tau` the between-event standard deviation, associated to the
cross correlation, while :math:`\phi` is the within-event standard
deviation, associated to the spatial correlation. math:`\tau` and
:math:`\phi` are normally N-independent, i.e.  each array of shape
(M, N) actually contains N copies of the same M values read from the
coefficient table of the GMPE.

In the OpenQuake engine each rupture has associated a random seed
generated from the parameter ``ses_seed`` given in the job.ini file,
therefore given a fixed number E of events it is possible to generate
a deterministic distribution of ground motion fields, i.e. an array of
shape (M, N, E). Technically such feature is implemented in the class
``openquake.hazardlib.calc.gmf.GmfComputer``. The algorithm used there
is to generate two arrays of normally distributed numbers called
:math:`\epsilon_\tau` (of shape (M, E)) and :math:`\epsilon_\phi` (of
shape (M, N, E)), one using the between-event standard deviation
:math:`\tau` and the other using the within-event standard deviation
:math:`\phi`, while keeping the same mean :math:`\mu`. Then the ground
motion fields are generated as an array of shape (M, N, E) with the
formula

.. math::

  gmf = exp(\mu + crosscorrel(\epsilon_\tau) + spatialcorrel(\epsilon\phi))

The details depend on the form of the cross correlation model and of
the spatial correlation model and you have to study the source code if
you really want to understand how it works, in particular how the
correlation matrices are extracted from the correlation models. By
default, if no cross correlation nor spatial correlation are
specified, then there are no correlation matrices and
:math:`crosscorrel(\epsilon_\tau)` and
:math:`spatialcorrel(\epsilon\phi)` are computed by using
``scipy.stats.truncnorm``. Otherwise
``scipy.stats.multivariate_normal`` with a correlation
matrix of shape (M, M) is used for cross correlation and
``scipy.stats.multivariate_normal`` distribution with a
matrix of shape (N, N) is used for spatial correlation. Notice that the
truncation feature is lost if you use correlation, since scipy does
not offer at truncated multivariate_normal distribution. Not truncating
the normal distribution can easily generated non-physical fields, but
even if the truncation is on it is very possible to generate exceedingly
large ground motion fields, so the user has to be *very* careful.

Correlation is important because its presence normally causes the risk to
increase, i.e. ignoring the correlation will under-estimate
the risk. The best way to play with the correlation is to consider a
scenario_risk calculation with a single rupture and to change the
cross and spatial correlation models. Possibilities are to specify
in the job.ini all possible combinations of

cross_correlation = FullCrossCorrelation
cross_correlation = GodaAtkinson2009
ground_motion_correlation_model = JB2009
ground_motion_correlation_model = HM2018

including removing one or the other or all correlations.
