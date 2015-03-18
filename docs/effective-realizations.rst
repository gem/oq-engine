The concept of effective realizations
==============================================

The management of the logic trees is the most complex thing in the
OpenQuake libraries. The problem is that it is necessary to implement logic
trees in an efficient way, otherwise the engine will not be able to
cope with large computations.
To this aim we introduced the concept of *effective
realizations*. There are common situations where it is
possible to reduce the full logic tree of a computation to a much
smaller one. The engine takes full advantage of such situations.

Reduction of the logic tree (full enumeration)
-----------------------------------------------

The reduction of the logic tree happens when the actual
sources do not span the full range of tectonic region types in the
GMPE logic tree file. This happens very often in SHARE calculations.
The GMPE logic tree potentially contains 1280 realizations per each
of the three source models contained in the SHARE model,
coming from 7 different tectonic region types:

Active_Shallow:
 4 GMPEs (b1, b2, b3, b4)
Stable_Shallow:
 5 GMPEs (b21, b22, b23, b24, b25)
Shield:
 2 GMPEs (b31, b32)
Subduction_Interface:
 4 GMPEs (b41, b42, b43, b44)
Subduction_InSlab:
 4 GMPEs (b51, b52, b53, b54)
Volcanic:
 1 GMPE (b61)
Deep:
 2 GMPEs (b71, b72)

The number of paths in the logic tree is 4 * 5 * 2 * 4 * 4 * 1 * 2 =
1280, pretty large. We say that there are 1280 *potential realizations*.
However, in most computations the user will be interested
only in a subset of them. For instance, if the sources contributing to
your region of interest are only of kind **Active_Shallow** and
**Stable_Shallow**, you would consider only 4 * 5 = 20 effective
realizations instead of 1280. Doing so will improve the computation
time and the neeed storage by a factor of 1280 / 20 = 64, which is
very significant.

Having motivated the need for the concept of effective realizations,
let explain how it works in practice. For sake of simplicity let us
consider the simplest possible situation, when there are two tectonic
region types in the logic tree file, but the engine contains only
sources of one tectonic region type.  Let us assume that for the first
tectonic region type (T1) the GMPE logic tree file contains 3 GMPEs (A,
B, C) and for the second tectonic region type (T2) the GMPE logic tree
file contains 2 GMPEs (D, E). The total number of realizations is

  `total_num_rlzs = 3 * 2 = 6`

The realizations are identified by an ordered pair of GMPEs, one for each
tectonic region type. Let's number the realizations, starting from zero,
and let's identify the logic tree path with the notation
`<GMPE of first region type>_<GMPE of second region type>`:

== ========
#  lt_path
== ========
0   `A_D`
1   `B_D`
2   `C_D`
3   `A_E`
4   `B_E`
5   `C_E`
== ========

Now assume that the source model does not contain sources of tectonic region
type T1, or that such sources are filtered away since they are too distant
to have an effect: in such a situation we would expect to have only 2
effective realizations corresponding to the GMPEs in the second
tectonic region type. The weight of each effective realizations will be
three times the weight of a regular representation, since three different paths
in the first tectonic region type will produce exactly the same result.
It is not important which GMPE was chosen for the first tectonic region
type because there are no sources of kind T1; so let's denote the
path of the effective realizations with the notation
`*_<GMPE of second region type>`:

== ======
#   path
== ======
0  `*_D`
1  `*_E`
== ======

In such situation the engine will perform the computation only for the 2
effective realizations, not for the 6 potential realizations; moreover,
it will export only two files with names like::

  hazard_curve-smltp_sm-gsimltp_*_D-ltr_0.csv
  hazard_curve-smltp_sm-gsimltp_*_E-ltr_1.csv


Reduction of the logic tree when sampling is enabled
----------------------------------------------------

There are real life examples of very complex logic trees, even with more
more than 400,000 branches. In such situation it is impossible to perform
a full computation. However, the engine allows to
sample the branches of the complete logic tree. More precisely,
for each branch sampled from the source model logic
tree a branch of the GMPE logic tree is chosen randomly,
by taking into account the weights in the GMPE logic tree file.

Suppose for instance that we set

  `number_of_logic_tree_samples = 4000`

to sample 4,000 branches instead of 400,000. The expectation is that
the computation will be 100 times faster. This is indeed the case for the
classical calculator. However, for the event based calculator things
are trickier: each sample of the source model must produce different
ruptures, even if there is only one source model repeated 4,000 times,
because of the inherent stochasticity of the process. Therefore the
time spent in generating the needed amount of ruptures could make the
calculator slower than using full enumeration: remember than when
using full enumeration the ruptures of a given source model are generated
exactly once, since each path is taken exactly once.

Notice that even if source model path is
sampled several times, the model is parsed and sent to the workers *only
once*. In particular if there is a single source model and
`number_of_logic_tree_samples = 4000`, we generate effectively
1 source model realization and not 4,000 equivalent source model
realizations, as we did in past (actually in the engine version 1.3).
Then engine keeps track of how many times a model has
been sampled (say `N`) and in the event based case it produce ruptures
(*with different seeds*)
by calling the appropriate hazardlib function `N` times. This is done
inside the worker nodes. In the classical case, all the ruptures are
identical and there are no seeds, so the computation is done only once,
in an efficient way.


Convergency of the event based hazard calculator
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

 
How to analyze the logic tree of a calculation without running the calculation
==============================================================================


`oq-lite` provide some facilities to explore the logic tree of a
computation. The command you need is the *info* command::

   $ oq-lite info -h
   usage: oq-lite info [-h] [-f] name
   
   positional arguments:
     name                 calculator name, job.ini file or zip archive
   
   optional arguments:
     -h, --help           show this help message and exit
     -f, --filtersources  flag to enable filtering of the source models

Let's assume that you have a zip archive called `SHARE.zip` containing the
SHARE source model, the SHARE source model logic tree file and the SHARE
GMPE logic tree file as provided by the SHARE collaboration, as well as
a `job.ini` file. If you run

  `oq-lite info SHARE.zip`

all the files will be parsed and the full logic tree of the computation
will be generated. This is very fast, it runs in exactly 1 minute on my
laptop, which is impressive, since the XML of the SHARE source models
is larger than 250 MB. Such speed come with a price: all the sources
are parsed, but they are not filtered, so you will get the complete
logic tree, not the one used by your computation, which will likely be
reduced because filtering will likely remove some tectonic region types.

The output of the `info` command will start with a `CompositionInfo`
object, which contains information about the composition of the source
model. You will get something like this::

   <CompositionInfo
   b1, area_source_model.xml, trt=[0, 1, 2, 3, 4, 5, 6]: 1280 realization(s)
   b2, faults_backg_source_model.xml, trt=[7, 8, 9, 10, 11, 12, 13]: 1280 realization(s)
   b3, seifa_model.xml, trt=[14, 15, 16, 17, 18, 19]: 640 realization(s)>
   <RlzsAssoc...>

You can read the lines above as follows. The SHARE model is composed by three
submodels:

 * `area_source_model.xml` contains 7 Tectonic Region Types numbered from 0 to 7
   and produces 1280 potential realizations;
 * `faults_backg_source_model.xml` contains 7 Tectonic Region Types numbered from 7 to 13
   and produces 1280 potential realizations;
 * `seifa_model.xml` contains 6 Tectonic Region Types numbered from 14 to 19
   and produces 640 potential realizations;

In practice, you want to know if your complete logic tree will be
reduced by the filtering, i.e. you want to know the effective
realizations, not the potential ones. You can perform that check by
using the `--filtersources` flag. For the sake of exemplification, I will
show the output of a real life computation, performed by one of our users
who was interested in only three sites and wanted to filter the sources
around those points with a maximum distance of 200 kilometers::

   $ oq-lite info SHARE.zip --filtersources
   <CompositionInfo
   b1, area_source_model.xml, trt=[0, 1, 2, 3, 4, 5, 6]: 80 realization(s)
   b2, faults_backg_source_model.xml, trt=[7, 8, 9, 10, 11, 12, 13]: 80 realization(s)
   b3, seifa_model.xml, trt=[14, 15, 16, 17, 18, 19]: 80 realization(s)>
   <RlzsAssoc...>

In this example the effective SHARE model is composed by three submodels:

 * `area_source_model.xml` contains 7 Tectonic Region Types numbered from 0 to 7
   and produces 80 effective realizations;
 * `faults_backg_source_model.xml` contains 7 Tectonic Region Types numbered from 7 to 13
   and produces 80 effective realizations;
 * `seifa_model.xml` contains 6 Tectonic Region Types numbered from 14 to 19
   and produces 80 effective realizations;

Depending on the location of the points and the maximum distance, one
or more submodels could be completely filtered out and could produce
zero effective realizations, so the reduction effect could be even
stronger. Such a situation is covered by our tests
and will be discussed in the next paragraph. Notice that already in
this case we reduced the computation from 1280 + 1280 + 640 = 3200
potential realizations to only 80 + 80 + 80 = 240 effective
realizations.


The realization-association object
----------------------------------

The `info` commands produces more output, which I have denoted simply as
`<RlzsAssoc...>`. This output is the string representation of
a Python object containing the associations between the pairs

  `(trt_model_id, gsim) -> realizations`

In the case of the SHARE model there are simply too many realizations to make
it possible to understand what it is in the association object. So, it is
better to look at a simpler example. Consider for instance our QA test
classical/case_7; you can run the command and get::

   $ oq-lite info classical/case_7/job.ini 
   <CompositionInfo
   b1, source_model_1.xml, trt=[0]: 1 realization(s)
   b2, source_model_2.xml, trt=[1]: 1 realization(s)>
   <RlzsAssoc
   0,SadighEtAl1997: ['<0,b1,b1,w=0.7>']
   1,SadighEtAl1997: ['<1,b2,b1,w=0.3>']>

In other words, this is an example containing two submodels, each one
with a single tectonic region type and with a single GMPE
(SadighEtAl1997). There are only two realizations with weights 0.7 and
0.3 and they are associated to the tectonic region types as shown in
the RlzsAssoc object. This is a case when there is a realization for
tectonic region type, but more complex cases are possibile.  For
instance consider our test classical/case_19, which is a reduction of
the SHARE model with just a simplified area source model::

   $ oq-lite info classical/case_19/job.ini -f
   <CompositionInfo
   b1, simple_area_source_model.xml, trt=[0, 1, 2, 3, 4]: 4 realization(s)>
   <RlzsAssoc
   0,AtkinsonBoore2003SInter: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   1,FaccioliEtAl2010: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   2,ToroEtAl2002SHARE: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   3,AkkarBommer2010: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   4,AtkinsonBoore2003SSlab: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>']
   4,LinLee2008SSlab: ['<1,b1,*_*_*_*_b52_*_*,w=0.2>']
   4,YoungsEtAl1997SSlab: ['<2,b1,*_*_*_*_b53_*_*,w=0.2>']
   4,ZhaoEtAl2006SSlab: ['<3,b1,*_*_*_*_b54_*_*,w=0.4>']>

This is a case where a lot of tectonic region types have been completely
filtered out, so the original 160 realizations have been reduced to merely 4 for
5 different tectonic region types:

- the first TRT with GSIM `AtkinsonBoore2003SInter` contributes to all the realizations;
- the second TRT with GSIM `FaccioliEtAl2010` contributes to all the realizations;
- the third TRT with GSIM `ToroEtAl2002SHARE` contributes to all the realizations;
- the fourth TRT with GSIM `AtkinsonBoore2003SInter` contributes to all the realizations;
- the fifth TRT contributes to one realization for each of four different GSIMs. 
