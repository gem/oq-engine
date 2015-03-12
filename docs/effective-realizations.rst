The concept of effective realizations
==============================================

The management of the so-called logic trees is the most complex
concept in the OpenQuake-engine. The difficulty lies in optimization
concerns: it is necessary to implement logic trees in an efficient way,
otherwise the engine will not be able to cope with large computations.

To this aim we introduced the concept of *effective realizations*:
there are very common situations in which it is possible to reduce the
full logic tree of a computation to a much smaller tree, containing
much less effective realizations (i.e. paths) than the potential
realizations.

Reduction of the GMPE logic tree
------------------------------------

The reduction of the GMPE logic tree happens when the actual
sources do not span the full range of tectonic region types in the
GMPE logic tree file. This happens practically always in SHARE calculations.
The SHARE GMPE logic tree potentially contains 1280 realizations,
coming from 7 different tectonic region types.

Active_Shallow:
 4 GMPEs
Stable_Shallow:
 5 GMPEs
Shield:
 2 GMPEs
Subduction_Interface:
 4 GMPEs
Subduction_InSlab:
 4 GMPEs
Volcanic:
 1 GMPE
Deep:
 2 GMPEs

The number of paths in the full logic tree is 4 * 5 * 2 * 4 * 4 * 1 *
2 = 1280, pretty large. However, in practice, in most computation
users are interested only in a subset of the tectonic region type. For
instance, if the sources in your model are only of kind Active_Shallow
and Stable_Shallow, you should consider only 4 * 5  = 20 effective
realizations instead of 1280. Doing so will improve the computation
time and the neeed storage by a factor of 1280 / 20 = 64, which is
very significant.

Having motivated the need for the concept of effective realizations,
let explain how it works in practice. For sake of simplicity let us
consider the simplest possible situation, when there are two tectonic
region types in the logic tree file, but the engine contains only
sources of one tectonic region type.  Let us assume that for the first
tectonic region type (T1) the GMPE logic tree file contains 3 GMPEs A,
B, C and for the second tectonic region type (T2) the GMPE logic tree
file contains 2 GMPEs D, E. The total number of realizations is

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

The engine lite will export two files with names like::

  hazard_curve-smltp_sm-gsimltp_*_D-ltr_0.csv
  hazard_curve-smltp_sm-gsimltp_*_E-ltr_1.csv


Reduction of the source model logic tree when sampling is enabled
-----------------------------------------------------------------

Consider a very common use case where one has a simple source model
but a very large GMPE logic tree (we have real life examples
with more than 400,000 branches). In such situation one would like to
sample the branches of the GMPE logic tree. The complications is that
currently the GMPE logic tree and the source model logic tree are
coupled and the only way to sample the GMPE logic is to sample the
source model logic tree. For each branch of the source model logic
tree a single branch of the GMPE logic tree is chosen randomly,
by taking into account the weights in the GMPE logic tree file.

Suppose for instance that we set

  `number_of_logic_tree_samples = 4000`

to sample 4,000 branches instead of 400,000. The expectation is
that the computation will be 100 times faster, however this is
not necessarily the case. There are two very different situations:

1. if we are performing an event based calculation then each sample
   of the source model will produce different ruptures even if there is
   only one source model repeated 4,000 times, because of the inherent
   stochasticity of the process;
2. if we are performing a classical (or disaggregation) calculation
   identical samples will produce identical ruptures.

In both cases the engine is so smart that even if source model path is
sampled several times, the model is parsed and sen to the workers *only
once*. In particular if there is a single source model and
`number_of_logic_tree_samples = 4000`, we generate effectively
1 source model realization and not 4,000 equivalent source model
realizations. Then engine keeps track of how many times a model has
been sampled (say `N`) and in the event based case it produce ruptures
(*with different seeds*)
by calling the appropriate hazardlib function `N` times. This is done
inside the worker nodes. In the classical case, all the ruptures are
identical and there are no seeds, so the computation is done only once,
in an efficient way.


Convergency of the event based hazard curves to the classical hazard curves
---------------------------------------------------------------------------

Are the effective realizations produced by an event based calculation
the same as the one produced by an equivalent classical calculation?
The answer is yes and do: they are the same in theory, since the result
of an event based calculation should converge to the result of the
equivalent classical calculation, however in practice if the parameters
`number_of_logic_tree_samples` and `ses_per_logic_tree_path` (the product
of them is the relevant one) are not large enough they may be different.
In particular, if you are unlucky, a tectonic region type producing
ruptures in the classical calculation could *not* produce case in the
corresponding event based calculation, for a given set of parameters.
The consequence is the event based calculation can have less effective
realizations than the classical calculation. In the limit of
many samples/many SES however all tectonic regions which are relevant
for the classical calculation should produce ruptures for the event
based calculation too.

 
How to analyze the logic tree of a calculation without running the calculation
==============================================================================


`oq-lite` provide some facilities to explore the logic tree of a
computation. The command you need is the `info` command::

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
   area_source_model.xml, trt=[0, 1, 2, 3, 4, 5, 6]: 1280 realization(s)
   faults_backg_source_model.xml, trt=[7, 8, 9, 10, 11, 12, 13]: 1280 realization(s)
   seifa_model.xml, trt=[14, 15, 16, 17, 18, 19]: 640 realization(s)
   trt=0, col=[0]
   trt=1, col=[1]
   trt=2, col=[2]
   trt=3, col=[3]
   trt=4, col=[4]
   trt=5, col=[5]
   trt=6, col=[6]
   trt=7, col=[7]
   trt=8, col=[8]
   trt=9, col=[9]
   trt=10, col=[10]
   trt=11, col=[11]
   trt=12, col=[12]
   trt=13, col=[13]
   trt=14, col=[14]
   trt=15, col=[15]
   trt=16, col=[16]
   trt=17, col=[17]
   trt=18, col=[18]
   trt=19, col=[19]>
   <lots-of-other-stuff-here>

You can read the lines above as follows. The SHARE model is composed by three
submodels:

 * `area_source_model.xml` contains 7 Tectonic Region Types numbered from 0 to 7
   and produces 1280 potential realizations;
 * `faults_backg_source_model.xml` contains 7 Tectonic Region Types numbered from 7 to 13
   and produces 1280 potential realizations;
 * `seifa_model.xml` contains 6 Tectonic Region Types numbered from 14 to 19
   and produces 640 potential realizations;

The `col` list contains a single element which is the tectonic region type: this
is always the case when full enumeration is enabled. That list is only interesting
when you are doing sampling, which is a case which we will consider later on.

In practice, you want to know if your complete logic tree will be
reduced by the filtering, i.e. you want to know the effective
realizations, not the potential ones. You can perform that check by
using the `--filtersources` flag. For the sake of exemplification, I will
show the output of a real life computation, performed by one of our users
which was interested in only three sites and wanted to filter the sources
around those points with a maximum distance of 200 kilometers::

   $ oq-lite info SHARE.zip --filtersources
   <CompositionInfo
   area_source_model.xml, trt=[0, 1, 2, 3, 4, 5, 6]: 80 realization(s)
   faults_backg_source_model.xml, trt=[7, 8, 9, 10, 11, 12, 13]: 80 realization(s)
   seifa_model.xml, trt=[14, 15, 16, 17, 18, 19]: 80 realization(s)
   trt=0, col=[0]
   trt=1, col=[1]
   trt=2, col=[2]
   trt=3, col=[3]
   trt=4, col=[4]
   trt=5, col=[5]
   trt=6, col=[6]
   trt=7, col=[7]
   trt=8, col=[8]
   trt=9, col=[9]
   trt=10, col=[10]
   trt=11, col=[11]
   trt=12, col=[12]
   trt=13, col=[13]
   trt=14, col=[14]
   trt=15, col=[15]
   trt=16, col=[16]
   trt=17, col=[17]
   trt=18, col=[18]
   trt=19, col=[19]>
   <lots-of-other-stuff-here>

In this example the effective SHARE model is composed by three submodels:

 * `area_source_model.xml` contains 7 Tectonic Region Types numbered from 0 to 7
   and produces 80 effective realizations;
 * `faults_backg_source_model.xml` contains 7 Tectonic Region Types numbered from 7 to 13
   and produces 80 effective realizations;
 * `seifa_model.xml` contains 6 Tectonic Region Types numbered from 14 to 19
   and produces 80 effective realizations;

Depending on the location of the points and the maximum distance, one or more submodels
could be completely filtered out and could produce zero effective realizations, so
the reduction effect could be even stronger. Already in this case we reduced the
computation from 1280 + 1280 + 640 = 3200 potential realizations to only 80 + 80 + 80 = 240
realizations.


The realization association object
----------------------------------

The `info` commands produces more output, which I have denoted simply as
`<lots-of-other-stuff-here>`. This output is the string representation of
a Python object containing the associations between the pairs

  `(trt_model_id, gsim) -> realizations`

In the case of the SHARE model there are simply too many realizations to make
it possible to undestand what it is in the association object. So, it is
better to look at a simpler example. Consider for instance our QA test
classical/case_7; you can run the command and get::

   $ oq-lite info classical/case_7/job.ini 
   <CompositionInfo
   source_model_1.xml, trt=[0]: 1 realization(s)
   source_model_2.xml, trt=[1]: 1 realization(s)
   trt=0, col=[0]
   trt=1, col=[1]>
   <RlzsAssoc
   0,SadighEtAl1997: ['<0,b1,b1,w=0.7>']
   1,SadighEtAl1997: ['<1,b2,b1,w=0.3>']>

In other words, this is an example containing two submodels, each one with a single
tectonic region type and with a single GMPE (SadighEtAl1997). There are only two
realizations with weights 0.7 and 0.3 and they are associated to the tectonic
region types as shown in the RlzsAssoc object. This is a case when there is
a realization for tectonic region type, but more complex cases are possibile.
For instance consider our case_19::

   $ oq-lite info classical/case_19/job.ini -f
   <CompositionInfo
   simple_area_source_model.xml, trt=[0, 1, 2, 3, 4]: 4 realization(s)
   trt=0, col=[0]
   trt=1, col=[1]
   trt=2, col=[2]
   trt=3, col=[3]
   trt=4, col=[4]>
   <RlzsAssoc
   0,AtkinsonBoore2003SInter: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   1,FaccioliEtAl2010: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   2,ToroEtAl2002SHARE: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   3,AkkarBommer2010: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>', '<1,b1,*_*_*_*_b52_*_*,w=0.2>', '<2,b1,*_*_*_*_b53_*_*,w=0.2>', '<3,b1,*_*_*_*_b54_*_*,w=0.4>']
   4,AtkinsonBoore2003SSlab: ['<0,b1,*_*_*_*_b51_*_*,w=0.2>']
   4,LinLee2008SSlab: ['<1,b1,*_*_*_*_b52_*_*,w=0.2>']
   4,YoungsEtAl1997SSlab: ['<2,b1,*_*_*_*_b53_*_*,w=0.2>']
   4,ZhaoEtAl2006SSlab: ['<3,b1,*_*_*_*_b54_*_*,w=0.4>']>

This is a SHARE calculation where a lot of tectonic region types have been completely
filtered out, so the original 3200 realizations have been reduced to merely 4 for
5 different tectonic region types.

THe first TRT with GSIM `AtkinsonBoore2003SInter` contributes to all the realizations;
the second TRT with GSIM `FaccioliEtAl2010` contributes to all the realizations;
the third TRT with GSIM `ToroEtAl2002SHARE` contributes to all the realizations;
the fourth TRT with GSIM `AtkinsonBoore2003SInter` contributes to all the realizations;
the fifth TRT contributes to one realization for each of four different GSIMs. 
