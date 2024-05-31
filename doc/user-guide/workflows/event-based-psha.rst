.. _event-based-psha-intro:

Event Based PSHA
================

Analysis Input data for the Event-Based PSHA - as in the case of the Classical *Probabilistic Seismic Hazard Analysis* 
calculator - consists of a PSHA Input Model and a set of calculation settings.

The main calculators used to perform this analysis are:

1. *Logic Tree Processor*

   The Logic Tree Processor works in the same way described in the description of the Classical *Probabilistic Seismic 
   Hazard Analysis* workflow (see Section :ref:`Classical PSHA <classical-psha-intro>`).

2. *Earthquake Rupture Forecast Calculator*

   The Earthquake Rupture Forecast Calculator was already introduced in the description of the PSHA workflow (see 
   Section :ref:`Classical PSHA <classical-psha-intro>`).

3. *Stochastic Event Set Calculator*

   The Stochastic Event Set Calculator generates a collection of stochastic event sets by sampling the ruptures 
   contained in the ERF according to their probability of occurrence.

   A Stochastic Event Set (SES) thus represents a potential realisation of the seismicity (i.e. a list of ruptures) 
   produced by the set of seismic sources considered in the analysis over the time span fixed for the calculation of 
   hazard.

4. *Ground Motion Field Calculator*

   The Ground Motion Field Calculator computes for each event contained in a Stochastic Event Set a realization of the 
   geographic distribution of the shaking by taking into account the aleatory uncertainties in the ground- motion model. 
   Eventually, the Ground Motion Field calculator can consider the spatial correlation of the ground-motion during the 
   generation of the Ground Motion Field.

5. *Event-based PSHA Calculator*

   The event-based PSHA calculator takes a (large) set of ground-motion fields representative of the possible shaking 
   scenarios that the investigated area can experience over a (long) time span and for each site computes the 
   corresponding hazard curve.

   This procedure is computationally intensive and is not recommended for investigating the hazard over large areas.

The reader interested in learning more about the science behaind this calculator can explore the 
:ref:`Underlying Science <underlying-science>` tab.