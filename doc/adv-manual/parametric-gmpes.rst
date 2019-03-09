Parametric GMPEs
===================================

Most of the Ground Motion Prediction Equations (GMPEs) in hazardlib are
classes that can be instantiated without arguments, however there is
now a growing number of exceptions to the rule. Here I will describe
some of the parametric GMPEs we have, as well as give some guidance for
authors wanting to implement a parametric GMPE.

Signature of a GMPE class
-------------------------

The best advice for an implementor of a new GMPE is *do not define an
__init__ method*. It is not necessary, since the ``__init__`` will
be inherited from the superclass. If you need to perform some
initialization please define an ``init()`` method without arguments
and the engine will call it. Here is an example:

.. code-block:

   from openquake.hazardlib.gsim.base import GMPE

   class MyGMPE(GMPE):
      def init(self):
          # doing some initialization here

The signature of the base ``GMPE.__init__`` method is ``**kwargs``.
Such dictionary is stored in ``self.kwargs`` and your
``init()`` method can operate on the passed arguments in this way, if need
there is.

There is a limitation on ``kwargs``: it must be a *dictionary of literal Python
objects* so that it admits a TOML representation. TOML is a simple format
similar to the ``.ini`` format but hierarchical that is described here
https://github.com/toml-lang/toml#user-content-example and it is used
by lots of people in the IT world. The advantage of TOML is that it is
a lot more readable than JSON and XML and simpler than YAML: moreover,
it is perfect for serializing into text literal Python objects like
dictionaries and lists. The serialization feature is essential for the
engine since the GMPEs are read from the GMPE logic tree file which is a
text file, a because the GMPEs are saved into the datastore as a text,
in the dataset ``csm_info/gsim_lt/branches``.

The examples below will make it clear how it works.

GMPETable
------------------------

Historically, the first parametric GMPE was the GMPETable, introduced many
years ago to support the Canada model. The GMPETable class has a single
parameter, called ``gmpe_table``, which is a (relative) pathname to an
.hdf5 file with a fixed format, containing a tabular representation of
the GMPE, numeric rather than analytic.

You can find an example of use of GMPETables in the test
openquake/qa_tests_data/case_18, which contains three tables in its
logic tree:

.. code-block: xml

        <logicTreeBranch branchID="b11">
          <uncertaintyModel>
            [GMPETable]
            gmpe_table = "Wcrust_low_rhypo.hdf5"
          </uncertaintyModel>
          <uncertaintyWeight>0.16</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="b12">
          <uncertaintyModel>
            [GMPETable]
            gmpe_table = "Wcrust_med_rhypo.hdf5"
          </uncertaintyModel>
          <uncertaintyWeight>0.68</uncertaintyWeight>
        </logicTreeBranch>
        <logicTreeBranch branchID="b13">
          <uncertaintyModel>
            [GMPETable]
            gmpe_table = "Wcrust_high_rhypo.hdf5"
          </uncertaintyModel>
          <uncertaintyWeight>0.16</uncertaintyWeight>
        </logicTreeBranch>

As you see, the TOML format is used inside the ``uncertaintyModel`` tag;
the text::

    [GMPETable]
    gmpe_table = "Wcrust_low_rhypo.hdf5"

is automatically translated into a dictionary
``{'GMPETable': {'gmpe_table': "Wcrust_low_rhypo.hdf5"}}`` and the ``.kwargs``
dictionary passed to the GMPE class is simply

.. code-block:

   {'gmpe_table': "Wcrust_low_rhypo.hdf5"}

NB: you may see around old GMPE logic files using a different syntax,
without TOML:

.. code-block: xml

       <logicTreeBranch branchID="b11">
          <uncertaintyModel gmpe_table="Wcrust_low_rhypo.hdf5">
             GMPETable
          </uncertaintyModel>
          <uncertaintyWeight>0.16</uncertaintyWeight>
       </logicTreeBranch>
          <logicTreeBranch branchID="b12">
          <uncertaintyModel gmpe_table="Wcrust_med_rhypo.hdf5">
             GMPETable
          </uncertaintyModel>
          <uncertaintyWeight>0.68</uncertaintyWeight>
       </logicTreeBranch>
          <logicTreeBranch branchID="b13">
          <uncertaintyModel gmpe_table="Wcrust_high_rhypo.hdf5">
             GMPETable
          </uncertaintyModel>
          <uncertaintyWeight>0.16</uncertaintyWeight>
       </logicTreeBranch>

This is a legacy syntax, which is still supported and will likely be supported
forever, but we recommend you to use the new TOML-based syntax, which is
more general. The old syntax has the limitation of being non-hierarchic,
making it impossible to define MultiGMPEs involving parametric GMPEs:
this is why we switched to TOML.

MultiGMPE
-----------------

The second example of parametric GMPE is the MultiGMPE class. A MultiGMPE
is a dictionary of GMPEs, keyed by Intensity Measure Type. It is useful
in geotechnical applications and in general in any situation where you
have GMPEs depending on the IMTs. You can find an example in our test
openquake/qa_tests_data/classical/case_1:

.. code-block: xml
   
           <logicTreeBranch branchID="b1">
              <uncertaintyModel>
                [MultiGMPE."PGA".AkkarBommer2010]
                [MultiGMPE."SA(0.1)".SadighEtAl1997]
              </uncertaintyModel>
              <uncertaintyWeight>1.0</uncertaintyWeight>
            </logicTreeBranch>

Here the engine will use the GMPE ``AkkarBommer2010`` for ``PGA`` and
``SadighEtAl1997`` for ``SA(0.1)``. The ``.kwargs`` passed to the
``MultiGMPE`` class will have the form:

.. code-block:

   {'PGA': {'AkkarBommer2010': {}},
    'SA(0.1)': {'SadighEtAl1997': {}}}

The beauty of the TOML format is that it is hierarchic, so if we wanted
to use parametric GMPEs in a MultiGMPE we could. Here is an example
using the GMPETable `Wcrust_low_rhypo.hdf5` for ``PGA`` and
`Wcrust_med_rhypo.hdf5` for ``SA(0.1)`` (the example has not physical
meaning, it is just an example):

.. code-block: xml

           <logicTreeBranch branchID="b1">
              <uncertaintyModel>
                [MultiGMPE."PGA".GMPETable]
                  gmpe_table = "Wcrust_low_rhypo.hdf5"
                [MultiGMPE."SA(0.1)".GMPETable]
                  gmpe_table = "Wcrust_med_rhypo.hdf5"
              </uncertaintyModel>
              <uncertaintyWeight>1.0</uncertaintyWeight>
            </logicTreeBranch>

GenericGmpeAvgSA
----------------

In engine 3.4 we introduced a GMPE that manages a range of spectral
accelerations and acts in terms of an average spectral acceleration.
You can find an example of use in openquake/qa_tests/data/classical/case_34:

.. code-block: xml
   
           <logicTreeBranch branchID="b1">
               <uncertaintyModel>
                  [GenericGmpeAvgSA]
                  gmpe_name = "BooreAtkinson2008"
                  avg_periods = [0.5, 1.0, 2.0]
                  corr_func = "baker_jayaram"
               </uncertaintyModel>
               <uncertaintyWeight>1.0</uncertaintyWeight>
           </logicTreeBranch>

As you see, the format is quite convenient when there are several arguments
of different types: here we have two strings (``gmpe_name`` and
``corr_func``) and a list of floats (``avg_periods``). The dictionary
passed to the underlying class will be

.. code_block:

   {'gmpe_name': "BooreAtkinson2008",
    'avg_periods': [0.5, 1.0, 2.0],
    'corr_func': "baker_jayaram"}

