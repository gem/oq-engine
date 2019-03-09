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
``__init__`` method*. It is not necessary, since the ``__init__`` will
be inherited from the superclass. If you need to perform some
initialization please define and ``init()`` method without arguments
and the engine will call it. Here is an example::

.. code-block:

   from openquake.hazardlib.gsim.base import GMPE

   class MyGMPE(GMPE):
      def init(self):
          # doing some initialization here

The signature of the base ``GMPE.__init__`` method is ``**kwargs``, so anything
can be passed to it. Such dictionary is stored in ``self.kwargs`` and your
``init()`` method can operate on the passed arguments in this way, if need
there is.

There is a limitation on ``kwargs``: it must be a *dictionary of literal Python
objects* so that it admits a TOML representation. TOML is a simple format
similar to the .ini format but hierarchical that is described here
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
``{'gmpe_table': "Wcrust_low_rhypo.hdf5"}``.

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
