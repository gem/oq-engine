.. _configuration-file:

Configuration File
==================

This section summarises the structure of the information necessary to define the different input data to be used with 
the OpenQuake engine hazard and risk calculators, i.e. the so called ``job.ini`` configuration file.

The configuration file is the primary file controlling both the definition of the input model as well as parameters 
governing the calculation. We illustrate in the following different examples of the configuration file addressing 
different types of seismic hazard and risk calculations. Each calculator has its own specific parameters, however there are a few
parameters which are common to all calculators, so they will be explained first.


.. toctree::
   :maxdepth: 2

   hazard-common-config
   classical-psha-config
   event-based-psha-config
   scenario-hazard-config
   risk-common-config
   classical-risk-config
   event-based-risk-config
   scenario-risk-config
   refrofit-benefit-cost-config
   reinsurance-config

