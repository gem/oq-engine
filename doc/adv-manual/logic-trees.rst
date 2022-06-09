Advanced logic trees
====================

Logic trees are documented in the OpenQuake manual (section "Defining
Logic Trees"). However some features are only mentioned without giving
examples (such as ``applyToBranches``) and some recent developments
are missing, in particular the ``extendModel`` feature. Here we
will document both.

extendModel
---------------------------------

Starting from engine 3.9 it is possible to define logic trees by adding sources
to one or more base models. An example will make things clear:

.. code-block:: xml

  <?xml version="1.0" encoding="UTF-8"?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
        xmlns="http://openquake.org/xmlns/nrml/0.5">
    <logicTree logicTreeID="lt1">
      <logicTreeBranchSet uncertaintyType="sourceModel"
                          branchSetID="bs0">
        <logicTreeBranch branchID="A">
          <uncertaintyModel>common1.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="B">
          <uncertaintyModel>common2.xml</uncertaintyModel>
          <uncertaintyWeight>0.4</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet uncertaintyType="extendModel" branchSetID="bs1">
        <logicTreeBranch branchID="C">
          <uncertaintyModel>extra1.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="D">
          <uncertaintyModel>extra2.xml</uncertaintyModel>
          <uncertaintyWeight>0.2</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="E">
          <uncertaintyModel>extra3.xml</uncertaintyModel>
          <uncertaintyWeight>0.2</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTree>
  </nrml>

In this example there are two base source models, named
``commom1.xml`` and ``common2.xml`` and three possibile extensions
``extra1.xml``, ``extra2.xml`` and ``extra3.xml``. The engine will
generate six effective source models by extending first
``common1.xml`` and then ``common2.xml`` with ``extra1.xml``, then
with ``extra2.xml`` and then with ``extra3.xml`` respectively. Notice
that ``extra1.xml``, ``extra2.xml`` and ``extra3.xml`` can be different
versions of the same sources with different parameters or geometries,
so ``extendModel`` can be used to implement correlated uncertainties.

Since engine 3.15 it is possible to describe logic trees as python
lists (one list for each branchset) and to programmatically generate
the realizations by using a simplified logic tree implementation in
hazardlib. This is extremely useful. For instance, the logic tree
above would be written as follows:

.. code-block:: python

 >>> from openquake.hazardlib.lt import build
 >>> logictree = build(
 ...     ['sourceModel', [], ['A', 'common1.xml', 0.6],
 ...                         ['B', 'common2.xml', 0.4]],
 ...     ['extendModel', [], ['C', 'extra1.xml', 0.6],
 ...                         ['D', 'extra2.xml', 0.2],
 ...                         ['E', 'extra3.xml', 0.2]])

and the 6 possible paths can be extracted as follows:
 
 >>> logictree.get_all_paths()  # 2 x 3 paths
 ['AC', 'AD', 'AE', 'BC', 'BD', 'BE']

The empty square brackets means that the branchset should be applied to all
branches in the previous branchset and correspond to the ``applyToBranches``
tag in the XML version of the logic tree. If ``applyToBranches`` is missing
the logic tree is multiplicative and the total number of paths can be
obtained simply by multiplying the number of paths in each branchset.
When ``applyToBranches`` is used the logic tree becomes additive and the
total number of paths can be obtained by summing the number of paths in
the different subtrees. For instance, let us extend the previous example
by adding another ``extendModel`` branchset and by using ``applyToBranches``:

.. code-block:: xml

  <?xml version="1.0" encoding="UTF-8"?>
  <nrml xmlns:gml="http://www.opengis.net/gml"
        xmlns="http://openquake.org/xmlns/nrml/0.4">
    <logicTree logicTreeID="lt1">
      <logicTreeBranchSet uncertaintyType="sourceModel"
                          branchSetID="bs0">
        <logicTreeBranch branchID="A">
          <uncertaintyModel>common1.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="B">
          <uncertaintyModel>common2.xml</uncertaintyModel>
          <uncertaintyWeight>0.4</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet uncertaintyType="extendModel" branchSetID="bs1"
                          applyToBranches="A">
        <logicTreeBranch branchID="C">
          <uncertaintyModel>extra1.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="D">
          <uncertaintyModel>extra2.xml</uncertaintyModel>
          <uncertaintyWeight>0.2</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="E">
          <uncertaintyModel>extra3.xml</uncertaintyModel>
          <uncertaintyWeight>0.2</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
      <logicTreeBranchSet uncertaintyType="extendModel" branchSetID="bs2"
                          applyToBranches="B">
        <logicTreeBranch branchID="F">
          <uncertaintyModel>extra4.xml</uncertaintyModel>
          <uncertaintyWeight>0.6</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="G">
          <uncertaintyModel>extra5.xml</uncertaintyModel>
          <uncertaintyWeight>0.4</uncertaintyWeight>
        </logicTreeBranch>
      </logicTreeBranchSet>
    </logicTree>
  </nrml>

In this case only 3 + 2 = 5 paths are considered. You can see which
are the combinations by building the logic tree:

 >>> logictree = build(
 ...     ['sourceModel', [], ['A', 'common1.xml', 0.6],
 ...                         ['B', 'common2.xml', 0.4]],
 ...     ['extendModel', ['A'], ['C', 'extra1.xml', 0.6],
 ...                            ['D', 'extra2.xml', 0.2],
 ...                            ['E', 'extra3.xml', 0.2]],
 ...     ['extendModel', ['B'], ['F', 'extra4.xml', 0.6],
 ...                            ['G', 'extra5.xml', 0.4]])
 >>> logictree.get_all_paths()  # 3 + 2 paths
 ['AC.', 'AD.', 'AE..', 'BF.', 'BG.']

``applyToBranches`` can be used in different ways. For instance you can
attach the second ``extendModel`` to everything and get 8 paths:

 >>> logictree = build(
 ...     ['sourceModel', [], ['A', 'common1.xml', 0.6],
 ...                         ['B', 'common2.xml', 0.4]],
 ...     ['extendModel', ['A'], ['C', 'extra1.xml', 0.6],
 ...                            ['D', 'extra2.xml', 0.2],
 ...                            ['E', 'extra3.xml', 0.2]],
 ...     ['extendModel', [], ['F', 'extra4.xml', 0.6],
 ...                         ['G', 'extra5.xml', 0.4]])
 >>> logictree.get_all_paths()  # 3 * 2 + 2 paths
 ['ACF', 'ACG', 'ADF', 'ADG', 'AEF', 'AEG', 'B.F', 'B.G']

The complete realizations can be obtained by not specifying ``applyToSources``:

.. code-block:: python

 >>> logictree = build(
 ...     ['sourceModel', [], ['A', 'common1.xml', 0.6],
 ...                         ['B', 'common2.xml', 0.4]],
 ...     ['extendModel', [], ['C', 'extra1.xml', 0.6],
 ...                         ['D', 'extra2.xml', 0.2],
 ...                         ['E', 'extra3.xml', 0.2]],
 ...     ['extendModel', [], ['F', 'extra4.xml', 0.6],
 ...                         ['G', 'extra5.xml', 0.4]])
 >>> logictree.get_all_paths() # 12 paths
 ['ACF', 'ACG', 'ADF', 'ADG', 'AEF', 'AEG', 'BCF', 'BCG', 'BDF', 'BDG', 'BEF', 'BEG']

The logic tree demo
-------------------

As another example we will consider the demo
``LogicTreeCase2ClassicalPSHA`` in the engine distribution; the
logic tree has the following structure:

.. code-block:: python

 >>> lt = build(
 ...    ['sourceModel', [], ['b11', 'source_model.xml', .333]],
 ...    ['abGRAbsolute', [], ['b21', '4.6 1.1', .333],
 ...                         ['b22', '4.5 1.0', .333],
 ...                         ['b23', '4.4 0.9', .334]],
 ...    ['abGRAbsolute', [], ['b31', '3.3 1.0', .333],
 ...                         ['b32', '3.2 0.9', .333],
 ...                         ['b33', '3.1 0.0', .334]],
 ...    ['maxMagGRAbsolute', [], ['b41', 7.0, .333],
 ...                             ['b42', 7.3, .333],
 ...                             ['b43', 7.6, .334]],
 ...    ['maxMagGRAbsolute', [], ['b51', 7.5, .333],
 ...                             ['b52', 7.8, .333],
 ...                             ['b53', 8.0, .334]],
 ...    ['Active Shallow Crust', [], ['c11', 'BA08', .5],
 ...                                 ['c12', 'CY12', .5]],
 ...    ['Stable Continental Crust', [], ['c21', 'TA02', .5],
 ...                                     ['c22', 'CA03', .5]])

Since the demo is using full enumeration there are 1*3*3*3*3*2*2 = 324
realizations in total that you can build as follows:

 >>> import numpy
 >>> paths = numpy.array(lt.get_all_paths())
 >>> for row in paths.reshape(36, 9):
 ...      print(' '.join(row))
 AADGJMO AADGJMP AADGJNO AADGJNP AADGKMO AADGKMP AADGKNO AADGKNP AADGLMO
 AADGLMP AADGLNO AADGLNP AADHJMO AADHJMP AADHJNO AADHJNP AADHKMO AADHKMP
 AADHKNO AADHKNP AADHLMO AADHLMP AADHLNO AADHLNP AADIJMO AADIJMP AADIJNO
 AADIJNP AADIKMO AADIKMP AADIKNO AADIKNP AADILMO AADILMP AADILNO AADILNP
 AAEGJMO AAEGJMP AAEGJNO AAEGJNP AAEGKMO AAEGKMP AAEGKNO AAEGKNP AAEGLMO
 AAEGLMP AAEGLNO AAEGLNP AAEHJMO AAEHJMP AAEHJNO AAEHJNP AAEHKMO AAEHKMP
 AAEHKNO AAEHKNP AAEHLMO AAEHLMP AAEHLNO AAEHLNP AAEIJMO AAEIJMP AAEIJNO
 AAEIJNP AAEIKMO AAEIKMP AAEIKNO AAEIKNP AAEILMO AAEILMP AAEILNO AAEILNP
 AAFGJMO AAFGJMP AAFGJNO AAFGJNP AAFGKMO AAFGKMP AAFGKNO AAFGKNP AAFGLMO
 AAFGLMP AAFGLNO AAFGLNP AAFHJMO AAFHJMP AAFHJNO AAFHJNP AAFHKMO AAFHKMP
 AAFHKNO AAFHKNP AAFHLMO AAFHLMP AAFHLNO AAFHLNP AAFIJMO AAFIJMP AAFIJNO
 AAFIJNP AAFIKMO AAFIKMP AAFIKNO AAFIKNP AAFILMO AAFILMP AAFILNO AAFILNP
 ABDGJMO ABDGJMP ABDGJNO ABDGJNP ABDGKMO ABDGKMP ABDGKNO ABDGKNP ABDGLMO
 ABDGLMP ABDGLNO ABDGLNP ABDHJMO ABDHJMP ABDHJNO ABDHJNP ABDHKMO ABDHKMP
 ABDHKNO ABDHKNP ABDHLMO ABDHLMP ABDHLNO ABDHLNP ABDIJMO ABDIJMP ABDIJNO
 ABDIJNP ABDIKMO ABDIKMP ABDIKNO ABDIKNP ABDILMO ABDILMP ABDILNO ABDILNP
 ABEGJMO ABEGJMP ABEGJNO ABEGJNP ABEGKMO ABEGKMP ABEGKNO ABEGKNP ABEGLMO
 ABEGLMP ABEGLNO ABEGLNP ABEHJMO ABEHJMP ABEHJNO ABEHJNP ABEHKMO ABEHKMP
 ABEHKNO ABEHKNP ABEHLMO ABEHLMP ABEHLNO ABEHLNP ABEIJMO ABEIJMP ABEIJNO
 ABEIJNP ABEIKMO ABEIKMP ABEIKNO ABEIKNP ABEILMO ABEILMP ABEILNO ABEILNP
 ABFGJMO ABFGJMP ABFGJNO ABFGJNP ABFGKMO ABFGKMP ABFGKNO ABFGKNP ABFGLMO
 ABFGLMP ABFGLNO ABFGLNP ABFHJMO ABFHJMP ABFHJNO ABFHJNP ABFHKMO ABFHKMP
 ABFHKNO ABFHKNP ABFHLMO ABFHLMP ABFHLNO ABFHLNP ABFIJMO ABFIJMP ABFIJNO
 ABFIJNP ABFIKMO ABFIKMP ABFIKNO ABFIKNP ABFILMO ABFILMP ABFILNO ABFILNP
 ACDGJMO ACDGJMP ACDGJNO ACDGJNP ACDGKMO ACDGKMP ACDGKNO ACDGKNP ACDGLMO
 ACDGLMP ACDGLNO ACDGLNP ACDHJMO ACDHJMP ACDHJNO ACDHJNP ACDHKMO ACDHKMP
 ACDHKNO ACDHKNP ACDHLMO ACDHLMP ACDHLNO ACDHLNP ACDIJMO ACDIJMP ACDIJNO
 ACDIJNP ACDIKMO ACDIKMP ACDIKNO ACDIKNP ACDILMO ACDILMP ACDILNO ACDILNP
 ACEGJMO ACEGJMP ACEGJNO ACEGJNP ACEGKMO ACEGKMP ACEGKNO ACEGKNP ACEGLMO
 ACEGLMP ACEGLNO ACEGLNP ACEHJMO ACEHJMP ACEHJNO ACEHJNP ACEHKMO ACEHKMP
 ACEHKNO ACEHKNP ACEHLMO ACEHLMP ACEHLNO ACEHLNP ACEIJMO ACEIJMP ACEIJNO
 ACEIJNP ACEIKMO ACEIKMP ACEIKNO ACEIKNP ACEILMO ACEILMP ACEILNO ACEILNP
 ACFGJMO ACFGJMP ACFGJNO ACFGJNP ACFGKMO ACFGKMP ACFGKNO ACFGKNP ACFGLMO
 ACFGLMP ACFGLNO ACFGLNP ACFHJMO ACFHJMP ACFHJNO ACFHJNP ACFHKMO ACFHKMP
 ACFHKNO ACFHKNP ACFHLMO ACFHLMP ACFHLNO ACFHLNP ACFIJMO ACFIJMP ACFIJNO
 ACFIJNP ACFIKMO ACFIKMP ACFIKNO ACFIKNP ACFILMO ACFILMP ACFILNO ACFILNP

The engine is computing all such realizations; after running the
calculations you will see an output called "Realizations". If you
export it, you will get a CSV file with the following structure::

  #,,"generated_by='OpenQuake engine 3.13..."
  rlz_id,branch_path,weight
  0,AAAAA~AA,3.0740926e-03
  1,AAAAA~AB,3.0740926e-03
  ...
  322,ACCCC~BA,3.1111853e-03
  323,ACCCC~BB,3.1111853e-03

For each realization there is a ``branch_path`` string which is split in
two parts separated by a tilde. The left part describe the branches of
the source model logic tree and the right part the branches of the gmpe
logic tree. In past versions of the engine the branch path was using
directly the branch IDs, so it was easy to assess the correspondence
between each realization and the associated branches.

Unfortunately, we had to remove that direct correspondence in engine
3.11. The reason is that engine is used in situations where the logic
tree has billions of billions of billions ... of billions potential
realizations, with hundreds of branchsets. If you have 100 branchsets
and the branch IDs are 10 characters long, each branch path will be
1000 characters long and impossible to display. The compact
representation requires only 1-character per branchset instead. It is
possible to pass from the compact representation to the original
branch IDs by using the command ``oq show branches``::

 $ oq show branches
 | branch_id | abbrev | uvalue              |
 |-----------+--------+---------------------|
 | b11       | A0     | source_model.xml    |
 | b21       | A1     | 4.60000 1.10000     |
 | b22       | B1     | 4.50000 1.00000     |
 | b23       | C1     | 4.40000 0.90000     |
 | b31       | A2     | 3.30000 1.00000     |
 | b32       | B2     | 3.20000 0.90000     |
 | b33       | C2     | 3.10000 0.80000     |
 | b41       | A3     | 7.00000             |
 | b42       | B3     | 7.30000             |
 | b43       | C3     | 7.60000             |
 | b51       | A4     | 7.50000             |
 | b52       | B4     | 7.80000             |
 | b53       | C4     | 8.00000             |
 | b11       | A0     | [BooreAtkinson2008] |
 | b12       | B0     | [ChiouYoungs2008]   |
 | b21       | A1     | [ToroEtAl2002]      |
 | b22       | B1     | [Campbell2003]      |

The first character of the ``abbrev`` specifies the branch number ("A"
means the first branch, "B" the second, etc) while the other characters
are the branch set number starting from zero. The format works up to
184 branches per branchset, bu using printable UTF8 characters.
For instance the realization #322 has the following branch path in
compact form::

 ACCCC~BA

which will expand to the following abbreviations (considering that fist "A"
corresponds to the branchset 0, the first "C" to branchset 1, the
second "C" to branchset 2, the third "C" to branchset 3, the fourth
"C" to branchset 4, "B" to branchset 0 of the GMPE logic tree and the
last "A" to branchset 1 of the GMPE logic tree)::

  A0 C1 C2 C3 C4 ~ B0 A1

and then, using the correspondence table ``abbrev->uvalue``, to::

  "source_model.xml" "4.4 0.9" "3.1 0.8" "7.6" "8.0" ~
  "[ChiouYoungs2008]" "[ToroEtAl2002]"

For convenience, the engine provides a simple command to display the content
of a realization, given the realization number, thus answering the
FAQ::

 $ oq show rlz:322
 | uncertainty_type         | uvalue            |
 |--------------------------+-------------------|
 | sourceModel              | source_model.xml  |
 | abGRAbsolute             | 4.40000 0.90000   |
 | abGRAbsolute             | 3.10000 0.80000   |
 | maxMagGRAbsolute         | 7.60000           |
 | maxMagGRAbsolute         | 8.00000           |
 | Active Shallow Crust     | [ChiouYoungs2008] |
 | Stable Continental Crust | [ToroEtAl2002]    |

NB: the commands `oq show branches` and `oq show rlz` are new in
engine 3.13: they may change in the future and the string
representation of the branch path may change too. It has already
changed twice in engine 3.11 and engine 3.12. You cannot rely on
it across engine versions.
