.. _secondary-perils:

Secondary perils
================

Several methodologies exist for calculating probabilities and displacements from secondary perils, such as landslides
and liquefaction. We have implemented multiple models in OpenQuake, each requiring different input datasets, which 
are incorporated in the site model. Performing secondary perils calculations requires 
the adjusted `site_model.csv` in addition to the required files for running event-based or scenario analyses. 
Futhermore, user is asked to define in `job.ini` file which model should be used to perform the analysis using the
parameter ``secondary_perils``. For example, if one wants to use the HAZUS methodology, they should type::
    
    secondary_perils = HazusLiquefaction

The tables below provide a comprehensive list of the liquefaction and landslide models implemented in the OpenQuake engine. 
They detail the Intensity Measure Types (IMTs) utilized by each model, the outputs calculated and the additional site 
model parameters required. 


+---------------------------------+------------------------+----------+-----------------------------------------+
| Model                           | Output                 | IMTs     | Additional parameters in the site model |
+=================================+========================+==========+=========================================+
| HazusLiquefaction               | LiqProb                | PGA, M   | liq_susc_cat, gwd                       |
+---------------------------------+------------------------+----------+-----------------------------------------+
| ZhuEtAl2015LiquefactionGeneral  | LiqProb/LSE, LiqOccur  | PGA, M   | cti, vs30                               |
+---------------------------------+------------------------+----------+-----------------------------------------+
| ZhuEtAl2017LiquefactionCoastal  | LiqProb, LiqOccur, LSE | PGV      | vs30, dr, dc, precip                    |
+---------------------------------+------------------------+----------+-----------------------------------------+
| ZhuEtAl2017LiquefactionGeneral  | LiqProb, LiqOccur, LSE | PGV      | vs30, dw, gwd, precip                   |
+---------------------------------+------------------------+----------+-----------------------------------------+
| RashidianBaise2020Liquefaction  | LiqProb, LiqOccur, LSE | PGV, PGA | vs30, dw, gwd, precip                   |
+---------------------------------+------------------------+----------+-----------------------------------------+
| AllstadtEtAl2022Liquefaction    | LiqProb, LiqOccur, LSE | PGV, PGA | vs30, dw, gwd, precip                   |
+---------------------------------+------------------------+----------+-----------------------------------------+
| AkhlagiEtAl2021LiquefactionA    | LiqProb, LiqOccur      | PGV      | tri, dc, dr, zwb                        |
+---------------------------------+------------------------+----------+-----------------------------------------+
| AkhlagiEtAl2021LiquefactionB    | LiqProb, LiqOccur      | PGV      | vs30, dc, dr, zwb                       |
+---------------------------------+------------------------+----------+-----------------------------------------+
| Bozzoni2021LiquefactionEurope   | LiqProb, LiqOccur      | PGA, M   | cti, vs30                               |
+---------------------------------+------------------------+----------+-----------------------------------------+
| TodorovicSilva2022NonParametric | LiqProb, LiqOccur      | PGV      | vs30, dw, gwd, precip                   |
+---------------------------------+------------------------+----------+-----------------------------------------+
| HazusDeformation                | PGDMax                 | PGA, M   | liq_susc_cat                            |
+---------------------------------+------------------------+----------+-----------------------------------------+



+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| Model                              | Output          | IMTs     | Additional parameters in the site model                                                    |
+====================================+=================+==========+============================================================================================+
| Jibson2007ALandslides              | Disp            | PGA      | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| Jibson2007BLandslides              | Disp            | PGA, M   | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| ChoRathje2022Landslides            | Disp            | PGV      | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness, tslope, hratio |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| FotopoulouPitilakis2015ALandslides | Disp            | PGV, M   | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| FotopoulouPitilakis2015BLandslides | Disp            | PGA, M   | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| FotopoulouPitilakis2015CLandslides | Disp            | PGA, M   | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| FotopoulouPitilakis2015DLandslides | Disp            | PGV, PGA | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| SaygiliRathje2008Landslides        | Disp            | PGV, PGA | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| RathjeSaygili2009Landslides        | Disp            | PGA, M   | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| JibsonEtAl2000Landslides           | Disp, Disp Prob | IA       | slope, cohesion_mid, friction_mid, saturation, dry_density, slab_thickness                 |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| NowickiJessee2018Landslides        | LSProb, LSE     | PGV      | slope, lithology, landcover                                                                |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+
| AllstadtEtAl2022Landslides         | LSProb, LSE     | PGV, PGA | slope, lithology, landcover                                                                |
+------------------------------------+-----------------+----------+--------------------------------------------------------------------------------------------+

Before demonstrating an example of a site model, we first discuss the implemented functions that are useful for 
retrieving relevant inputs for sites.


Getting raster values at sites
------------------------------

Digital elevation data and its derivatives are often given as rasters. However, in the case of probabilistic analysis 
of secondary perils (particularly for risk analysis) the analyst may need to deal with sites that are not distributed 
according to a raster grid.

Raster values may be extracted at sites using a GIS program to perform a spatial join, but following inconvenient 
historical precedent, this operation often produces new data files instead of simply appending the raster values to the 
point data file.

Therefore we have implemented a simple function, `sample_raster_at_points <https://github.com/gem/oq-engine/blob/engine-3.20/openquake/sep/utils.py#L19>`_,
to get the raster values. This function requires the filename of the raster, and the longitudes and latitudes of the 
sites, and returns a Numpy array with the raster values at each point. This function can be easily incorporated into 
a Python script or workflow in this manner.

Additional function for :math:`V_{s30}` estimates, `vs30_from_slope_wald_allen_2007 <https://github.com/gem/oq-engine/blob/engine-3.20/openquake/sep/utils.py#L260>`_ is implemented in the engine. 
It requires that the slope is calculated as the gradient :math:`\frac{dy}{dx}` rather than an angular unit, and the 
study area is categorized as tectonically *active* or *stable*.

We also provide a more general, wrapper function, `slope_angle_to_gradient <https://github.com/gem/oq-engine/blob/engine-3.20/openquake/sep/utils.py#L228>`_. 
This function can calculate gradient from the slope in degrees (a more common formulation), and will be able to use 
different formulas or relations between slope and :math:`V_{s30}` if and when those are implemented.


Site model
----------
Besides usual input required for hazard assessment due to ground-shaking, several additional parameters are required to
supplement the ``site_model.csv``. Before building up the site model, one should refer to the underlying science behind
these analyses and familiarise themselves with additional parameter requirements, as different models may require
different parameters. Below we present an example of a site model including several parameters that are characterising 
soil density and wetness.

``site_model.csv``

+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
| **site_id** | **lon** | **lat** | **slope** | **liq_susc_cat** | **vs30** | **gwd** | **dr** | **dc** | **precip** |
+=============+=========+=========+===========+==================+==========+=========+========+========+============+
|      0      | -76.50  |  3.465  |   1.9321  |         h        |   270    |   0.3   |  0.36  |   73   |    2040    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
|      1      | -76.53  |  3.448  |   2.6499  |         l        |   425    |   1.25  |  0.39  |   70   |    1548    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
|      2      | -76.48  |  3.473  |   0.4687  |         h        |   270    |   0.3   |  0.04  |   74   |    1992    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
|      3      | -76.55  |  3.403  |   41.366  |         l        |   330    |   1.75  |  0.06  |   70   |    1788    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
|      4      | -76.48  |  3.434  |   3.2612  |         h        |   270    |   0.3   |  0.19  |   75   |    1352    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
|      5      | -76.47  |  3.407  |   3.4565  |         h        |   210    |   0.3   |  0.38  |   78   |    1588    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
|      6      | -76.55  |  3.406  |   13.859  |         l        |   270    |   1.75  |  0.51  |   69   |    1692    |
+-------------+---------+---------+-----------+------------------+----------+---------+--------+--------+------------+
