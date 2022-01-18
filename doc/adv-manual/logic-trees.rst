Logic trees FAQ
===============

Logic trees are documented in the OpenQuake manual (section "Defining
Logic Trees"). Here we will discuss some example for users already
familiar with the concept and we will answer the following frequently asked
questions:

- what is the meaning of the ``branch_path`` column in the "Realizations"
  output?
- given a realization, how do I extract the corresponding source model,
  modifications parameters and GMPEs?

As a concrete example we will consider the demo
``LogicTreeCase2ClassicalPSHA`` in the engine distribution; the source
model logic tree file has the following structure branchset ->
branches::

   bs1[sourceModel] ->      b11[source_model.xml]
   bs2[abGRAbsolute] ->     b21[4.6 1.1], b22[4.5 1.0], b23[4.4 0.9]
   bs3[abGRAbsolute] ->     b31[3.3 1.0], b32[3.2 0.9], b33[3.1 0.8]
   bs4[maxMagGRAbsolute] -> b41[7.0], b42[7.3], b43[7.6]
   bs5[maxMagGRAbsolute] -> b51[7.5], b52[7.8], b53[8.0]

while the gsim logic tree file has the following structure::

  bs1[Active Shallow Crust] ->     b11[BooreAtkinson2008], b12[ChiouYoungs2008]
  bs2[Stable Continental Crust] -> b21[ToroEtAl2002], b22[Campbell2003]

Since the demo is using full enumeration there are 3**4 * 2**2 = 324
realizations in total.

After running the calculations you will see an output called
"Realizations". If you export it, you will get a CSV file with the
following structure::

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
64 branches per branchset, and the characters used in the abbreviations are in
the following order::

 ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-

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
