Scenario Based Seismic Hazard Analysis
======================================

In case of Scenario Based Seismic Hazard Analysis, the engine simulates a set of ground motion fields (GMFs) at the 
target sites for the requested set of intensity measure types. This set of GMFs can then be used in :ref:`Scenario Damage 
Assessment <scenario-damage-assessment>` and :ref:`Scenario Risk Assessment <scenario-risk-assessment>` to estimate the 
distribution of potential damage, economic losses, fatalities, and other consequences. The scenario calculator is 
useful for simulating both historical and hypothetical earthquakes.

In case of Scenario Based Seismic Hazard Analysis, The input data consist of a single earthquake rupture model and one 
or more ground-motion models (GSIMs). Using the Ground Motion Field Calculator, multiple realizations of ground shaking 
can be computed, each realization sampling the aleatory uncertainties in the ground-motion model. The main calculator 
used to perform this analysis is the Ground Motion Field Calculator, which was already introduced during the description 
of the event based PSHA workflow (see Section :ref:`Event based PSHA <event-based-psha>`).

Starting from OpenQuake engine v3.16, it is possible to condition the ground shaking to observations, such as ground 
motion recordings and macroseismic intensity observations. The simulated ground motion fields are cross-spatially 
correlated, and can reduce considerably the uncertainty and bias in the resulting loss and damage estimates. The 
implementation of the conditioning of ground motion fields in the engine was performed following closely the procedure 
proposed by Engler et al. (2022).

As the scenario calculator does not need to determine the probability of occurrence of the specific rupture, but only 
sufficient information to parameterise the location (as a three-dimensional surface), the magnitude and the 
style-of-faulting of the rupture, a more simplified NRML structure is sufficient compared to the source model structures 
described in :ref:`source typologies <source-typologies>`. A rupture model XML can be defined in the following formats:

1. *Simple Fault Rupture* - in which the geometry is defined by the trace of the fault rupture, the dip and the upper and lower seismogenic depths. An example is shown in the listing below::

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

2. *Planar & Multi-Planar Rupture* - in which the geometry is defined as a collection of one or more rectangular planes, each defined by four corners. An example of a multi-planar rupture is shown below in the listing below::

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

3. *Complex Fault Rupture* - in which the geometry is defined by the upper, lower and (if applicable) intermediate edges of the fault rupture. An example of a complex fault rupture is shown below in the listing below::

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

The concept of “mean” ground motion field
-----------------------------------------

The engine has at least three different kinds of mean ground motion field, computed 
differently and used in different situations:

Mean ground motion field by GMPE, used to reduce disk space and make risk 
calculations faster.

Mean ground motion field by event, used for debugging/plotting purposes.

Single-rupture hazardlib mean ground motion field, used for analysis/plotting 
purposes.

Mean ground motion field by GMPE
********************************

This is the most useful concept for people doing risk calculations. To be concrete, 
suppose you are running a *scenario_risk* calculation on a region where you have a 
very fine site model (say at 1 km resolution) and a sophisticated hazard model 
(say with 16 different GMPEs): then you can easily end up with a pretty large 
calculation. For instance one of our users was doing such a calculation with an 
exposure of 1.2 million assets, 50,000+ hazard sites, 5 intensity measure levels 
and 1000 simulations, corresponding to 16,000 events given that there are 16 GMPEs. 
Given that each ground motion value needs 4 bytes to be stored as a 32 bit float, 
the math tells us that such calculation will generate 50000 x 16000 x 5 x 4 ~ 15 
GB of data (it could be a but less by using the ``minimum_intensity`` feature, but 
you get the order of magnitude). This is very little for the engine that can 
store such an amount of data in less than 1 minute, but it is a huge amount of 
data for a database. If you a (re)insurance company and your workflow requires 
ingesting the GMFs in a database to compute the financial losses, that’s a big 
issue. The engine could compute the hazard in just an hour, but the risk part 
could easily take 8 days. This is a no-go for most companies. They have deadlines 
and cannot way 8 days to perform a single analysis. At the end they are interested 
only in the mean losses, so they would like to have a single effective mean field 
producing something close to the mean losses that more correctly would be obtained 
by considering all 16 realizations. With a single effective realization the data 
storage would drop under 1 GB and more significantly the financial model software 
would complete the calculation in 12 hours instead of 8 days, something a lot 
more reasonable.

For this kind of situations hazardlib provides an ``AvgGMPE`` class, that allows to 
replace a set of GMPEs with a single effective GMPE. More specifically, the 
method ``AvgGMPE.get_means_and_stddevs`` calls the methods ``.get_means_and_stddevs`` 
on the underlying GMPEs and performs a weighted average of the means and a weighted 
average of the variances using the usual formulas:

.. math::

 \mu = \sum_{i}\omega_{i}\mu_{i}

.. math::

 \sigma^2 = \sum_{i}\omega_{i}(\sigma_{i})^2

where the weights sum up to 1. It is up to the user to check how big is the 
difference in the risk between the complete calculation and the mean field 
calculation. A factor of 2 discrepancies would not be surprising, but we have 
also seen situations where there is no difference within the uncertainty due to 
the random seed choice.

Mean ground motion field by event
*********************************

Using the *AvgGMPE* trick does not solve the issue of visualizing the ground motion 
fields, since for each site there are still 1000 events. A plotting tool has still 
to download 1 GB of data and then one has to decide which event to plot. The 
situation is the same if you are doing a sensitivity analysis, i.e. you are 
changing some parameter (it could be a parameter of the underlying rupture, or 
even the random seed) and you are studying how the ground motion fields change. 
It is hard to compare two sets of data of 1 GB each. Instead, it is a lot easier 
to define a “mean” ground motion field obtained by averaging on the events and then 
compare the mean fields of the two calculations: if they are very different, it is 
clear that the calculation is very sensitive to the parameter being studied. Still, 
the tool performing the comparison will need to consider 1000 times less data and 
will be 1000 times faster, also downloding 1000 times less data from the remote 
server where the calculation has been performed.

For this kind of analysis the engine provides an internal output ``avg_gmf`` that can 
be plotted with the command ``oq plot avg_gmf <calc_id>``. It is also possible to 
compare two calculations with the command ``$ oq compare avg_gmf imt <calc1> <calc2>``
Since ``avg_gmf`` is meant for internal usage and for debugging it is not exported 
by default and it is not visible in the WebUI. It is also not guaranteed to stay 
the same across engine versions. It is available starting from version 3.11. It 
should be noted that, consistently with how the ``AvgGMPE`` works, the ``avg_gmf`` 
output is computed in *log space*, i.e. it is geometric mean, not the usual mean. 
If the distribution was exactly lognormal that would also coincide with the median 
field.

However, you should remember that in order to reduce the data transfer and to 
save disk space the engine discards ground motion values below a certain minimum 
intensity, determined explicitly by the user or inferred from the vulnerability 
functions when performing a risk calculation: there is no point in considering 
ground motion values below the minimum in the vulnerability functions, since they 
would generate zero losses. Discarding the values below the threshould breaks the 
log normal distribution.

To be concrete, consider a case with a single site, and single intensity measure 
type (PGA) and a ``minimum_intensity`` of 0.05g. Suppose there are 1000 simulations 
and that you have a normal distribution of the logarithms with :math:`\mu = -2.0,  \sigma=.5`; 
then the ground motion values that you could obtain would be as follows::

	>>> import numpy
	>>> np.random.seed(42) # fix the seed
	>>> gmvs = np.random.lognormal(mean=-2.0, sigma=.5, size=1000)

As expected, the variability of the values is rather large, spanning more than 
one order of magnitude::

	>>> numpy.round([gmvs.min(), np.median(gmvs), gmvs.max()], 6)
	array([0.026766, 0.137058, 0.929011])

Also mean and standard deviation of the logarithms are very close to the expected 
values :math:`\mu = -2.0,  \sigma=.5`::

	>>> round(np.log(gmvs).mean(), 6)
	-1.990334
	>>> round(np.log(gmvs).std(), 6)
	0.489363

The geometric mean of the values (i.e. the exponential of the mean of the 
logarithms) is very close to the median, as expected for a lognormal distribution::

	>>> round(np.exp(np.log(gmvs).mean()), 6)
	0.13665

All these properties are broken when the ground motion values are truncated 
below the ``minimum_intensity``::

	>>> gmvs[gmvs < .05] = .05
	>>> round(np.log(gmvs).mean(), 6)
	-1.987608
	>>> round(np.log(gmvs).std(), 6)
	0.4828063
	>>> round(np.exp(np.log(gmvs).mean()), 6)
	0.137023

In this case the difference is minor, but if the number of simulations is small 
and/or the :math:`\sigma` is large the mean and standard deviation obtained from 
the logarithms of the ground motion fields could be quite different from the 
expected ones.

Finally, it should be noticed that the geometric mean can be orders of magnitude 
different from the usual mean and it is purely a coincidence that in this case 
they are close (~0.137 vs ~0.155).

Single-rupture estimated median ground motion field
***************************************************

The mean ground motion field by event discussed above is an a posteriori output: 
after performing the calculation, some statistics are performed on the stored 
ground motion fields. However, in the case of a single rupture it is possible to 
estimate the geometric mean and the geometric standard deviation a priori, using 
hazardlib and without performing a full calculation. However, there are some 
limitations to this approach:

1. it only works when there is a single rupture
2. you have to manage the ``minimum_intensity`` manually if you want to compare with a concrete engine output
3. it is good for estimates, it gives you the theoretical ground ground motion field but not the ones concretely generated by the engine fixed a specific seed

It should also be noticed that there is a shortcut to compute the single-rupture 
hazardlib “mean” ground motion field without writing any code; just set in your 
``job.ini`` the following values::

	truncation_level = 0
	ground_motion_fields = 1

Setting ``truncation_level = 0`` effectively replaces the lognormal distribution 
with a delta function, so the generated ground motion fields will be all equal, 
with the same value for all events: this is why you can set ``ground_motion_fields = 1``, 
since you would just waste time and space by generating multiple copies.

Finally let’s warn again on the term hazardlib “mean” ground motion field: in log 
space it is truly a mean, but in terms of the original GMFs it is a geometric mean 
- which is the same as the median since the distribution is lognormal - so you can 
also call this the hazardlib median ground motion field.

Case study: GMFs for California
*******************************

We had an user asking for the GMFs of California on 707,920 hazard sites, using 
the UCERF mean model and an investigation time of 100,000 years. Is this feasible 
or not? Some back of the envelope calculations suggests that it is unfeasible, 
but reality can be different.

The relevant parameters are the following::

	N = 707,920 hazard sites
	E = 10^5 estimated events of magnitude greater then 5.5 in the investigation
	    time of 100,000 years
	B = 1 number of branches in the UCERF logic tree
	G = 5 number of GSIMS in the GMPE logic tree
	I = 6 number of intensity measure types
	S1 = 13 number of bytes used by the engine to store a single GMV

The maximum size of generated GMFs is ``N * E * B * G * I * S1 = 25 TB (terabytes)``
Storing and sharing 25 TB of data is a big issue, so the problem seems without 
solution. However, most of the ground motion values are zero, because there is a 
maximum distance of 300 km and a rupture cannot affect all of the sites. So the 
size of the GMFs should be less than 25 TB. Moreover, if you want to use such GMFs 
for a damage analysis, you may want to discard very small shaking that will not 
cause any damage to your buildings. The engine has a parameter to discard all 
GMFs below a minimum threshold, the ``minimum_intensity`` parameter. The higher the 
threshold, the smaller the size of the GMFs. By playing with that parameter you 
can reduce the size of the output by orders of magnitudes. Terabytes could easily 
become gigabytes with a well chosen threshold.

In practice, we were able to run the full 707,920 sites by splitting the sites in 
70 tiles and by using a minimum intensity of 0.1 g. This was the limit 
configuration for our cluster which has 5 machines with 128 GB of RAM each.

The full calculation was completed in only 4 hours because our calculators are 
highly optimized. The total size of the generated HDF5 files was of 400 GB. This 
is a lot less than 25 TB, but still too large for sharing purposes.

Another way to reduce the output is to reduce the number of intensity measure 
types. Currently in your calculations there are 6 of them (PGA, SA(0.1), SA(0.2), 
SA(0.5), SA(1.0), SA(2.0)) but if you restrict yourself to only PGA the 
computation and the output will become 6 times smaller. Also, there are 5 GMPEs: 
if you restrict yourself to 1 GMPE you gain a factor of 5. Similarly, you can 
reduce the investigation period from 100,000 year to 10,000 years, thus gaining 
another order of magnitude. Also, raising the minimum magnitude reduces the 
number of events significantly.

But the best approach is to be smart. For instance, we know from experience that 
if the final goal is to estimate the total loss for a given exposure, the correct 
way to do that is to aggregate the exposure on a smaller number of hazard sites. 
For instance, instead of the original 707,920 hazard sites we could aggregate on 
only ~7,000 hazard sites and we would a calculation which is 100 times faster, 
produces 100 times less GMFs and still produces a good estimate for the total loss.

In short, risk calculations for the mean field UCERF model are routines now, in 
spite of what the naive expectations could be.

.. _scenarios-from-shakemaps:

Scenarios from ShakeMaps
------------------------

Beginning with version 3.1, the engine is able to perform *scenario_risk* and 
*scenario_damage* calculations starting from the GeoJSON feed for `ShakeMaps <https://earthquake.usgs.gov/data/shakemap/>`__
provided by the United States Geological Survey (USGS). Furthermore, starting 
from version 3.12 it is possible to use ShakeMaps from other sources like the 
local filesystem or a custom URL.

Running the Calculation
***********************

In order to enable this functionality one has to prepare a parent calculation 
containing the exposure and risk functions for the region of interest, say Peru. 
To that aim the user will need to write a prepare ``job.ini`` file like this one::

	[general]
	description = Peru - Preloading exposure and vulnerability
	calculation_mode = scenario
	exposure_file = exposure_model.xml
	structural_vulnerability_file = structural_vulnerability_model.xml

By running the calculation::

	$ oq engine --run prepare_job.ini

The exposure and the risk functions will be imported in the datastore.

This example only includes vulnerability functions for the loss type ``structural``, 
but one could also have in this preparatory job file the functions for 
nonstructural components and contents, and occupants, or fragility functions if 
damage calculations are of interest.

It is essential that each fragility/vulnerability function in the risk model 
should be conditioned on one of the intensity measure types that are supported 
by the ShakeMap service – MMI, PGV, PGA, SA(0.3), SA(1.0), and SA(3.0). If your 
fragility/vulnerability functions involves an intensity measure type which is 
not supported by the ShakeMap system (for instance SA(0.6)) the calculation will 
terminate with an error.

Let’s suppose that the calculation ID of this ‘pre’ calculation is 1000. We can 
now run the risk calculation starting from a ShakeMap. For that, one need a ``job.ini`` 
file like the following::

	[general]
	description = Peru - 2007 M8.0 Pisco earthquake losses
	calculation_mode = scenario_risk
	number_of_ground_motion_fields = 10
	truncation_level = 3
	shakemap_id = usp000fjta
	spatial_correlation = yes
	cross_correlation = yes

This example refers to the 2007 Mw8.0 Pisco earthquake in Peru 
(see https://earthquake.usgs.gov/earthquakes/eventpage/usp000fjta#shakemap). 
The risk can be computed by running the risk job file against the prepared 
calculation::

	$ oq engine --run job.ini --hc 1000

Starting from version 3.12 it is also possible to specify the following sources 
instead of a *shakemap_id*::

	# (1) from local files:
	shakemap_uri = {
	      "kind": "usgs_xml",
	      "grid_url": "relative/path/file.xml",
	      "uncertainty_url": "relative/path/file.xml"
	      }
	
	# (2) from remote files:
	shakemap_uri = {
	      "kind": "usgs_xml",
	      "grid_url": "https://url.to/grid.xml",
	      "uncertainty_url": "https://url.to/uncertainty.zip"
	      }
	
	# (3) both files in a single archive
	# containing grid.xml, uncertainty.xml:
	shakemap_uri = {
	      "kind": "usgs_xml",
	      "grid_url": "relative/path/grid.zip"
	      }

While it is also possible to define absolute paths, it is advised not to do so 
since using absolute paths will make your calculation not portable across 
different machines.

The files must be valid *.xml* USGS ShakeMaps (1). One or both files can also be 
passed as *.zip* archives containing a single valid xml ShakeMap (2). If both files 
are in the same *.zip*, the archived files *must* be named ``grid.xml`` and ``uncertainty.xml``.

Also starting from version 3.12 it is possible to use ESRI Shapefiles in the same 
manner as ShakeMaps. Polygons define areas with the same intensity levels and 
assets/sites will be associated to a polygon if contained by the latter. Sites 
outside of a polygon will be discarded. Shapefile inputs can be specified similar 
to ShakeMaps::

	shakemap_uri = {
	   "kind": "shapefile",
	   "fname": "path_to/file.shp"
	}

It is only necessary to specify one of the available files, and the rest of the 
files will be expected to be in the same location. It is also possible to have 
them contained together in a *.zip* file. There are at least a *.shp-main* file 
and a *.dbf-dBASE* file required. The record field names, intensity measure types 
and units all need to be the same as with regular USGS ShakeMaps.

Irrespective of the input, the engine will perform the following operations:

1. download the ShakeMap and convert it into a format suitable for further processing, i.e. a ShakeMaps array with lon, lat fields
2. the ShakeMap array will be associated to the hazard sites in the region covered by the ShakeMap
3. by using the parameters ``truncation_level`` and ``number_of_ground_motion_fields`` a set of ground motion fields (GMFs) following the truncated Gaussian distribution will be generated and stored in the datastore
4. a regular risk calculation will be performed by using such GMFs and the assets within the region covered by the shakemap.

Correlation
***********

By default the engine tries to compute both the spatial correlation and the cross 
correlation between different intensity measure types. Please note that if you 
are using MMI as intensity measure type in your vulnerability model, it is not 
possible to apply correlations since those are based on physical measures.

For each kind of correlation you have three choices, that you can set in the 
*job.ini*, for a total of nine combinations::

	- spatial_correlation = yes, cross_correlation = yes  # the default
	- spatial_correlation = no, cross_correlation = no   # disable everything
	- spatial_correlation = yes, cross_correlation = no
	- spatial_correlation = no, cross_correlation = yes
	- spatial_correlation = full, cross_correlation = full
	- spatial_correlation = yes, cross_correlation = full
	- spatial_correlation = no, cross_correlation = full
	- spatial_correlation = full, cross_correlation = no
	- spatial_correlation = full, cross_correlation = yes

yes means using the correlation matrix of the `Silva-Horspool <https://onlinelibrary.wiley.com/doi/abs/10.1002/eqe.3154>`__
paper; *no* mean using no correlation; *full* means using an all-ones correlation 
matrix.

Apart from performance considerations, disabling either the spatial correlation 
or the cross correlation (or both) might be useful to see how significant the 
effect of the correlation is on the damage/loss estimates.

In particular, due to numeric errors, the spatial correlation matrix - that by 
construction contains only positive numbers - can still produce small negative 
eigenvalues (of the order of -1E-15) and the calculation fails with an error 
message saying that the correlation matrix is not positive defined. Welcome to 
the world of floating point approximation! Rather than magically discarding 
negative eigenvalues the engine raises an error and the user has two choices: 
either disable the spatial correlation or reduce the number of sites because 
that can make the numerical instability go away. The easiest way to reduce the 
number of sites is setting a *region_grid_spacing* parameter in the *prepare_job.ini* 
file, then the engine will automatically put the assets on a grid. The larger the 
grid spacing, the fewer the number of points, and the closer the calculation will 
be to tractability.

Performance Considerations
**************************

The performance of the calculation will be crucially determined by the number of 
hazard sites. For instance, in the case of the Pisco earthquake the ShakeMap has 
506,142 sites, which is a significantly large number of sites. However, the extent 
of the ShakeMap in longitude and latitude is about 6 degrees, with a step of 10 
km the grid contains around 65 x 65 sites; most of the sites are without assets 
because most of the grid is on the sea or on high mountains, so actually there 
are around ~500 effective sites. Computing a correlation matrix of size 500 x 500 
is feasible, so the risk computation can be performed.

Clearly in situations in which the number of hazard sites is too large, 
approximations will have to be made such as using a larger *region_grid_spacing*. 
Disabling spatial AND cross correlation makes it possible run much larger 
calculations. The performance can be further increased by not using a ``truncation_level``.

When applying correlation, a soft cap on the size of the calculations is defined. 
This is done and modifiable through the parameter ``cholesky_limit`` which refers to 
the number of sites multiplied by the number of intensity measure types used in 
the vulnerability model. Raising that limit is at your own peril, as you might 
run out of memory during calculation or may encounter instabilities in the 
calculations as described above.

If the ground motion values or the standard deviations are particularly large, 
the user will get a warning about suspicious GMFs.

Moreover, especially for old ShakeMaps, the USGS can provide them in a format 
that the engine cannot read.

Thus, this feature is not expected to work in all cases.

The concept of “mean” ground motion field
The engine has at least three different kinds of mean ground motion field, computed differently and used in different situations:

Mean ground motion field by GMPE, used to reduce disk space and make risk calculations faster.

Mean ground motion field by event, used for debugging/plotting purposes.

Single-rupture hazardlib mean ground motion field, used for analysis/plotting purposes.