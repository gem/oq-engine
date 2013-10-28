Hazard Modeller's Toolkit (hmtk)
====

This is the web repository of the Hazard Modeller's Toolkit (hmtk). 
The hmtk is a suite of tools developed by Scientists working at the 
GEM (i.e. Global Earthquake Model) Model Facility. The main purpouse
of the hmtk is to provide a suite of tools for the creation of PSHA 
input models.

The toolkit contains the following functionalities for constructing 
seismic hazard input models (please refer to the documentation and
tutorial for more information):


SEISMICITY TOOLS:

* Declustering:
    * Gardner & Knopoff (1974)
    * AFTERAN (Musson, 1999)

* Completeness:
    * Stepp (1971)

* Earthquake Recurrence:
    * Weichet (1980)
    * ''Simple'' Maximum Likelihood (Aki, 1965)
    * ''Averaged'' Maximum Likelihood
    * Kijko & Smit (2012)

* Instrumental Seismicity Estimator of Maximum Magnitude
    * ''Fixed b-value'' (Kijko, 2004)
    * ''Uncertain b-value'' (Kijko, 2004)
    * ''Nonparametric Gaussian'' (Kijko, 2004)
    * Cumulative Moment

* Smoothed Seismicity
    * Isotropic Gaussian Smoothing (Frankel, 1995, approach)

GEOLOGICAL EARTHQUAKE RECURRENCE TOOLS:

* Anderson & Luco (1983)
    * ''Arbitrary'' recurrence - based on fault area
    * ''Area-Mmax'' recurrence - based on rupture area
    * ''Characteristic'' - via a Truncated Gaussian Distribution
    * Exponential (Youngs & Coppersmith, 1985)
    * Hybrid Characteristic (Youngs & Coppersmith, 1985)

GEODETIC SEISMICITY RECURRENCE TOOLS:

* Seismic Hazard Inferred from Tectonics (SHIFT) (Bird & Liu, 2007)


The Hazard Modeller's Toolkit is free software: you can redistribute 
it and/or modify it under the terms of the GNU Affero General Public 
License as published by the Free Software Foundation, either version 
3 of the License, or (at your option) any later version. Please take 
a minute of your time to read the disclaimer below.

The main dependencies of this library are the following:
* csv
* numpy
* python-decorator
* hazardlib (this is part of the OpenQuake suite)
* nrmllib (this is part of the OpenQuake suite)

For the libraries part of the OpenQuake suite the reader can refer to 
http://github.com/gem

Copyright (c) 2010-2013, GEM Foundation, G. Weatherill, M. Pagani, 
D. Monelli.


Disclaimer
----

The software Hazard Modeller's Toolkit (hmtk) provided herein 
is released as a prototype implementation on behalf of 
scientists and engineers working within the GEM Foundation (Global 
Earthquake Model). 

It is distributed for the purpose of open collaboration and in the 
hope that it will be useful to the scientific, engineering, disaster
risk and software design communities. 

The software is NOT distributed as part of GEM’s OpenQuake suite 
(http://www.globalquakemodel.org/openquake) and must be considered as a 
separate entity. The software provided herein is designed and implemented 
by scientific staff. It is not developed to the design standards, nor 
subject to same level of critical review by professional software 
developers, as GEM’s OpenQuake software suite.  

Feedback and contribution to the software is welcome, and can be 
directed to the hazard scientific staff of the GEM Model Facility 
(hazard@globalquakemodel.org). 

The Hazard Modeller's Toolkit (hmtk) is therefore distributed WITHOUT 
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
for more details.

The GEM Foundation, and the authors of the software, assume no 
liability for use of the software.
