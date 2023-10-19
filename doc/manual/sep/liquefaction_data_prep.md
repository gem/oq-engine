# Site characterization for probabilistic liquefaction analysis

There are many methods to calculate the probabilities and displacements that result from liquefaction.  In OpenQuake, we have several models, the methods developed by the US Federal Emergency Management Agency through their HAZUS project, and geospatial methods recently developed by [Zhu et al. (2015)][z15], [Zhu et al. (17)][z17], [Rashidian et al. (2020)][rb20], [Akhlagi et al. (2021)][akh21], [Bozzoni et al. (2021)][b21],[Allstadt et al. (2022)][all22], [Todorovic and Silva (2022)][ts22].

These methods require different input datasets. The HAZUS methods are simplified from older, more comprehensive liquefaction evaluations that would be made at a single site following in-depth geotechnical analysis; the HAZUS methods retain their reliance upon geotechnical parameters that may be measured or inferred at the study sites. The methods by [Zhu et al. (2015)][z15] were developed to only use data that can be derived from a digital elevation model (DEM), but in practice, the datasets must be chosen carefully for the statistical relations to hold. Furthermore, Zhu's methods do not predict displacements from liquefaction, so the HAZUS site characterizations must be used for displacement calculations regardless of the methods used to calculate the probabilities of liquefaction.

## General considerations

### Spatial resolution and accuracy of data and site characterization

Much like traditional seismic hazard analysis, liquefaction analysis may range from low-resolution analysis over broad regions to very high resolution analysis of smaller areas. With advances in computing power, it is possible to run calculations for tens or hundreds of thousands of earthquakes at tens or hundreds of thousands of sites in a short amount of time on a personal computer, giving us the ability to work at a high resolution over a broad area, and considering a very comprehensive suite of earthquake sources. In principle, the methods should be reasonably scale-independent but in practice this isn't always the case.

Two of the major issues that can arise are the limited spatial resolutions of key datasets and the spatial misalignments of different datasets.

Some datasets, particularly those derived from digital elevation models, must be of a specific resolution or source to be used accurately in these calculations. For example, if Vs30 is calculated from slope following methods developed by [Wald and Allen (2007)][wa_07_paper], the slope should be calculated from a DEM with a resolution of around 1 km. Higher resolution DEMs tend to have higher slopes at a given point because the slope is averaged over smaller areas. The mathematical correspondance between slope and Vs30 was developed for DEMs of about 1 km resolution, so if modern DEMs with resolutions of 90 m or less are used, the resulting Vs30 values will be too high.

In and of itself, this is not necessarily a problem.  The issues can arise when the average spacing of the sites is much lower than the resolution of the data, or the characteristics of the sites vary over spatial distances much less than the data, so that important variability between sites is lost.

The misalignment of datasets is another issue. Datasets derived from geologic mapping or other vector-type geospatial data may be made at spatial resolutions much higher or lower than those derived from digital elevation data or other raster geospatial datasets (particularly for 1 km raster data as discussed above). This can cause a situation where irregular geographic or geologic features such as rivers may be in different locations in two datasets, which can 

## HAZUS

### Liquefaction probabilities

The HAZUS methods require several variables to characterize the ground shaking
and the site response:
- Earthquake magnitude
- Peak Ground Acceleration (PGA)
- Liquefaction susceptibility category
- Groundwater depth

The magnitude of the earthquake and the resulting PGA may be calculated by
OpenQuake during a scenario or event-based PSHA, or alternatively from ShakeMap
data or similar for real earthquakes, or through other methods. The earthquake
magnitude should be given as the moment magnitude or work magnitude (*M* or
*M<sub>W</sub>*). PGA should be provided for each site in units of *g* (i.e.,
9.81 m/s<sup>2</sup>).


#### Liquefaction suscepibility category

The HAZUS methods require that each site be assigned into a liquefaction
susceptibility category. These categories are ordinal variables ranging from 'no
susceptibility' to 'very high susceptibility'. The categorization is based on
geologic and geotechnical characteristics of the site, including the age, grain
size and strength of the deposits or rock units.

For a regional probabilistic liquefaction analysis, the categorization will be
based on a geologic map focusing on Quaternary geologic units. The analyst will
typically associate each geologic unit with a liquefaction susceptibility class,
based on the description or characteristics of the unit. (Please note that there
will typically be far fewer geologic units than individual unit polygons or
contiguous regions on a geologic map; the associations described here should
generally work for each unit rather than each polygon.)

Please see the [HAZUS manual][hzm], Section 4-21, for more information on
associating geologic units with susceptibility classes. The descriptions of the
susceptibility classes may not align perfectly with the descriptions of the
geologic units, and therefore the association may have some uncertainty.
Consulting a local or regional geotechnical engineer or geologist may be
helpful. Furthermore, may be prudent to run analyses multiple times, changing
the associations to quantify the effects on the final results, and perhaps
creating a final weighted average of the results.

Once each geologic map unit has been associated with a liquefaction
susceptibility class, each site must be associated with a geologic unit. This is
most readily done through a spatial join operation in a GIS program.

#### Groundwater depth

The groundwater depth parameter is the mean depth from the surface of the soil
to the water table, in meters. Estimation of this parameter from remote sensing
data is quite challenging. It may range from less than a meter near major water
bodies in humid regions to tens of meters in dry, rugged areas. Furthermore,
this value may fluctuate with recent or seasonal rainfall. Sensitivity testing
of this parameter throughout reasonable ranges of uncertainty for each site is
recommended. For large scale application (e.g., in geospatial models), the
ground water depth database compiled by [Fan et al. (2013)][f13] can be used.

### Lateral spreading

The horizontal displacements from lateral spreading may be calculated through
HAZUS methods as well. These calculations do not require additional data or site
characterization. However, if methods are used for calculating liquefaction
probabilities that do not use the HAZUS site classifications (such as Zhu et al
2015), then these classifications will have to be done in order to calculate the
displacements.


## Geospatial models

The geospatial liquefaction models (e.g, [Zhu et al. (2015)][z15], [Zhu et al. (17)][z17]) 
calculates the probability of liquefaction via logistic regression of a few 
variables that are, in principle, easily derived from digital elevation data. 
In practice, there are strict requirements on the spatial resolution and sources 
of these data derivations, and deviations from this will yield values at each site 
that may be quite discrepant from those calculated 'correctly'. This may produce 
very inaccurate liquefaction probabilities, as the logistic coefficients will no 
longer be calibrated correctly.

### Getting raster values at sites

Digital elevation data and its derivatives are often given as rasters. However,
in the case of probabilistic analysis of secondary perils (particularly for risk
analysis) the analyist may need to deal with sites that are not distributed
according to a raster grid.

Raster values may be extracted at sites using a GIS program to perform a spatial
join, but following inconvenient historical precedent, this operation often
produces new data files instead of simply appending the raster values to the
point data file.

Therefore we have implemented a simple function, [`openquake.sep.utils.sample_raster_at_points`]
[srap], to get the raster values. This function requires the filename of the raster, 
and the longitudes and latitudes of the sites, and returns a Numpy array with the 
raster values at each point. This function can be easily incorporated into a Python 
script or workflow in this manner.

### Liquefaction probabilities

Calculating liquefaction probabilities requires values for Vs30 and the Compound
Topographic Index, which is a proxy for soil wetness.

#### Vs30

Zhu et al (2015) calibrated their model on Vs30 data derived from DEMs using the
methods of [Wald and Allen (2007)][wa_07_paper]. 

This method is implemented in the engine [here][wald_allen_07]. It requires
that the slope is calculated as the gradient (dy/dx) rather than an angular
unit, and the study area is categorized as tectonically `active` or `stable`. 

A more general wrapper function has also been written [here][wrapper]. This function can
calculate gradient from the slope in degrees (a more common formulation), and
will be able to use different formulas or relations between slope and Vs30 if
and when those are implemented (we have no current plans for doing so).


#### Soil wetness proxies
A set of candidate proxies are globally available to characterise the soil wetness.
The general model by [Zhu et al. (2015)][z15] and [Bozzoni et al. (2021)][b21] used
the compound topographic index, a proxy for soil wetness that relates the topographic
slope of a point to the upstream drainage area of that point. This index can be obtained
from dataset that has a global range of 0-20 [Marthews et al. (2015)][m15]. In more recent
models, additional proxies were introduced such as distance to the nearest coast available 
[here][dc], distance to the nearest river network available [here][dr], and precipitation
available [here][precip].

[z15]: https://journals.sagepub.com/doi/abs/10.1193/121912EQS353M
[z17]: https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/107/3/1365/354192/An-Updated-Geospatial-Liquefaction-Model-for?redirectedFrom=fulltext 
[rb20]: https://www.sciencedirect.com/science/article/abs/pii/S0013795219312979
[akh21]: https://earthquake.usgs.gov/cfusion/external_grants/reports/G20AP00029.pdf
[b21]: https://link.springer.com/article/10.1007/s10518-020-01008-6
[all22]: https://journals.sagepub.com/doi/10.1177/87552930211032685
[ts22]: https://www.sciencedirect.com/science/article/abs/pii/S0267726122002792
[hzm]: https://www.hsdl.org/?view&did=12760
[wa_07_paper]: https://pubs.geoscienceworld.org/ssa/bssa/article/97/5/1379/146527
[f13]: https://www.science.org/doi/10.1126/science.1229881
[m15]: https://hess.copernicus.org/articles/19/91/2015/
[dc]: https://oceancolor.gsfc.nasa.gov/#
[dr]: https://www.hydrosheds.org/about
[precip]: https://worldclim.org/data/worldclim21.html

[srap]: https://github.com/gem/oq-engine/blob/ef33b5e0dfdca7a214dac99d4d7214086023ab39/openquake/sep/utils.py#L22
[wald_allen_07]: https://github.com/gem/oq-engine/blob/ef33b5e0dfdca7a214dac99d4d7214086023ab39/openquake/sep/utils.py#L260
[wrapper]: https://github.com/gem/oq-engine/blob/ef33b5e0dfdca7a214dac99d4d7214086023ab39/openquake/sep/utils.py#L227
