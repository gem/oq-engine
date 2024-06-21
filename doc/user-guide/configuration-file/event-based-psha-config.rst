.. _event-based-psha-params:

Event based PSHA
----------------

In the following we describe the sections of the configuration file that are required to complete event based PSHA 
calculations.

*******
general
*******

This part is almost identical to the corresponding one described in Section :ref:`Classical PSHA <classical-psha-params>`.

Note the setting of the ``calculation_mode`` parameter which now corresponds to ``event_based``.::

	[general]
	description = A demo OpenQuake-engine .ini file for event based PSHA
	calculation_mode = event_based

**********************
event based parameters
**********************

This section is used to specify the number of stochastic event sets to be generated for each logic tree realisation 
(each stochastic event set represents a potential realisation of seismicity during the ``investigation_time`` specified 
in the ``calculation_configuration`` part). Additionally, in this section the user can specify the spatial correlation 
model to be used for the generation of ground motion fields.::

	ses_per_logic_tree_path = 5
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}

The acceptable flags for the parameter ``vs30_clustering`` are ``False`` and ``True``, with a capital ``F`` and ``T`` 
respectively. ``0`` and ``1`` are also acceptable flags.

******
output
******

This part substitutes the ``Output`` part described in the
configuration file example described in the Section :ref:`Classical PSHA <classical-psha-params>`.::

	[output]
	export_dir = /tmp/xxx
	ground_motion_fields = true
	# post-process ground motion fields into hazard curves,
	# given the specified `intensity_measure_types_and_levels`
	hazard_curves_from_gmfs = true
	mean = true
	quantiles = 0.15, 0.50, 0.85
	poes = 0.1, 0.2

Starting from OpenQuake engine v2.2, it is now possible to export
information about the ruptures directly in CSV format.

The option ``hazard_curves_from_gmfs`` instructs the user to use the
event- based ground motion values to provide hazard curves indicating
the probabilities of exceeding the intensity measure levels set
previously in the ``intensity_measure_types_and_levels`` option.


====================================================
The difference between full enumeration and sampling
====================================================

Users are often confused about the difference between full enumeration and sampling. For this reason the engine 
distribution comes with a pedagogical example that considers an extremely simplified situation comprising a single site, 
a single rupture, and only two GMPEs. You can find the example in the engine repository under the directory 
openquake/qa_tests_data/event_based/case_3. If you look at the ground motion logic tree file, the two GMPEs are 
AkkarBommer2010 (with weight 0.9) and SadighEtAl1997 (with weight 0.1).

The parameters in the job.ini are::

	investigation_time = 1
	ses_per_logic_tree_path = 5_000
	number_of_logic_tree_paths = 0

Since there are 2 realizations, the effective investigation time is 10,000 years. If you run the calculation, you will 
generate (at least with version 3.13 of the engine, though the details may change with the version) 10,121 events, since 
the occurrence rate of the rupture was chosen to be 1. Roughly half of the events will be associated with the first 
GMPE (AkkarBommer2010) and half with the second GMPE (SadighEtAl1997). Actually, if you look at the test, the precise 
numbers will be 5,191 and 4,930 events, i.e. 51% and 49% rather than 50% and 50%, but this is expected and by increasing 
the investigation time you can get closer to the ideal equipartition. Therefore, even if the AkkarBommer2010 GMPE is 
assigned a relative weight that is 9 times greater than SadighEtAl1997, *this is not reflected in the simulated event set.* 
It means that when performing a computation (for instance to compute the mean ground motion field, or the average loss) 
one has to keep the two realizations distinct, and only at the end to perform the weighted average.

The situation is the opposite when sampling is used. In order to get the same effective investigation time of 10,000 
years you should change the parameters in the job.ini to::

	investigation_time = 1
	ses_per_logic_tree_path = 1
	number_of_logic_tree_paths = 10_000

Now there are 10,000 realizations, not 2, and they all have the same weight .0001. The number of events per realization 
is still roughly constant (around 1) and there are still 10,121 events, however now *the original weights are reflected 
in the event set.* In particular there are 9,130 events associated to the AkkarBommer2010 GMPE and 991 events associated 
to the SadighEtAl1997 GMPE. There is no need to keep the realizations separated: since they have all the same weigths, 
you can trivially compute average quantities. AkkarBommer2010 will count more than SadighEtAl1997 simply because there 
are 9 times more events for it (actually 9130/991 = 9.2, but the rate will tend to 9 when the effective time will tend 
to infinity).

**Note:** just to be clear, normally realizations are not in one-to-one correspondence with GMPEs. In this example, it is true 
because there is a single tectonic region type. However, usually there are multiple tectonic region types, and a 
realization is associated to a tuple of GMPEs.