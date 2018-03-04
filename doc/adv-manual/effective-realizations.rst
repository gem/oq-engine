The concept of effective realizations
==============================================

The management of the logic trees is the most complicated thing in the
OpenQuake libraries. The issue is that it is necessary to manage them
in an efficient way, by avoiding redundant computation and storage,
otherwise the engine will not be able to cope with large computations.

Historically the engine did not fare well in the case of complex logic
trees. In recent years we improved the situation by introducing the
concept of *effective realizations*. After realizing that in many
calculations it is possible to reduce the full logic tree (the tree of
the potential realizations) to a much smaller one
(the tree of the effective realizations), we implemented an engine
optimization to take advantage of such situations. Here I will
explain how the optimization work.

First, it is best to give some terminology.

1. for each source model in the source model logic tree there is a
   different GMPE logic tree
2. the total number of realizations is the sum of the number of realizations
   of each GMPE logic tree
3. a GMPE logic tree is *trivial* if it has no tectonic region types with
   multiple GMPEs
4. a GMPE logic tree is *simple* if it has at most one tectonic region type
   with multiple GMPEs
5. a GMPE logic tree is *complex* if it has more than one tectonic region
   type with multiple GMPEs.

Here is an example of trivial GMPE logic tree, in its XML input representation::
  
  <?xml version="1.0" encoding="UTF-8"?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
        xmlns="http://openquake.org/xmlns/nrml/0.4">
      <logicTree logicTreeID='lt1'>
          <logicTreeBranchingLevel branchingLevelID="bl1">
              <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs1"
                      applyToTectonicRegionType="active shallow crust">
  
                  <logicTreeBranch branchID="b1">
                      <uncertaintyModel>SadighEtAl1997</uncertaintyModel>
                      <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
  
              </logicTreeBranchSet>
          </logicTreeBranchingLevel>
      </logicTree>
  </nrml>

The logic tree is trivial since there is a single branch
("b1") and GMPE ("SadighEtAl1997") for each tectonic region
type ("active shallow crust").  A logic tree with multiple branches
can be simple, complex, or even trivial if the tectonic region type
with multiple branches is not present in the underlying source
model. This is the key to the logic tree reduction concept.

Reduction of the logic tree
-----------------------------------------------

The simplest case of logic tree reduction is when the actual
sources do not span the full range of tectonic region types in the
GMPE logic tree file. This happens very often in SHARE calculations.
The GMPE logic tree (actually there are three of them, one for each
source model) potentially contains 1280 realizations
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
1280, pretty large. We say that there are 1280 *potential
realizations* per source model. However, in most computations, the
user will be interested only in a subset of them. For instance, if the
sources contributing to your region of interest are only of kind
**Active_Shallow** and **Stable_Shallow**, you would consider only 4 *
5 = 20 effective realizations instead of 1280. Doing so will improve
the computation time and the needed storage by a factor of 1280 / 20 =
64, which is very significant.

Having motivated the need for the concept of effective realizations,
let explain how it works in practice. For sake of simplicity let us
consider the simplest possible situation, when there are two tectonic
region types in the logic tree file, but the engine contains only
sources of one tectonic region type.  Let us assume that for the first
tectonic region type (T1) the GMPE logic tree file contains 3 GMPEs (A,
B, C) and that for the second tectonic region type (T2) the GMPE logic tree
file contains 2 GMPEs (D, E). The total number of realizations (assuming
full enumeration) is

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

Now assume that the source model does not contain sources of tectonic
region type T1, or that such sources are filtered away since they are
too distant to have an effect: in such a situation we would expect to
have only 2 effective realizations corresponding to the GMPEs in the
second tectonic region type. The weight of each effective realizations
will be three times the weight of a regular representation, since
three different paths in the first tectonic region type will produce
exactly the same result.  It is not important which GMPE was chosen
for the first tectonic region type because there are no sources of
kind T1; so let's denote the path of the effective realizations with
the notation `@_<GMPE of second region type>`:

== ======
#   path
== ======
0  `@_D`
1  `@_E`
== ======

The "@" character should be read as "any", meaning that for the first
tectonic region type any path (i.e. "A", "B" and "C") will give
the same contribution, i.e. there is independence from the GMPE
combinations coming from the first tectonic region type.

In such a situation the engine will perform the computation only for the 2
effective realizations, not for the 6 potential realizations; moreover,
it will export only two files with names like::

  hazard_curve-smltp_sm-gsimltp_@_D-ltr_0.csv
  hazard_curve-smltp_sm-gsimltp_@_E-ltr_1.csv

How to analyze the logic tree of a calculation without running the calculation
------------------------------------------------------------------------------

The engine provide some facilities to explore the logic tree of a
computation without running it. The command you need is the *info* command::

   $ oq info -h
   usage: oq info [-h] [-c] [-g] [-v] [-r] [input_file]
   
   positional arguments:
     input_file         job.ini file or zip archive [default: '']
   
   optional arguments:
     -h, --help         show this help message and exit
     -c, --calculators  list available calculators
     -g, --gsims        list available GSIMs
     -v, --views        list available views
     -r, --report       build a report in rst format
   
Let's assume that you have a zip archive called `SHARE.zip` containing the
SHARE source model, the SHARE source model logic tree file and the SHARE
GMPE logic tree file as provided by the SHARE collaboration, as well as
a `job.ini` file. If you run

  `oq info SHARE.zip`

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
   b1, area_source_model.xml, trt=[0, 1, 2, 3, 4, 5, 6], weight=0.500: 1280 realization(s)
   b2, faults_backg_source_model.xml, trt=[7, 8, 9, 10, 11, 12, 13], weight=0.200: 1280 realization(s)
   b3, seifa_model.xml, trt=[14, 15, 16, 17, 18, 19], weight=0.300: 640 realization(s)>
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
using the `--report` flag. This will generate a report with a name
like `report_<calc_id>.rst`::

   $ oq info SHARE.zip --report
   ...
   Generated /home/michele/report_5580.rst

If you open that file you will find a lot of useful information about
the source model, its composition, the number of sources and ruptures
and the effective realizations.

Depending on the location of the points and the maximum distance, one
or more submodels could be completely filtered out and could produce
zero effective realizations, so the reduction effect could be even
stronger. Such a situation is covered by our tests
and will be discussed later on.

The realization-association object
----------------------------------

The `info` commands produces more output, which I have denoted simply as
`<RlzsAssoc...>`. This output is the string representation of
a Python object containing the associations between the pairs

  `(src_group_id, gsim) -> realizations`

In the case of the SHARE model there are simply too many realizations to make
it possible to understand what it is in the association object. So, it is
better to look at a simpler example. Consider for instance our QA test
classical/case_7; you can run the command and get::

   $ oq info classical/case_7/job.ini 
   <CompositionInfo
   b1, source_model_1.xml, trt=[0], weight=0.70: 1 realization(s)
   b2, source_model_2.xml, trt=[1], weight=0.30: 1 realization(s)>
   <RlzsAssoc(2)
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

   $ oq info classical/case_19/job.ini -f
   <CompositionInfo
   b1, simple_area_source_model.xml, trt=[0, 1, 2, 3, 4], weight=1.0:: 4 realization(s)>
   <RlzsAssoc(8)
   0,AtkinsonBoore2003SInter: ['<0,b1,@_@_@_@_b51_@_@,w=0.2>', '<1,b1,@_@_@_@_b52_@_@,w=0.2>', '<2,b1,@_@_@_@_b53_@_@,w=0.2>', '<3,b1,@_@_@_@_b54_@_@,w=0.4>']
   1,FaccioliEtAl2010: ['<0,b1,@_@_@_@_b51_@_@,w=0.2>', '<1,b1,@_@_@_@_b52_@_@,w=0.2>', '<2,b1,@_@_@_@_b53_@_@,w=0.2>', '<3,b1,@_@_@_@_b54_@_@,w=0.4>']
   2,ToroEtAl2002SHARE: ['<0,b1,@_@_@_@_b51_@_@,w=0.2>', '<1,b1,@_@_@_@_b52_@_@,w=0.2>', '<2,b1,@_@_@_@_b53_@_@,w=0.2>', '<3,b1,@_@_@_@_b54_@_@,w=0.4>']
   3,AkkarBommer2010: ['<0,b1,@_@_@_@_b51_@_@,w=0.2>', '<1,b1,@_@_@_@_b52_@_@,w=0.2>', '<2,b1,@_@_@_@_b53_@_@,w=0.2>', '<3,b1,@_@_@_@_b54_@_@,w=0.4>']
   4,AtkinsonBoore2003SSlab: ['<0,b1,@_@_@_@_b51_@_@,w=0.2>']
   4,LinLee2008SSlab: ['<1,b1,@_@_@_@_b52_@_@,w=0.2>']
   4,YoungsEtAl1997SSlab: ['<2,b1,@_@_@_@_b53_@_@,w=0.2>']
   4,ZhaoEtAl2006SSlab: ['<3,b1,@_@_@_@_b54_@_@,w=0.4>']>

This is a case where a lot of tectonic region types have been completely
filtered out, so the original 160 realizations have been reduced to merely 4 for
5 different tectonic region types:

- the first TRT with GSIM `AtkinsonBoore2003SInter` contributes to all the realizations;
- the second TRT with GSIM `FaccioliEtAl2010` contributes to all the realizations;
- the third TRT with GSIM `ToroEtAl2002SHARE` contributes to all the realizations;
- the fourth TRT with GSIM `AtkinsonBoore2003SInter` contributes to all the realizations;
- the fifth TRT contributes to one realization for each of four different GSIMs. 
