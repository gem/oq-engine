Classical Probabilistic Seismic Hazard Analysis
===============================================

Analysis Input data for the classical *Probabilistic Seismic Hazard Analysis* consist of a PSHA input model provided 
together with calculation settings.

The main calculators used to perform this analysis are the following:

1. *Logic Tree Processor*

   The Logic Tree Processor (LTP) takes as an input the *Probabilistic Seismic Hazard Analysis* Input Model and creates a 
   Seismic Source Model. The LTP uses the information in the Initial Seismic Source Models and the Seismic Source Logic 
   Tree to create a Seismic Source Input Model (i.e. a model describing geometry and activity rates of each source 
   without any epistemic uncertainty).

   Following a procedure similar to the one just described the Logic Tree Processor creates a Ground Motion model (i.e. 
   a data structure that associates to each tectonic region considered in the calculation a Ground Motion Prediction 
   Equation).

2. *Earthquake Rupture Forecast Calculator*

   The produced Seismic Source Input Model becomes an input information for the Earthquake Rupture Forecast (ERF) 
   calculator which creates a list earthquake ruptures admitted by the source model, each one characterized by a 
   probability of occurrence over a specified time span.

3. *Classical PSHA Calculator*

   The classical PSHA calculator uses the ERF and the Ground Motion model to compute hazard curves on each site 
   specified in the calculation settings.