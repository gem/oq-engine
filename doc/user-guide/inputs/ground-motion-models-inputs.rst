Ground Motion Models
====================

The list of GMPEs available in the OpenQuake engine can be found :ref:`here <openquake-hazardlib-gsim>`.

Parametric GMPEs
----------------

Most of the Ground Motion Prediction Equations (GMPEs) in hazardlib are classes that can be instantiated without 
arguments. However, there is now a growing number of exceptions. Here I will describe some of the parametric GMPEs we 
have, as well as give some guidance for authors wanting to implement a parametric GMPE.

*************************
Signature of a GMPE class
*************************

The more robust way to define parametric GMPEs is to use a ``**kwargs`` signature (robust against subclassing)::

	from openquake.hazardlib.gsim.base import GMPE
	
	class MyGMPE(GMPE):
	   def __init__(self, **kwargs):
	       super().__init__(**kwargs)
	       # doing some initialization here

The call to ``super().__init__`` will set a ``self.kwargs`` attribute and perform a few checks, like raising a warning 
if the GMPE is experimental. In absence of parameters ``self.kwargs`` is the empty dictionary, but in general it is 
non-empty and it can be arbitrarily nested, with only one limitation: it must be a *dictionary of literal Python objects* 
so that it admits a TOML representation.

TOML is a simple format similar to the ``.ini`` format but hierarchical (see `toml-lang/toml <https://github.com/toml-lang/toml#user-content-example>`_). 
It is used by lots of people in the IT world, not only in Python. The advantage of TOML is that it is a lot more 
readable than JSON and XML and simpler than YAML: moreover, it is perfect for serializing into text literal Python 
objects like dictionaries and lists. The serialization feature is essential for the engine since the GMPEs are read 
from the GMPE logic tree file which is a text file, and because the GMPEs are saved into the datastore as text, in the 
dataset ``full_lt/gsim_lt``.

The examples below will clarify how it works.

*********
GMPETable
*********

Historically, the first parametric GMPE was the GMPETable, introduced many years ago to support the Canada model. The 
GMPETable class has a single parameter, called ``gmpe_table``, which is a (relative) pathname to an .hdf5 file with a fixed 
format, containing a tabular representation of the GMPE, numeric rather than analytic.

You can find an example of use of GMPETables in the test openquake/qa_tests_data/case_18, which contains three tables 
in its logic tree::

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

As you see, the TOML format is used inside the ``uncertaintyModel`` tag; the text::

	[GMPETable]
	gmpe_table = "Wcrust_low_rhypo.hdf5"

is automatically translated into a dictionary ``{'GMPETable': {'gmpe_table': "Wcrust_low_rhypo.hdf5"}}`` and the 
``.kwargs`` dictionary passed to the GMPE class is simply::

	{'gmpe_table': "Wcrust_low_rhypo.hdf5"}

NB: you may see around old GMPE logic files using a different syntax, without TOML::

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

This is a legacy syntax, which is still supported and will likely be supported forever, but we recommend to use the new 
TOML-based syntax, which is more general. The old syntax has the limitation of being non-hierarchic, making it 
impossible to define MultiGMPEs involving parametric GMPEs: this is why we switched to TOML.

********************
File-dependent GMPEs
********************

It is possible to define other GMPEs taking one or more filenames as parameters. Everything will work provided you 
respect the following rules:

1. there is a naming convention on the file parameters, that must end with the suffix ``_file`` or ``_table``;
2. the files must be read at GMPE initialization time (i.e. in the ``__init__`` method);
3. in the gsim logic tree file you must use **relative** path names.

The constraint on the argument names makes it possible for the engine to collect all the files required by the GMPEs; 
moreover, since the path names are relative, the ``oq zip`` command can work making it easy to ship runnable calculations. 
The engine also stores in the datastore a copy of all of the required input files. Without the copy, it would not be 
possible from the datastore to reconstruct the inputs, thus making it impossible to dump and restore calculations from 
a server to a different machine.

The constraint about reading at initialization time makes it possible for the engine to work on a cluster. The issue is 
that GMPEs are instantiated in the controller and used in the worker nodes, which *do not have access to the same 
filesystem*. If the files are read after instantiation, you will get a file not found error when running on a cluster.

For instance, if your GMPE must read 
a text file with argument name *text_file* you should write the following code::

	class GMPEWithTextFile(GMPE):
	    def __init__(self, text_file):
	        with open(text_file) as myfile:
	            self.text = myfile.read()

*********
MultiGMPE
*********

Another example of parametric GMPE is the MultiGMPE class. A MultiGMPE is a dictionary of GMPEs, keyed by Intensity 
Measure Type. It is useful in geotechnical applications and in general in any situation where you have GMPEs depending 
on the IMTs. You can find an example in our test openquake/qa_tests_data/classical/case_1::

	<logicTreeBranch branchID="b1">
	   <uncertaintyModel>
	     [MultiGMPE."PGA".AkkarBommer2010]
	     [MultiGMPE."SA(0.1)".SadighEtAl1997]
	   </uncertaintyModel>
	   <uncertaintyWeight>1.0</uncertaintyWeight>
	 </logicTreeBranch>

Here the engine will use the GMPE ``AkkarBommer2010`` for ``PGA`` and ``SadighEtAl1997`` for ``SA(0.1)``. The ``.kwargs`` 
passed to the ``MultiGMPE`` class will have the form::

	{'PGA': {'AkkarBommer2010': {}},
	 'SA(0.1)': {'SadighEtAl1997': {}}}

The beauty of the TOML format is that it is hierarchic, so if we wanted to use parametric GMPEs in a MultiGMPE we could. 
Here is an example using the GMPETable *Wcrust_low_rhypo.hdf5* for ``PGA`` and *Wcrust_med_rhypo.hdf5* for ``SA(0.1)`` 
(the example has no physical meaning, it is just an example)::

	<logicTreeBranch branchID="b1">
	   <uncertaintyModel>
	     [MultiGMPE."PGA".GMPETable]
	       gmpe_table = "Wcrust_low_rhypo.hdf5"
	     [MultiGMPE."SA(0.1)".GMPETable]
	       gmpe_table = "Wcrust_med_rhypo.hdf5"
	   </uncertaintyModel>
	   <uncertaintyWeight>1.0</uncertaintyWeight>
	 </logicTreeBranch>

****************
GenericGmpeAvgSA
****************

In engine 3.4 we introduced a GMPE that manages a range of spectral accelerations and acts in terms of an average 
spectral acceleration. You can find an example of use in openquake/qa_tests/data/classical/case_34::

	<logicTreeBranch branchID="b1">
	    <uncertaintyModel>
	       [GenericGmpeAvgSA]
	       gmpe_name = "BooreAtkinson2008"
	       avg_periods = [0.5, 1.0, 2.0]
	       corr_func = "baker_jayaram"
	    </uncertaintyModel>
	    <uncertaintyWeight>1.0</uncertaintyWeight>
	</logicTreeBranch>

As you see, the format is quite convenient when there are several arguments of different types: here we have two strings 
(``gmpe_name`` and ``corr_func``) and a list of floats (``avg_periods``). The dictionary passed to the underlying class 
will be::

	{'gmpe_name': "BooreAtkinson2008",
	 'avg_periods': [0.5, 1.0, 2.0],
	 'corr_func': "baker_jayaram"}

**************
ModifiableGMPE
**************

In engine 3.10 we introduced a ``ModifiableGMPE`` class which is able to modify the behavior of an underlying GMPE. 
Here is an example of use in the logic tree file::

	<uncertaintyModel>
	    [ModifiableGMPE]
	    gmpe.AkkarEtAlRjb2014 = {}
	    set_between_epsilon.epsilon_tau = 0.5
	</uncertaintyModel>

Here *set_between_epsilon* is simply shifting the mean with the formula *mean -> mean + epsilon_tau * inter_event*. In 
the future ``ModifiableGMPE`` will likely grow more methods. If you want to understand how it works you should look at 
the source code: `gem/oq-engine <https://github.com/gem/oq-engine/blob/master/openquake/hazardlib/gsim/mgmpe/modifiable_gmpe.py>`_

In engine 3.21 we added a helper function `valid.modified_gsim`
to modify a GMPE. Internally it is creating a `ModifiableGMPE` instance,
but it is much simpler to use. An example is:

.. code-block:: python

   >>> from openquake.hazardlib import valid
   >>> orig_gsim = valid.gsim('Lin2011foot')
   >>> gsim = valid.modified_gsim(
   ...        orig_gsim, add_between_within_stds={'with_betw_ratio':1.5})
   >>> print(gsim)
   [ModifiableGMPE.gmpe.Lin2011foot]
   [ModifiableGMPE.add_between_within_stds]
   with_betw_ratio = 1.5

***************
NRCan15SiteTerm
***************

The ``NRCan15SiteTerm`` class is another example of a GMPE that can be
used to modify the behavior of an underlying GMPE. It is used in many models
of the GEM mosaic (but not in 2015 model for Canada, in spite of the name).
Here are a few examples of how to use it in the gsim logic tree file::

 [NRCan15SiteTerm]
 gmpe_name = SomervilleEtAl2009YilgarnCraton

 [NRCan15SiteTerm]
 gmpe_name = PezeshkEtAl2011NEHRPBC

 [NRCan15SiteTerm]
 gmpe_name = ToroEtAl2002SHARE

When instantiated, the ``NRCan15SiteTerm`` works like the underlying
GMPE, except the computed mean values are amplified by a factor
depending on the vs30 parameters (hence the name ``SiteTerm``). The
initial version of the code for the amplification factor was
provided by Michal Kolaj from Geological Survey of Canada, hence the
name ``NRCan15``.
