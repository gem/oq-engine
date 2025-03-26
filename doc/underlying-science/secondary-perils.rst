Liquefaction and Landslide
==========================

Landslides and liquefaction are well-known perils that accompany earthquakes. Basic models to describe their occurrence 
have been around for decades and are constantly improving. However, these models have rarely been incorporated into 
PSHA.

The tools presented here are implementations of some of the more common and appropriate secondary perils models. The 
intention is seamless incorporation of these models into PSH(R)A calculations done through the OpenQuake Engine, though 
the incorporation is a work in progress. 

In what follows, we provide a brief overview of the implemented models, preceded by general considerations on the 
spatial resolution at which these analyses are typically conducted. For more in-depth information on the geospatial 
models, we recommend referring to the original studies. Additionally, we offer corresponding demonstration analyses, 
which can be found in the  `demos section <https://github.com/gem/oq-engine/tree/master/demos>`_) of our GitHub 
repository. We encourage users to check them out and and familiarize themselves with the required inputs for performing
liquefaction or landslide assessment. We also provide tools to extract relevant information from digital elevation data
and its derivatives, which are often given as rasters.


General considerations
----------------------


*****************************************************************
Spatial resolution and accuracy of data and site characterization
*****************************************************************

Much like traditional seismic hazard analysis, liquefaction analysis may range from low-resolution analysis over broad 
regions to very high resolution analysis of smaller areas. With advances in computing power, it is possible to run 
calculations for tens or hundreds of thousands of earthquakes at tens or hundreds of thousands of sites in a short 
amount of time on a personal computer, giving us the ability to work at a high resolution over a broad area, and 
considering a very comprehensive suite of earthquake sources. In principle, the methods should be reasonably 
scale-independent but in practice this isn't always the case.

Two of the major issues that can arise are the limited spatial resolutions of key datasets and the spatial misalignments 
of different datasets.

Some datasets, particularly those derived from digital elevation models, must be of a specific resolution or source to 
be used accurately in these calculations. As we will see in the coming sections of this document, a common proxy to 
most of the geospatial models is shear wave velocity in the top :math:`30 \, \text{m}`. For example, if :math:`V_{s30}` 
is calculated from slope following methods developed by `Wald and Allen (2007) <https://pubs.geoscienceworld.org/ssa/bssa/article/97/5/1379/146527>`_, 
the slope should be calculated from a DEM with a resolution of around 1 km. Higher resolution DEMs tend to have higher 
slopes at a given point because the slope is averaged over smaller areas. The mathematical correspondance between slope 
and :math:`V_{s30}` was developed for DEMs of about 1 km resolution, so if modern DEMs with resolutions of 90 m or less 
are used, the resulting :math:`V_{s30}` values will be too high.

In and of itself, this is not necessarily a problem. The issues can arise when the average spacing of the sites is much 
lower than the resolution of the data, or the characteristics of the sites vary over spatial distances much less than 
the data, so that important variability between sites is lost.


Liquefaction models
-------------------

Several liquefaction models are implemented in the OpenQuake-engine, as detailed in the table under 
`Input models for Secondary Perils <https://docs.openquake.org/oq-engine/master/manual/user-guide/inputs/secondary-perils-inputs.html>`_

One of them models is the method developed for the HAZUS 
software by the US Federal Emergency Management Agency. This model involves categorization of sites into liquefaction 
susceptibility classes based on geotechnical characteristics, and a quantitative probability model for each 
susceptibility class. The remaining models are the academic geospatial models, i.e., statistical models that use 
globally available input variables as first-order proxies to characterise saturation and density properties of the 
soil. The shaking component is expressed either in terms of Peak Ground Acceleration , :math:`PGA`, or Peak Ground 
Velocity , :math:`PGV`. These methods are simplified from older, more comprehensive liquefaction evaluations 
performed at a single site following in-depth geotechnical analysis.

*****
HAZUS
*****

The HAZUS model (see `HAZUS manual <https://www.hsdl.org/?view&did=12760>`_) classifies each site into a liquefaction 
susceptibility class, :math:`LSC`, based on the geologic and geotechnical characteristics of the site, such as the 
sedimentological type and the deposition age of the unit. Note that descriptions of the susceptibility classes may not 
align perfectly with the descriptions of the geologic units.
In addition to the :math:`LSC` and the local ground 
acceleration at each site, the depth to groundwater at the site and the magnitude of the causative earthquake will 
affect the probability that a given site will experience liquefaction.

The equation that describes this probability is:

.. math::

	P(L) = \frac{P(L | PGA=a) \cdot P_{ml}}{K_m K_w} \\ (1)

:math:`P(L|PGA=a)` is the conditional probability that a site will fail based on the :math:`PGA` and the :math:`LSC`. 
:math:`P_{ml}` is the fraction of the total mapped area that will experience liquefaction if :math:`P(L|PGA=a)` reaches
1. These terms both have :math:`LSC`-specific coefficients; these are shown in Table 1.

:math:`K_m` is a magnitude-correction factor that scales :math:`P(L)` for earthquake magnitudes other than :math:`M7.5` 
potentially to account for the duration of shaking (longer shaking increases liquefaction probability). :math:`K_w` is 
a groundwater depth correction factor (shallower groundwater increases liquefaction probability).

+----------------+-----------------------+-------------------------+-----------------------+--------------------+
|   :math:`LSC`  |   :math:`PGA_{min}`   |   :math:`PGA_{slope}`   |   :math:`PGA_{int}`   |   :math:`P_{ml}`   |
+================+=======================+=========================+=======================+====================+
| very high      |         0.09          |         9.09            |        0.82           |         0.25       |
+----------------+-----------------------+-------------------------+-----------------------+--------------------+
| high           |         0.12          |         7.67            |        0.92           |         0.2        |
+----------------+-----------------------+-------------------------+-----------------------+--------------------+
| moderate       |         0.15          |         6.67            |        1.0            |         0.1        |
+----------------+-----------------------+-------------------------+-----------------------+--------------------+
| low            |         0.21          |         5.57            |        1.18           |         0.05       |
+----------------+-----------------------+-------------------------+-----------------------+--------------------+
| very low       |         0.26          |         4.16            |        1.08           |         0.02       |
+----------------+-----------------------+-------------------------+-----------------------+--------------------+
| none           |     :math:`\infty`    |         0.0             |        0.0            |         0.0        |
+----------------+-----------------------+-------------------------+-----------------------+--------------------+

Table 1: Liquefaction values for different liquefaction susceptibility categories, :math:`LSC`. :math:`PGA_{min}` is 
the minimum ground acceleration required to initiate liquefaction. :math:`PGA_{slope}` is the slope of the liquefaction
probability curve as a function of :math:`PGA`, and :math:`PGA_{int}` is the y-intercept of that curve. :math:`P_{ml}` 
is the Map Area Proportion, which gives the area of liquefaction within each map unit conditional on liquefaction 
occurring in the map unit.

*****************
Geospatial models
*****************

#################
Zhu et al. (2015)
#################

The model by `Zhu et al. (2015) <https://journals.sagepub.com/doi/abs/10.1193/121912EQS353M>`_, is a logistic 
regression model requiring specification of the :math:`V_{s30} \, [\text{m/s}]`, the Compound Topographic 
Index, :math:`CTI`, a proxy for soil wetness or groundwater depth, :math:`gwd \, [\text{m}]`, 
the :math:`PGA_{M,SM} \, [\text{g}]` experienced at a site, and the magnitude of the causative earthquake.

The model is quite simple. An explanatory variable :math:`X` is calculated as:

.. math::

	X = 24.1 + 2.067\, ln\, PGA_{M,SM} + 0.355\,CTI - 4.784\, ln\, V_{s30} \\ (2)

and the final probability is the logistic function:

.. math::

	P(L) = \frac{1}{1+e^X} \\ (3)

The term :math:`PGA_{M,SM}` is the :math:`PGA` corrected by magnitude scaling factor, :math:`MSF`, that serves as proxy
for earthquake duration. The :math:`MSF` is calculated as per `Youd et al. (2001) 
<https://ascelibrary.org/doi/10.1061/%28ASCE%291090-0241%282001%29127%3A4%28297%29>`_:

.. math::

	MSF = \frac{10^{2.24}}{M^{2.56}} \\ (4)

Both the :math:`CTI` and the :math:`V_{s30}` may be derived from digital elevation data. The :math:`Vs30` may be
estimated from the topographic slope through the equations of `Wald and Allen (2007) 
<https://pubs.geoscienceworld.org/ssa/bssa/article/97/5/1379/146527>`_, which uses a very low resolution DEM compared
to modern offerings. As topographic slope tends to increase with increased DEM resolution, the estimated :math:`Vs30`
does too; therefore a low-resolution DEM (i.e., a 1 km resolution) must be used to calculate :math:`Vs30`, rather than
the 30 m DEM that is the current standard. This results in a more accurate :math:`Vs30` for a given slope measurement,
but it also means that in an urban setting, sub-km-scale variations in slope are not accounted for.

The :math:`CTI` (`Moore et al., 1991 <https://onlinelibrary.wiley.com/doi/10.1002/hyp.3360050103>`_) is a proxy for
soil wetness that relates the topographic slope of a point to the upstream drainage area of that point, through the
relation:

.. math::

	CTI = \ln (d_a / \tan \delta) \\ (5)

where :math:`d_{a}` is the upstream drainage area per unit width through the flow direction (i.e. relating to the DEM 
resolution). It ranges from :math:`0` to :math:`20`. It was developed for hillslopes, and is not meaningful in certain
very flat areas such as the valley floors of major low-gradient rivers, where the upstream drainage areas are very 
large. Unfortunately, this is exactly where liquefaction is most expected away from coastal settings. 

Model's prediction can be transformed into binary class (liquefaction occurrence or nonoccurrence) via probability 
threshold value. The authors proposed a threshold of 0.2.

#####################
Bozzoni et al. (2021)
#####################

The parametric model developed by `Bozzoni et al. (2021) <https://link.springer.com/article/10.1007/s10518-020-01008-6>`_,
keeps the same input variables (i.e., :math:`PGA_{M,SM}`, :math:`CTI`, :math:`V_{s30}`) and functional form as in 
`Zhu et al. (2015) <https://journals.sagepub.com/doi/abs/10.1193/121912EQS353M>`_. Regression parameters are calibrated 
based on the liquefaction case histories observed during seismic events in Europe. The implemented model is associated 
with the ADASYN sampling algorithm. The explanatory variable :math:`X` is computed as:

.. math::

	X = -11.489 + 3.864\, ln\, PGA_{M} + 2.328\,CTI - 0.091\, ln\, V_{s30} \\ (6)

and the probability of liquefaction in calculated using equation (3).

The adopted probability threshold of 0.57 converts the probability of liquefaction into binary outcome.

#################
Zhu et al. (2017)
#################

Two parametric models, a coastal model (Model 1), and a more general model (Model 2) are proposed by 
`Zhu et al. (2017) <https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/107/3/1365/354192/An-Updated-Geospatial-Liquefaction-Model-for?redirectedFrom=fulltext>`_. 
A coastal event is defined as one where the liquefaction occurrences are, on average, within 20 km of the coast; or, 
for earthquakes with insignificant or no liquefaction, epicentral distances less than 50 km.The implemented geospatial 
models are for global use. An extended set of input parameters is used to describe soil properties (its density and 
wetness). The ground shaking is characterised by :math:`PGV \, [\text{cm/s}]`. Soil density is described by 
:math:`V_{s30} \, [\text{m/s}]`. Soil wetness in Model 1 is chatacterised by a set of features: mean annual 
precipitation, :math:`precip \, [\text{mm}]`, distance to the coast, :math:`d_{c} \, [\text{km}]`, and distance to the 
river, :math:`d_{r} \, [\text{km}]`. Distance to the coast also indicates the geologic age - younger deposits are found
near the coast. Soil wetness in Model 2 is characterised by closest distance to the water body, 
:math:`d_{w} \, [\text{km}]`, which is determined as :math:`\min(d_{c}, d_{r})`, and the ground water table depth, 
:math:`gwd \, [\text{m}]`. Mean annual precipitation is from a global layer developed by `Hijmans et al. (2005) 
<https://rmets.onlinelibrary.wiley.com/doi/10.1002/joc.1276>`_. Distance to the nearest river is calculated based on the 
HydroSHEDS database by `Lehner et al. 2008 <https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2008eo100001>`_. 
Water table depth is retreived from a global dataset by `Fan et al (2013) <https://www.science.org/doi/10.1126/science.1229881>`_. 
Distance to the nearest coastline data was computed from `Ocean Color <https://oceancolor.gsfc.nasa.gov>`_.

The explanatory varibale :math:`X` is calculated as:

Model 1:

.. math:: 

   X = 12.435 + 0.301 \ln(PGV) - 2.615 \ln(V_{s30}) + 0.0005556 precip \quad

.. math:: 

   -0.0287 \sqrt{d_{c}} + 0.0666 d_{r} - 0.0369 \sqrt{d_{c}} \cdot d_{r} \\ (7)


Model 2: 

.. math:: 

   X = 8.801 + 0.334 \ln(PGV) - 1.918 \ln(V_{s30}) + 0.0005408 precip \quad

.. math:: 

   -0.2054 d_{w} - 0.0333 wtd \\ (8)

and the probability of liquefaction is calculated using equation (3). Zero probability is heuristically assigned if 
:math:`PGV < 3 \, \text{cm/s}` or :math:`V_{s30} > 620 \, \text{m/s}`.

The proposed probability threshold to convert to class outcome is 0.4.

Another model's outcome is liquefaction spatial extent, :math:`LSE`. After an earthquake LSE is the spatial area 
covered by surface manifestations of liquefaction reported as a percentage of liquefied material within that pixel. 
Logistic regression with the same form was fit for the two models, with only difference in squaring the denominator to 
improve the fit. The regression coefficients are given in Table 2.

.. math::

	LSE(P) = \frac{a}{\left( 1 + b\,e^{-c\,P} \right)^2} \\ (9)

.. raw:: latex

   \vspace{15pt}

+----------------+-------------+-------------+
| **Parameters** | **Model 1** | **Model 2** |
+================+=============+=============+
| a              |    42.08    |    49.15    |
+----------------+-------------+-------------+
| b              |    62.59    |    42.40    |
+----------------+-------------+-------------+
| c              |    11.43    |    9.165    |
+----------------+-------------+-------------+

Table 2: Parameters for relating probabilities to areal liquefaction percent.

##########################
Rashidian and Baise (2020)
##########################

The model proposed by `Rashidian and Baise (2020) <https://www.sciencedirect.com/science/article/abs/pii/
S0013795219312979>`_ keeps the same functional form as the general model (Model 2) proposed by `Zhu et al. (2017)
<https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/107/3/1365/354192/An-Updated-Geospatial-Liquefaction-Model-for?redirectedFrom=fulltext>`_;
however, introducing two constraints to address the overestimation of liquefaction extent. The mean annual 
precipitation has been capped to :math:`1700 \, \text{mm}`. No liquefaction is heuristically assign when 
:math:`PGA < 0.1 \, \text{g}` as an additional measure to decrease the overestimation of liquefaction. 
Additional novelty introduced in this model is the magnitude scaling factor, :math:`MSF`, to multiply the :math:`PGV` 
to mitigate the potential over-prediction in earthquake with low magnitude.

The explanatory variable :math:`X` is evaluated using the equation (8) that corresponds to the general model of 
`Zhu et al. (2017) <https://pubs.geoscienceworld.org/ssa/bssa/article-abstract/107/3/1365/354192/An-Updated-Geospatial-Liquefaction-Model-for?redirectedFrom=fulltext>`_. 
The spatial extent is evaluated identically using the equation (9).

The proposed probability threshold to convert to class outcome is 0.4.

#####################
Akhlagi et al. (2021)
#####################

Expanding the liquefaction inventory to include 51 earthquake, `Akhlagi et al. (2021) <https://earthquake.usgs.gov/cfusion/external_grants/reports/G20AP00029.pdf>`_ 
proposed two candidate models to predict probability of liquefaction. Shaking is expressed in terms of 
:math:`PGV \, [\text{cm/s}]`. Soil saturation is characterised using the set of proxies: distance to the nearest 
coastline, :math:`d_{c} \, [\text{km}]`, distance to the closest river, :math:`d_{r} \, [\text{km}]`, elevation from 
the closest water body, :math:`Z_{wb} \, [\text{m}]`. Soil density is characterised either by 
:math:`V_{s30} \, [\text{m/s}]` or topographic roughness index, :math:`TRI` which is defined as the mean difference 
between a central pixel and its eight surrounding cells. The explanatory variables of two candidate models are:

Model 1: 

.. math:: 

   X = 4.925 + 0.694 \ln(PGV) - 0.459 \sqrt{TRI} - 0.403 \ln(d_{c} + 1) \quad

.. math:: 

   -0.309 \ln(d_{r} + 1) - 0.164 \sqrt{Z_{wb}} \\ (10)


Model 2: 

.. math:: 

   X = 9.504 + 0.706 \ln(PGV) - 0.994 \ln(V_{s30}) - 0.389 \ln(d_{c} + 1) \quad

.. math:: 

   -0.291 \ln(d_{r} + 1) - 0.205 \sqrt{Z_{wb}} \\ (11)


and the probability of liquefaction is calculated using equation (3). Zero probability is heuristically assigned if 
:math:`PGV < 3 \, \text{cm/s}` or :math:`V_{s30} > 620 \, \text{m/s}`.

The proposed probability threshold to convert to class outcome is 0.4.

#######################################
Allstadt et al. (2022) for liquefaction
#######################################

The model proposed by `Allstadth et al. (2022) <https://journals.sagepub.com/doi/10.1177/87552930211032685>`_ uses the 
model proposed by `Rashidian et al. (2020) <https://www.sciencedirect.com/science/article/abs/pii/S0013795219312979>`_
as a base with slight changes to limit unrealistic extrapolations. The authors proposed capping the mean annual 
precipitation at :math:`2500 \, \text{mm}`, and :math:`PGV = 150 \, \text{cm/s}`. The magnitude scaling factor 
:math:`MSF`, explanatory variables, :math:`X`, probability of liquefaction, :math:`P(L)`, and liquefaction spatial 
extent, :math:`LSE` are calculated using the set of equations previously shown. The proposed probability threshold to 
convert to class outcome is 0.4.

#######################
Todorovic et al. (2022)
#######################

A non-parametric model was proposed to predict liquefaction occurrence and the associated probabilities. The general 
model was trained on the dataset including inventories from over 40 events. A set of candidate variables were 
considered and the ones that correlate the best with liquefaction occurrence are identified as: strain proxy, a ratio
between :math:`pgv \, [\text{cm/s}]` and :math:`V_{s30} \, [\text{m/s}]`; distance to the closest water body, 
:math:`d_{w} \, [\text{km}]`, ground water table depth and :math:`gwd \, [\text{m}]`, average precipitation,
:math:`precip \, [\text{mm}]`.

**************************************************
Permanent ground displacements due to liquefaction
**************************************************

Evaluation of the liquefaction induced permanent ground deformation is conducted using the methodology developed for 
the HAZUS software by the US Federal Emergency Management Agency. Lateral spreading and vertical settlements can have 
detrimental effects on the built environement.

#########################
Lateral spreading (Hazus)
#########################

The expected permanent displacement due to lateral spreading given the susceptibility category can be determined as:

.. math::

	E[PGD_{sc}] = K_{\Delta} \, E[PGD|(PGA/PL_{sc}) = a] \\ (12)

Where: :math:`E[PGD|(PGA/PL_{SC})=a]` is the expected ground displacement given the susceptibility category under a 
specified level of normalised shaking, and is calculated as: 

.. math:: 

   12\, x - 12\ for\ 1 < PGA/PGA(t) < 2 \\ (13) 

.. math:: 

   18\, x - 24\ for\ 2 < PGA/PGA(t) < 3 \\ (14)

.. math:: 

   70\, x - 180\ for\ 3 < PGA/PGA(t) < 4 \\ (15)

:math:`PGA(t)` is theminimum shaking level to induce liquefaction (see Table 1) :math:`K_{\Delta}` is the 
displacement correction factor given that modify the displacement term for magnitudes other than :math:`M7.5`: 

.. math:: 

   K_{Delta} = 0.0086M^3\ - 0.0914M^2\ + 0.4698M\ - 0.9835 \\ (16)

############################
Vertical settlements (Hazus)
############################

Ground settlements are assumed to be related to the area's susceptibility category. The ground settlement amplitudes 
are given in Table 3 for the portion of a soil deposit estimated to experience liquefaction at a given ground motion 
level. The expected settlements at the site is the product of the probability of liquefaction (equation 1) and the 
characteristic settlement amplitude corresponding to the liquefaction susceptibility category, :math:`LSC`.

+---------------+--------------------------+
| **LSC**       | **Settlements (inches)** |
+===============+==========================+
| very high     |            12            |
+---------------+--------------------------+
| high          |            6             |
+---------------+--------------------------+
| moderate      |            2             |
+---------------+--------------------------+
| low           |            1             |
+---------------+--------------------------+
| very low      |            0             |
+---------------+--------------------------+
| none          |            0             |
+---------------+--------------------------+

Table 3: Ground settlements amplitudes for liquefaction susceptibility categories.


Landslide models
----------------

Landslides are considered as one of the most damaging secondary perils associated with earthquakes. Earthquake-induced 
landslides occur when the static and inertia forces within the sliding mass reduces the factor of safety below 1. 
Factors contributing to slope failures are rather complex. The permanent displacement analysis developed by `Newmark 
(1965) <https://www.icevirtuallibrary.com/doi/abs/10.1680/geot.1965.15.2.139>`_ is used to model the dynamic performance
of slopes (`Jibson et al., 2000 <https://www.sciencedirect.com/science/article/pii/S0013795200000399?via%3Dihub>`_, 
`Jibson 2007 <https://www.sciencedirect.com/science/article/pii/S0013795207000300?via%3Dihub>`_). It considers a slope
as a rigid block resting on an inclined plane at an angle :math:`slope` (derived from Digital Elevation Model, DEM). 
When the input motion which is expressed in terms of acceleration exceeds the critical acceleration, :math:`critaccel`, the
block starts to move. The critical acceleration accounts for the shear strength and geometrical characteristics of the
sliding surface, and is calculated as:

.. math:: 

   critaccel =(F_{s}-1)\ - \sin(slope)\cdot g \\ (17)

The static factor of safety is calculated according to the infinite slope model (`Jibson et al., 2000 <https://www.sciencedirect.com/science/article/pii/S0013795200000399?via%3Dihub>`_),
which is well suited for shallow disrupted slides, one of the most common landslide types during earthquakes 
(`Keefer, 1984 <https://people.wou.edu/~taylors/g407/Spring_2022/Keefer_1984_Landslides_Coseismic.pdf>`_):

.. math::

    F_{s} = \frac{cohesion'}{sdd\, slabth\, sin(slope)} + \frac{\tan(fricangle')}{\tan(slope)} - \frac{satcoeff\, waterdensity\, tan(fricangle')}{sdd\, tan(slope)} \\(18)

where: :math:`cohesion' \, [\text{Pa}]` is the effective cohesion with typical values ranging from :math:`20 \text{kPa}` for
soils up to :math:`20 \, {MPa}` for unfaulted rocks. :math:`slope^\circ` is the slope angle. :math:`fricangle'^\circ` is 
the effective friction angle with typical values ranging from :math:`30^\circ` to :math:`40^\circ`. 
:math:`sdd \, [\text{kg/m^3}]` is the dry density of the material. :math:`slabth` is the slope-normal thickness of a failure slab in meters and :math:`satcoeff` is the proportion of slab thickness that is saturated. :math:`waterdensity \, [\text{kg/m^3}]` is the unit weight of water which equals to :math:`1000 \, \text{kg/m^3}`.

Note that the units of the input parameters reported in this document corresponds to the format required by the Engine 
to produce correct results. The first and second term of the the equation corresponds to the cohesive and 
frictional components of the strength, while the third component accounts for the strength reduction due to pore 
pressure.

A variety of regression equations can be used to estimate the earthquake-induced displacements of landslides within the engine. Note that
some of the equations below may return displacements in cm (:math:`Disp_{cm}`); however, OQ  always converts them to m (:math:`Disp`).
Finally, it is important to emphasize that the computed displacements do not necessarily correspond directly to measurable slope movements in the field, 
but rather serve as an index of slope performance.

The table under `Input models for Secondary Perils <https://docs.openquake.org/oq-engine/master/manual/user-guide/inputs/secondary-perils-inputs.html>`_
provides a detailed list of the landslide models implemented in the OpenQuake-engine.


**************
Jibson (2007)
**************

`Jibson (2007) <https://www.sciencedirect.com/science/article/pii/S0013795207000300?via%3Dihub>`_ has generated regression equations for
co-seismic displacements of landslides in terms of i) critical acceleration ratio (i.e., the ratio between the landslide critical acceleration and the PGA) and
ii) crical acceleration ratio - moment magnitude. Displacement data used to derive the regression equations consist of rigorous Newmark displacements computed 
for 2270 strong-motion records and by assuming critical acceleration values in the range of 0.05-0.40 g:

Model a

.. math::
	
	\log(Disp_{cm}) = 0.215 + \log [\left( 1 - \frac{critaccel}{PGA} \right)^{2.341} \cdot \left( \frac{critaccel}{PGA} \right)^{-1.438}] \\ (19)

Model b

.. math::

	\log(Disp_{cm}) = -2.710 + \log [\left( 1 - \frac{critaccel}{PGA} \right)^{2.335} \cdot \left( \frac{critaccel}{PGA} \right)^{−1.478}] + 0.424 M \\ (20)

where :math:`Disp_{cm}` is the predicted co-seismic displacement in cm, but it is converted to m by OQ; :math:`PGA` is the Peak Ground Acceleration in g;
:math:`critaccel` is the landslide critical acceleration in g and :math:`M` is the moment magnitude of the earthquake. Jibson (2007) recommends using model b
only when magnitude is between 5.3 and 7.6.


*******************
Cho & Rathje (2022)
*******************

`Cho & Rathje (2022) <https://ascelibrary.org/doi/abs/10.1061/%28ASCE%29GT.1943-5606.0002757?af=R>`_ have proposed predictive models
for the maximum earthquake-induced displacement along the surface of slope failures subjected to shallow crustal earthquakes.
The dataset used to derive the predictive models consists of displacement values calculated by finite element numerical modelling for 49 slope models
and 1051 earthquakes. The most efficient model developed by the authors computes earthquake-induced displacements (:math:`Disp_{cm}`, in cm) as a function of the 
landslide critical acceleration (:math:`critaccel`, in g units), the :math:`PGV` (in cm/s), the natural period of the slope (:math:`T_{slope}`, in s) and the :math:`H ratio`, i.e., the ratio
between the landslide thickness and the slope height:

.. math::

    \ln(Disp_{cm}) = a_{0} + a_{1} \cdot \ln(PGV) \\ (21)

If :math:`H_{ratio} \leq 0.6`:

.. math::

    a_{0} = -1.01 + 1.57 \cdot \ln(T_{slope}) - 0.25 \cdot \ln(critaccel) \\ (22)

    a_{1} = 0.81 - 1.05 \cdot \ln(T_{slope}) - 0.60 \cdot (\ln(T_{slope}))^2 \\ (23)

If :math:`H_{ratio} > 0.6`:

.. math::

    a_{0} = -4.50 - 1.37 \cdot \ln(critaccel) \\ (24)

    a_{1} = 1.51 + 0.10 \cdot \ln(critaccel) \\ (25)
	

Displacements returned by openquake are converted to m.


*****************************
Fotopoulou & Pitilakis (2015)
*****************************

`Fotopoulou & Pitilakis (2015) <https://link.springer.com/article/10.1007/s10518-015-9768-4>`_ have correlated the average horizontal 
earthquake-induced displacement (:math:`Disp`, in m) of landslides to several intensity measures. The linear regression analyses performed to derive the predictive models 
were based on seismically induced displacement values computed through finited difference numerical modelling on 12 slope models and 40 seismic inputs.

Model a

.. math::

   \ln(Disp) = -9.891 + 1.873 \ln{(PGV)} - 5.964 critaccel + 0.285 M \\ (26)
   
Model b

.. math::

   \ln(Disp) = -2.965 + 2.127 \ln{(PGA)} - 6.583 critaccel + 0.535 M \\ (27)
   
Model c

.. math::

   \ln(Disp) = -10.246 - 2.165 \ln{\left(\frac{critaccel}{PGA}\right)} + 7.844 critaccel + 0.654 M \\ (28)
   
Model d

.. math::

   \ln(Disp) = -8.360 + 1.873 \ln{(PGV)} - 0.347 \ln{\left(\frac{critaccel}{PGA}\right)} - 5.964 critaccel \\ (29)
   
where :math:`PGA` is in g units, :math:`PGV` is in cm/s, :math:`critaccel` is the landslide critical acceleration in g and :math:`M` is the moment magnitude.


***********************
Saygili & Rathje (2008)
***********************

`Saygili & Rathje (2008) <https://ascelibrary.org/doi/10.1061/%28ASCE%291090-0241%282008%29134%3A6%28790%29>`_ have proposed predictive models for
earthquake-induced displacements of landslides based on the rigid-block hypothesis by `Newmark (1965) <https://www.icevirtuallibrary.com/doi/abs/10.1680/geot.1965.15.2.139>`_.
The models were defined by using displacement values computed assuming critical acceleration values (:math:`critaccel`, in g units) from 0.05g and 0.3g and
2383 ground-motions. The authors reccomend to use the predictive model that computes displacements as a function of :math:`PGA` and :math:`PGV`, as considering simultaneously these 
ground-motion parameters reduces the standard deviation.

.. math::

   \ln (Disp_{cm}) = -1.56 - 4.58 \cdot \left(\frac{critaccel}{PGA}\right) 
   - 20.84 \cdot \left(\frac{critaccel}{PGA}\right)^2 
   + 44.75 \cdot \left(\frac{critaccel}{PGA}\right)^3 
   - 30.50 \cdot \left(\frac{critaccel}{PGA}\right)^4 
   - 0.64 \cdot \ln(PGA) + 1.55 \cdot \ln(PGV) \\ (30)
   
where :math:`Disp_{cm}` is the earthquake-induced displacement in cm (converted to m OQ), :math:`PGA` is g units, :math:`critaccel` is the landslide critical acceleration in g and 
:math:`PGV` is in cm/s.

***********************
Rathje & Saygili (2009)
***********************

`Rathje & Saygili (2009) <https://bulletin.nzsee.org.nz/index.php/bnzsee/article/view/312>`_ have updated the PGA predictive model previously proposed
by `Saygili & Rathje (2008) <https://ascelibrary.org/doi/10.1061/%28ASCE%291090-0241%282008%29134%3A6%28790%29>`_ by introducing an additional term
dependent from the moment magnitude :math:`M` of the earthquake.

.. math::

   \ln (Disp_{cm}) = 4.89 - 4.85 \left(\frac{critaccel}{PGA}\right) - 19.64 \left(\frac{critaccel}{PGA}\right)^2 
   + 42.49 \left(\frac{critaccel}{PGA}\right)^3 - 29.06 \left(\frac{critaccel}{PGA}\right)^4 
   + 0.72 \ln(PGA) + 0.89 (M - 6) \\ (31)
   
where :math:`Disp_{cm}` is the earthquake-induced displacement in cm (but converted to m by OQ), :math:`PGA` is g units, :math:`critaccel` is the landslide critical acceleration in g and 
:math:`M` is the moment magnitude of the earthquake.

********************
Jibson et al. (2000)
********************

`Jibson et al. (2000) <https://www.sciencedirect.com/science/article/pii/S0013795200000399?via%3Dihub>`_  have proposed a regression equation
predicting co-seismic displacements of landslides as function of the landslide critical acceleration and the Arias Intensity. The authors have modified the equation
previously proposed by `Jibson (1993) <https://onlinepubs.trb.org/Onlinepubs/trr/1993/1411/1411-002.pdf>`_ to make the critical acceleration term logarithmic:

.. math::

	\log (Disp_{cm}) = 1.521\log (IA) - 1.993 \log (critaccel) - 1.546   \\ (32)

where :math:`Disp_{cm}` is the co-seismic displacement in cm, then converted to m by OQ, :math:`IA` is the Arias Intensity in m/s and 
:math:`critaccel` is the landslide critical acceleration in g units.

`Jibson et al. (2000) <https://www.sciencedirect.com/science/article/pii/S0013795200000399?via%3Dihub>`_ have also proposed a regression curve for the computation of 
the probability of slope failure (:math:`P(f)`) as function of Newmark displacements computed according to eq.32 for the Northridge earthquake:

.. math:: 

    P(f) = 0.335\ [1 - e^{-0.048 \cdot Disp_{cm}^{1.565}}] \\ (33)


****************************
Nowicki Jessee et al. (2018)
****************************

A geospatial model used to predict probability of landsliding using globally available geospatial variables was proposed by 
`Nowicki Jessee et al. (2018) <https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2017JF004494>`_. The level of shaking is 
characterised by Peak Ground Velocity , :math:`PGV`. Slope steepness affects slope stability, and here, the topographic 
slope, :math:`slope`, has been derived from the median elevation value from the 7.5 arc sec Global Multi-resolution Terrain 
Elevation Data (`Danielson and Gesch, 2011 <https://pubs.usgs.gov/of/2011/1073/>`_). The model uses lithology, as a proxy for 
the strength of the shaken material. The global lithology map is available in `Hartman and Moosdort, 2012 <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2012GC004370>`_. 
Slope stability is further controlled by the composite strength of the soil-vegetation root matrix. The Globcover 2009 data, 
available at 300-m resolution and separated into 20 classes has been used. More details on this database is available in 
`Arino et al. (2012) <https://doi.pangaea.de/10.1594/PANGAEA.787668>`_. Finally, the Compound Topographic Index, :math:`CTI`, 
has been used to characterise the wetness of the material. 

Explanatory variable :math:`X` is calculated as:

.. math:: 

   X = -6.30 + 1.65 \ln(PGV) - 0.06 Slope + \alpha \cdot lithology \quad

.. math:: 

   + \beta \cdot landcover + 0.03 CTI - 0.01 \ln(PGV) \cdot Slope \\ (34)

Coefficients \alpha and \beta values are estimated for several rock and landcover classes. The 
reader is reffered to the original study by `Nowicki Jessee et al. (2018) <https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2017JF004494>`_, 
where the coefficient values are reported in Table 3. 

Probability of landsliding is then evaluated using logistic regression:

.. math::

	P(L) = \frac{1}{1+e^X} \\ (35)

These probabilities are converted to areal percentages to unbias the predictions:

.. math::

	LSE(P) = e^{-7.592 + 5.237 \cdot P - 3.042 \cdot P^2 + 4.035 \cdot P^3} \\ (36)


*************************************
Allstadt et al. (2022) for landslides
*************************************

`Allstadth et al. (2022) <https://journals.sagepub.com/doi/10.1177/87552930211032685>`_ introduces modifications to the `Nowicki Jessee et al. (2018) <https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2017JF004494>`_ model, by capping the peak ground velocity at :math:`PGV = 211 \, \text{cm/s}`, 
and compound topographic index at :math:`CTI = 19`. To exclude high probabilities of landsliding in nearly flat areas due to 
the combination of other predictor variables, areas with slopes less than :math:`2^\circ` are excluded.  Zero probability is 
heuristically assigned if :math:`PGA < 0.02 \, \text{g}`. The model also adopts the USGS recommendation for modifying the 
regression coefficient for unconsolidated sediments. The new proposed value is set to :math:`-1.36`. 


Reference
---------

[1] HAZUS-MH MR5 Earthquake Model Technical Manual (https://www.hsdl.org/?view&did=12760)

[2] Youd, T. L., & Idriss, I. M. (2001). Liquefaction Resistance of Soils: Summary Report
from the 1996 NCEER and 1998 NCEER/NSF Workshops on Evaluation of Liquefaction Resistance of Soils. Journal of 
Geotechnical and Geoenvironmental Engineering, 127(4), 297–313. 
https://doi.org/10.1061/(asce)1090-0241(2001)127:4(297)

[3] I. D. Moore, R. B. Grayson & A. R. Ladson (1991). Digital terrain modelling: A review of
hydrological, geomorphological, and biological applications. Journal of Hydrological Processes, 5(1), 3-30. 
https://doi.org/10.1002/hyp.3360050103

[4] Wald, D.J., Allen, T.I., (2007). Topographic Slope as a Proxy for Seismic Site Conditions and Amplification. 
Bull. Seism. Soc. Am. 97 (5), 1379–1395.

[5] Zhu et al., 2015, 'A Geospatial Liquefaction Model for Rapid Response and Loss Estimation', Earthquake Spectra, 
31(3), 1813-1837.

[6] Bozzoni, F., Bonì, R., Conca, D., Lai, C. G., Zuccolo, E., & Meisina, C. (2021). 
Megazonation of earthquake-induced soil liquefaction hazard in continental Europe. Bulletin of Earthquake Engineering, 
19(10), 4059–4082. https://doi.org/10.1007/s10518-020-01008-6

[7] Zhu, J., Baise, L. G., & Thompson, E. M. (2017). An updated geospatial liquefaction
model for global application. Bulletin of the Seismological Society of America, 107(3), 1365–1385. 
https://doi.org/10.1785/0120160198

[8] Rashidian, V., & Baise, L. G. (2020). Regional efficacy of a global geospatial liquefaction model. 
Engineering Geology, 272, 105644. https://doi.org/10.1016/j.enggeo.2020.105644

[9] Allstadt, K. E., Thompson, E. M., Jibson, R. W., Wald, D. J., Hearne, M., Hunter, E. J.,
Fee, J., Schovanec, H., Slosky, D., & Haynie, K. L. (2022). The US Geological Survey ground failure product: 
Near-real-time estimates of earthquake-triggered landslides and liquefaction. Earthquake Spectra, 38(1), 5–36. 
https://doi.org/10.1177/87552930211032685

[10] Baise, L. G., Akhlaghi, A., Chansky, A., Meyer, M., & Moeveni, B. (2021). USGS Award #G20AP00029. Updating the 
Geospatial Liquefaction Database and Model. Tufts University. Medford, Massachusetts, United States.

[11] Todorovic, L., Silva, V. (2022). A liquefaction occurrence model for regional analysis.
Soil Dynamics and Earthquake Engineering, 161, 1–12. https://doi.org/10.1016/j.soildyn.2022.107430

[12] Newmark, N.M., 1965. Effects of earthquakes on dams and embankments. Geotechnique 15, 139–159.

[13] Jibson, R.W., Harp, E.L., & Michael, J.A. (2000). A method for producing digital probabilistic
seismic landslide hazard maps. Engineering Geology, 58(3-4), 271-289. https://doi.org/10.1016/S0013-7952(00)00039-9.

[14] Jibson, R.W. (2007). Regression models for estimating coseismic landslide displacement.
Engineering Geology, 91(2-4), 209-218. https://doi.org/10.1016/j.enggeo.2007.01.013.

[15] Keefer, D. K. (1984). Landslides caused by earthquakes. Geological Society of America Bulletin, 95(4), 406-421.

[16] Cho, Y., & Rathje, E. M. (2022). Generic predictive model of earthquake-induced slope displacements 
derived from finite-element analysis. Journal of Geotechnical and Geoenvironmental Engineering, 148(4), 04022010.
https://doi.org/10.1061/(ASCE)GT.1943-5606.0002757.

[17] Fotopoulou, S. D., & Pitilakis, K. D. (2015). Predictive relationships for seismically induced slope displacements 
using numerical analysis results. Bulletin of Earthquake Engineering, 13, 3207-3238. https://doi.org/10.1007/s10518-015-9768-4.

[18] Saygili, G., & Rathje, E. M. (2008). Empirical predictive models for earthquake-induced sliding displacements of slopes. 
Journal of geotechnical and geoenvironmental engineering, 134(6), 790-803. https://doi.org/10.1061/(ASCE)1090-0241(2008)134:6(790).

[19] Rathje, E. M., & Saygili, G. (2009). Probabilistic assessment of earthquake-induced sliding displacements of natural slopes. 
Bulletin of the New Zealand Society for Earthquake Engineering, 42(1), 18-27. https://doi.org/10.5459/bnzsee.42.1.18-27.

[20] Nowicki Jessee, M. A., Hamburger, M. W., Allstadt, K., Wald, D. J., Robeson, S. M., Tanyas, H., et al. (2018).
A global empirical model for near-real-time assessment of seismically induced landslides. Journal of Geophysical
Research: Earth Surface, 123, 1835–1859. https://doi.org/10.1029/2017JF004494.

[21] Danielson, J.J., and Gesch, D.B., 2011, Global multi-resolution terrain elevation data 2010 (GMTED2010): 
U.S. Geological Survey Open-File Report 2011–1073, 26 p.

[22] Hartmann, J., and N. Moosdorf (2012), The new global lithological map database GLiM: A representation of rock
properties atthe Earth surface, Geochem. Geophys. Geosyst., 13, Q12004, doi:10.1029/2012GC004370.

[23] Arino, O., Ramos Perez, J.J., Kalogirou, V., Bontemps, S., Defourny, P., Van Bogaert, E. (2012): Global Land Cover 
Map for 2009 (GlobCover 2009), https://doi.org/10.1594/PANGAEA.787668.

