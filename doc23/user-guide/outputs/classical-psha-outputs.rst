Outputs from Classical PSHA
===========================

By default, the classical PSHA calculator computes and stores hazard curves for each logic tree sample considered.

When the PSHA input model doesn’t contain epistemic uncertainties the results is a set of hazard curves (one for each 
investigated site). The command below illustrates how it is possible to retrieve the group of hazard curves obtained for 
a calculation with a given identifier ``<calc_id>`` (see Section :ref:`Exporting results from a hazard calculation <export-hazard-results>`
for an explanation about how to obtain the list of calculations performed with their corresponding ID)::
	
	user@ubuntu:~$ oq engine --lo <calc_id>
	id | name
	3* | Hazard Curves
	4  | Realizations

To export from the database the outputs (in this case hazard curves) contained in one of the output identifies, one can 
do so with the following command::

	user@ubuntu:~$ oq engine --export-output <output_id> <output_directory>

Alternatively, if the user wishes to export all of the outputs associated with a particular calculation then they can 
use the ``--export-outputs`` with the corresponding calculation key::

	user@ubuntu:~$ oq engine --export-outputs <calc_id> <output_directory>

The exports will produce one or more nrml files containing the seismic hazard curves, as represented below in the 
*listing <lst:output_hazard_curves_xml>* below.::

	<?xml version="1.0" encoding="utf-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	  <hazardCurves sourceModelTreePath="b1|b212"
	                gsimTreePath="b2" IMT="PGA"
	                investigationTime="50.0">
	    <IMLs>0.005 0.007 0.0098 ... 1.09 1.52 2.13</IMLs>
	    <hazardCurve>
	      <gml:Point>
	        <gml:pos>10.0 45.0</gml:pos>
	      </gml:Point>
	      <poEs>1.0 1.0 1.0 ... 0.000688359310522 0.0 0.0</poEs>
	    </hazardCurve>
	    ...
	    <hazardCurve>
	      <gml:Point>
	        <gml:pos>lon lat</gml:pos>
	      </gml:Point>
	      <poEs>poe1 poe2 ... poeN</poEs>
	    </hazardCurve>
	  </hazardCurves>
	</nrml>

Notwithstanding the intuitiveness of this file, let’s have a brief overview of the information included. The overall 
content of this file is a list of hazard curves, one for each investigated site, computed using a PSHA input model 
representing one possible realisation obtained using the complete logic tree structure.

The attributes of the ``hazardCurves`` element (see text in red) specify the path of the logic tree used to create the 
seismic source model (``sourceModelTreePath``) and the ground motion model (``gsimTreePath``) plus the intensity measure 
type and the investigation time used to compute the probability of exceedance.

The ``IMLs`` element (in green in the example) contains the values of shaking used by the engine to compute the 
probability of exceedance in the investigation time. For each site this file contains a ``hazardCurve`` element which 
has the coordinates (longitude and latitude in decimal degrees) of the site and the values of the probability of 
exceedance for all the intensity measure levels specified in the ``IMLs`` element.

If the hazard calculation is configured to produce results including seismic hazard maps and uniform hazard spectra, 
then the list of outputs would display the following::

	user@ubuntu:~$ oq engine --lo <calc_id>
	id | name
	2 | Full Report
	3 | Hazard Curves
	4 | Hazard Maps
	5 | Realizations
	6 | Uniform Hazard Spectra

The first listing below shows a sample of the nrml file used to describe a hazard map, and and the second listing below 
shows a sample of the nrml used to describe a uniform hazard spectrum.::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	  <hazardMap sourceModelTreePath="b1" gsimTreePath="b1"
	             IMT="PGA" investigationTime="50.0" poE="0.1">
	    <node lon="119.596690957" lat="21.5497682591" iml="0.204569990197"/>
	    <node lon="119.596751048" lat="21.6397004197" iml="0.212391638188"/>
	    <node lon="119.596811453" lat="21.7296325803" iml="0.221407505615"/>
	    ...
	  </hazardMap>
	</nrml>

::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	    <uniformHazardSpectra sourceModelTreePath="b1_b2_b4"
	                        gsimTreePath="b1_b2"
	                        investigationTime="50.0" poE="0.1">
	        <periods>0.0 0.025 0.1 0.2</periods>
	        <uhs>
	            <gml:Point>
	                <gml:pos>0.0 0.0</gml:pos>
	            </gml:Point>
	            <IMLs>0.3 0.5 0.2 0.1</IMLs>
	        </uhs>
	        <uhs>
	            <gml:Point>
	                <gml:pos>0.0 1.0</gml:pos>
	            </gml:Point>
	            <IMLs>0.3 0.5 0.2 0.1</IMLs>
	        </uhs>
	    </uniformHazardSpectra>
	</nrml>