The concept of effective realizations
==============================================

The management of the logic trees is the most complicated thing in the
OpenQuake engine. It is important to manage the logic trees in an
efficient way, by avoiding redundant computation and storage,
otherwise the engine will not be able to cope with large computations.
To that aim, it is essential to understand the concept of *effective
realizations*.

The crucial point is that in many calculations it is possible to reduce the
full logic tree (the tree of the potential realizations) to a much
smaller one (the tree of the effective realizations).

First, it is best to give some terminology.

1. for each source model in the source model logic tree there is potentially a
   different GMPE logic tree
2. the total number of realizations is the sum of the number of realizations
   of each GMPE logic tree
3. a GMPE logic tree is *trivial* if it has no tectonic region types with
   multiple GMPEs
4. a GMPE logic tree is *simple* if it has at most one tectonic region type
   with multiple GMPEs
5. a GMPE logic tree is *complex* if it has more than one tectonic region
   type with multiple GMPEs.

Here is an example of trivial GMPE logic tree, in its XML input representation:

.. code-block:: xml
  
   <?xml version="1.0" encoding="UTF-8"?>
   <nrml xmlns:gml="http://www.opengis.net/gml"
        xmlns="http://openquake.org/xmlns/nrml/0.4">
      <logicTree logicTreeID='lt1'>
              <logicTreeBranchSet uncertaintyType="gmpeModel" branchSetID="bs1"
                      applyToTectonicRegionType="active shallow crust">
  
                  <logicTreeBranch branchID="b1">
                      <uncertaintyModel>SadighEtAl1997</uncertaintyModel>
                      <uncertaintyWeight>1.0</uncertaintyWeight>
                  </logicTreeBranch>
  
              </logicTreeBranchSet>
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
*Active_Shallow* and *Stable_Shallow*, you would consider only 4 *
5 = 20 effective realizations instead of 1280. Doing so may improve
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
kind T1. In such a situation there will be 2 effective realization
coming from a total of 6 total realizations. It means that there will
be three copies of the outputs, i.e. three identical outputs for each
effective realization.

How to analyze the logic tree of a calculation without running the calculation
------------------------------------------------------------------------------

The engine provides some facilities to explore the logic tree of a
computation without running it. The command you need is the ``oq info`` command.
   
Let's assume that you have a zip archive called `SHARE.zip` containing the
SHARE source model, the SHARE source model logic tree file and the SHARE
GMPE logic tree file as provided by the SHARE collaboration, as well as
a `job.ini` file. If you run

  ``$ oq info SHARE.zip``

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

   $ oq info --report SHARE.zip
   ...
   [2020-04-14 11:11:50 #2493 WARNING] No sources for some TRTs: you should set
   discard_trts = Subduction_InSlab, Deep
   ...
   Generated /home/michele/report_2493.rst

If you open that file you will find a lot of useful information about
the source model, its composition, the number of sources and ruptures
and the effective realizations.

Depending on the location of the points and the maximum distance, one
or more submodels could be completely filtered out and could produce
zero effective realizations, so the reduction effect could be even
stronger.

In any case the warnings tells the user what she should do in order to
remove the duplication and reduce the calculation only to the effective
realizations, i.e. which are the TRTs to discard in the `job.ini` file.
