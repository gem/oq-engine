.. _rupture-model:

Rupture Model
=============

As the scenario calculator does not need to determine the probability of occurrence of the specific rupture, but only 
sufficient information to parameterise the location (as a three-dimensional surface), the magnitude and the style-of-
faulting of the rupture, a more simplified NRML structure is sufficient compared to the source model structures 
described previously in Source typologies. A rupture model XML can be defined in the following formats:

*Simple Fault Rupture* - in which the geometry is defined by the trace of the fault rupture, the dip and the upper and 
lower seismogenic depths. An example is shown in the listing below::

	      <?xml version='1.0' encoding='utf-8'?>
	      <nrml xmlns:gml="http://www.opengis.net/gml"
	            xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	          <simpleFaultRupture>
	            <magnitude>6.7</magnitude>
	            <rake>180.0</rake>
	            <hypocenter lon="-122.02750" lat="37.61744" depth="6.7"/>
	            <simpleFaultGeometry>
	              <gml:LineString>
	                <gml:posList>
	                  -121.80236 37.39713
	                  -121.91453 37.48312
	                  -122.00413 37.59493
	                  -122.05088 37.63995
	                  -122.09226 37.68095
	                  -122.17796 37.78233
	                </gml:posList>
	              </gml:LineString>
	              <dip>76.0</dip>
	              <upperSeismoDepth>0.0</upperSeismoDepth>
	              <lowerSeismoDepth>13.4</lowerSeismoDepth>
	            </simpleFaultGeometry>
	          </simpleFaultRupture>
	
	      </nrml>

*Planar & Multi-Planar Rupture* - in which the geometry is defined as a collection of one or more rectangular planes, 
each defined by four corners. An example of a multi-planar rupture is shown below in the listing below::

	<?xml version='1.0' encoding='utf-8'?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	    <multiPlanesRupture>
	        <magnitude>8.0</magnitude>
	        <rake>90.0</rake>
	        <hypocenter lat="-1.4" lon="1.1" depth="10.0"/>
	            <planarSurface strike="90.0" dip="45.0">
	                <topLeft lon="-0.8" lat="-2.3" depth="0.0" />
	                <topRight lon="-0.4" lat="-2.3" depth="0.0" />
	                <bottomLeft lon="-0.8" lat="-2.3890" depth="10.0" />
	                <bottomRight lon="-0.4" lat="-2.3890" depth="10.0" />
	            </planarSurface>
	            <planarSurface strike="30.94744" dip="30.0">
	                <topLeft lon="-0.42" lat="-2.3" depth="0.0" />
	                <topRight lon="-0.29967" lat="-2.09945" depth="0.0" />
	                <bottomLeft lon="-0.28629" lat="-2.38009" depth="10.0" />
	                <bottomRight lon="-0.16598" lat="-2.17955" depth="10.0" />
	            </planarSurface>
	    </multiPlanesRupture>
	
	</nrml>

*Complex Fault Rupture* - in which the geometry is defined by the upper, lower and (if applicable) intermediate edges 
of the fault rupture. An example of a complex fault rupture is shown below in the listing below::

	<?xml version='1.0' encoding='utf-8'?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	    <complexFaultRupture>
	        <magnitude>8.0</magnitude>
	        <rake>90.0</rake>
	        <hypocenter lat="-1.4" lon="1.1" depth="10.0"/>
	        <complexFaultGeometry>
	            <faultTopEdge>
	                <gml:LineString>
	                    <gml:posList>
	                        0.6 -1.5 2.0
	                        1.0 -1.3 5.0
	                        1.5 -1.0 8.0
	                    </gml:posList>
	                </gml:LineString>
	            </faultTopEdge>
	            <intermediateEdge>
	                <gml:LineString>
	                    <gml:posList>
	                        0.65 -1.55 4.0
	                        1.1  -1.4  10.0
	                        1.5  -1.2  20.0
	                    </gml:posList>
	                </gml:LineString>
	            </intermediateEdge>
	            <faultBottomEdge>
	                <gml:LineString>
	                    <gml:posList>
	                        0.65 -1.7 8.0
	                        1.1  -1.6 15.0
	                        1.5  -1.7 35.0
	                    </gml:posList>
	                </gml:LineString>
	            </faultBottomEdge>
	        </complexFaultGeometry>
	    </complexFaultRupture>
	
	</nrml>