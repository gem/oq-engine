Source Specific Logic Trees
=============================================

There are situations in which the hazard model is comprised by a small
number of sources, and for each source there is an individual logic
tree managing the uncertainty of a few parameters. In such situations
we say that we have a *Source Specific Logic Tree*.

Such situation is esemplified by the demo that you can find in
the directory ``demos/hazard/LogicTreeCase2ClassicalPSHA``, which has
the following logic tree, in XML form:

.. xml:

    <logicTree logicTreeID="lt1">

            <logicTreeBranchSet uncertaintyType="sourceModel"
                                branchSetID="bs1">
                <logicTreeBranch branchID="b11">
                    <uncertaintyModel>source_model.xml</uncertaintyModel>
                    <uncertaintyWeight>1.0</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>

            <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                applyToSources="1"
                                branchSetID="bs21">
                <logicTreeBranch branchID="b21">
                    <uncertaintyModel>4.6 1.1</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b22">
                    <uncertaintyModel>4.5 1.0</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b23">
                    <uncertaintyModel>4.4 0.9</uncertaintyModel>
                    <uncertaintyWeight>0.334</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>

            <logicTreeBranchSet uncertaintyType="abGRAbsolute"
                                applyToSources="2"
                                branchSetID="bs31">
                <logicTreeBranch branchID="b31">
                    <uncertaintyModel>3.3 1.0</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b32">
                    <uncertaintyModel>3.2 0.9</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b33">
                    <uncertaintyModel>3.1 0.8</uncertaintyModel>
                    <uncertaintyWeight>0.334</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>

            <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                applyToSources="1"
                                branchSetID="bs41">
                <logicTreeBranch branchID="b41">
                    <uncertaintyModel>7.0</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b42">
                    <uncertaintyModel>7.3</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b43">
                    <uncertaintyModel>7.6</uncertaintyModel>
                    <uncertaintyWeight>0.334</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet>

            <logicTreeBranchSet uncertaintyType="maxMagGRAbsolute"
                                applyToSources="2"
                                branchSetID="bs51">
                <logicTreeBranch branchID="b51">
                    <uncertaintyModel>7.5</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b52">
                    <uncertaintyModel>7.8</uncertaintyModel>
                    <uncertaintyWeight>0.333</uncertaintyWeight>
                </logicTreeBranch>
                <logicTreeBranch branchID="b53">
                    <uncertaintyModel>8.0</uncertaintyModel>
                    <uncertaintyWeight>0.334</uncertaintyWeight>
                </logicTreeBranch>
            </logicTreeBranchSet> 

As you can see, each branchset has an ``applyToSources`` attribute, pointing
to one of the two sources in the hazard model, therefore we have a source
specific logic tree.
   
In compact form we can represent the logic tree as the composition
of two source specific logic trees with the following branchsets::

 src "1": [<abGRAbsolute(3)>, <maxMagGRAbsolute(3)>]
 src "2": [<abGRAbsolute(3)>, <maxMagGRAbsolute(3)>]

The ``(X)`` notation denotes the number of branches for each branchset and
multiplying such numbers we can deduce the size of the full logic tree
(ignoring the gsim logic tree for sake of simplificity)::

  (3 x 3 for src "1") x (3 x 3 for src "2") = 81 realizations

It is possible to see the full logic tree as the product of two source
specific logic trees each one with 9 realizations. The interesting thing
it that the engine will require storage and computational power proportional
to 9 + 9 = 18 basic components and not to the 9 * 9 = 81 final realizations.
In general if there are N source specific logic trees, each one generating
R_i realizations with i in the range 0..N-1, the number of basic components
and final realizations are respectively::

 C = sum(R_i)
 R = prod(R_i)

In the demo the storage is over 4 times less (18 vs 81); in more
complex cases the gain than can be much more impressive. For instance
the ZAF model in our mosaic (the national model for South Africa)
contains a source specific logic tree with 22 sources that can be
decomposed as follows:

.. code:

   >> full_lt = readinput.get_full_lt(oq)
   >> dic = full_lt.source_model_lt.decompose()
   >> pprint(dic)
   {'1': <SSLT:1 [<abGRAbsolute(3)>, <maxMagGRAbsolute(4)>]>,
   '10': <SSLT:10 [<abGRAbsolute(4)>, <maxMagGRAbsolute(3)>]>,
   '11': <SSLT:11 [<abGRAbsolute(4)>, <maxMagGRAbsolute(2)>]>,
   '12': <SSLT:12 [<abGRAbsolute(3)>, <maxMagGRAbsolute(3)>]>,
   '13': <SSLT:13 [<abGRAbsolute(2)>, <maxMagGRAbsolute(2)>]>,
   '14': <SSLT:14 [<abGRAbsolute(3)>, <maxMagGRAbsolute(4)>]>,
   '15': <SSLT:15 [<abGRAbsolute(3)>, <maxMagGRAbsolute(3)>]>,
   '16': <SSLT:16 [<abGRAbsolute(4)>, <maxMagGRAbsolute(3)>]>,
   '17': <SSLT:17 [<abGRAbsolute(4)>, <maxMagGRAbsolute(3)>]>,
   '18': <SSLT:18 [<abGRAbsolute(2)>, <maxMagGRAbsolute(2)>]>,
   '19': <SSLT:19 [<abGRAbsolute(3)>, <maxMagGRAbsolute(3)>]>,
   '2': <SSLT:2 [<abGRAbsolute(2)>, <maxMagGRAbsolute(3)>]>,
   '20': <SSLT:20 [<abGRAbsolute(2)>, <maxMagGRAbsolute(2)>]>,
   '21': <SSLT:21 [<abGRAbsolute(2)>, <maxMagGRAbsolute(3)>]>,
   '22': <SSLT:22 [<abGRAbsolute(4)>, <maxMagGRAbsolute(3)>]>,
   '23': <SSLT:23 [<abGRAbsolute(2)>, <maxMagGRAbsolute(3)>]>,
   '24': <SSLT:24 [<abGRAbsolute(2)>, <maxMagGRAbsolute(2)>]>,
   '3': <SSLT:3 [<abGRAbsolute(5)>, <maxMagGRAbsolute(4)>]>,
   '4': <SSLT:4 [<abGRAbsolute(3)>, <maxMagGRAbsolute(2)>]>,
   '5': <SSLT:5 [<abGRAbsolute(3)>, <maxMagGRAbsolute(3)>]>,
   '8': <SSLT:8 [<abGRAbsolute(2)>, <maxMagGRAbsolute(2)>]>,
   '9': <SSLT:9 [<abGRAbsolute(3)>, <maxMagGRAbsolute(2)>]>}
   >> C, R = 0, 1
   >> for sslt in dic.values():
   ..  Rs = sslt.get_num_paths()
   ..  C += Rs
   ..  R *= Rs
   >> print(C, R)
   186 24959374950829916160

In other words, by storing only 186 components we can save enough information
to build 24_959_374_950_829_916_160 realizations, with a gain of over 10^17!

Extracting the hazard curves
-------------------------------------------------

While it is impossible to compute the hazard curves for
24_959_374_950_829_916_160 realizations, it is quite possible to
get the source-specific hazard curves. To this end the engine
provides a class ``HcurvesGetter`` with a method ``.get_hcurves``
which is able to retrieve all the curves associated to the
realizations of the logic tree associated to a specific source.
Here is the usage:

.. code::

 from openquake.commonlib.datastore import read
 from openquake.calculators.getters import HcurvesGetter

 getter = HcurvesGetter(read(-1))
 print(getter.get_hcurves('1', 'PGA'))  # array of shape (Rs, L)

Looking at the source-specific realizations is useful to assess if
the logic tree can be collapsed.
