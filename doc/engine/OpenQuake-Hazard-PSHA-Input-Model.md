## PSHA Input Model
### Introduction
First step in the calculation of probabilistic seismic hazard is the creation of an Earthquake Rupture Forecast (ERF) i.e. a list of all the possible ruptures - with an associated probability of occurrence in a given time span - occurring on all the seismic sources considered in a given analysis.  

In the simplest case, OpenQuake creates the ERF using the information contained in one input file formatted according to a unified PSHA input data model (defined in the course of GEM1 - the GEM kick-off project [[http://www.globalquakemodel.org/gem1]]) currently supporting four types of seismic sources. In particular, for each source type, a set of parameters specifies the data necessary to create a Seismic Source instance and successively calculate the comprehensive set of ruptures with their probability of occurrence.

The Seismic Sources currently supported by OpenQuake (version 0.1) are:

* Area sources
* Grid sources
* Fault sources based on a
    * Simple geometry
    * Complex geometry 

In more complicated cases (i.e. PSHA input models based on a Logic Tree structure) the number of ERFs to be created can reach very high numbers depending on the complexity (i.e. number and properties of branching levels). 

### Assumptions

* OpenQuake 0.1 - The seismicity temporal occurrence model follows a Poisson process

### User stories

* OpenQuake 0.5 - Extend the Unified PSHA Input Data model so as to support additional source typologies 
    * Additional source typologies:

        * Fault sources with a completely irregular surface 
        * Segmented fault sources 
        * Background sources

* OpenQuake 0.5 - Generalize the use of different seismicity temporal occurrence models.
    * Temporal occurrence models:

        * Poisson
        * Brownian Time Passage


### Suggested Implementation

* OpenQuake 0.5 - Extend the Unified PSHA Input Data model so as to support additional source typologies 
* OpenQuake 0.5 - Generalize the use of different seismicity temporal occurrence models.

Back to [[Blue Prints |BluePrints]]
