Liquefaction and Landslide models
=================================

Liquefaction models
-------------------

Several liquefaction models are implemented in the OpenQuake engine. 
One of them is the method developed for the HAZUS software by the US 
Federal Emergency Management Agency. This model involves categoriza-
tion of sites into liquefaction susceptibility classes based on geo-
technical characteristics, and a quanitative probability model for 
each susceptibility class. The remaining models are the academic 
geospatial models, i.e., statistical models that uses globally avai-
lable input variables as first-order proxies to characterise satura-
tion and density properties of the soil. The shaking component is 
expressed either in terms of Peak Ground Acceleration (PGA) or Peak 
Ground Velocity (PGV). 

HAZUS
^^^^^

The HAZUS model classifies each site into a liquefaction susceptibility
class (LSC) based on the geologic and geotechnical characteristics of
the site, such as the sedimentological type and the deposition age of
the unit. In addition to the LSC and the local ground acceleration at
each site, the depth to groundwater at the site and the magnitude of the
causative earthquake will affect the probability that a given site will
experience liquefaction.

The equation that describes this probability is:

.. math:: P(L) = \frac{P(L | PGA=a) \cdot P_{ml}}{K_m K_w}\ \ (1)

:math:`P(L|PGA=a)` is the conditional probability that a site will fail
based on the PGA and the LSC. :math:`P_{ml}` is the fraction of the
total mapped area that will experience liquefaction if
:math:`P(L|PGA=a)` reaches 1. These terms both have LSC-specific
coefficients; these are shown in Table 1.

:math:`K_m` is a magnitude-correction factor that scales :math:`P(L)`
for earthquake magnitudes other than *M*\ =7.5, potentially to account
for the duration of shaking (longer shaking increases liquefaction
probability). :math:`K_w` is a groundwater depth correction factor
(shallower groundwater increases liquefaction probability).

+-----------+----------------+-----------+---------+----------------+
| LSC       | PGA min        | PGA slope | PGA int | :math:`P_{ml}` |
+===========+================+===========+=========+================+
| very high | 0.09           | 9.09      | 0.82    | 0.25           |
+-----------+----------------+-----------+---------+----------------+
| high      | 0.12           | 7.67      | 0.92    | 0.2            |
+-----------+----------------+-----------+---------+----------------+
| moderate  | 0.15           | 6.67      | 1.0     | 0.1            |
+-----------+----------------+-----------+---------+----------------+
| low       | 0.21           | 5.57      | 1.18    | 0.05           |
+-----------+----------------+-----------+---------+----------------+
| very low  | 0.26           | 4.16      | 1.08    | 0.02           |
+-----------+----------------+-----------+---------+----------------+
| none      | :math:`\infty` | 0.0       | 0.0     | 0.0            |
+-----------+----------------+-----------+---------+----------------+

Table 1: Liquefaction values for different liquefaction susceptibility
categories (LSC). *PGA min* is the minimum ground acceleration required
to initiate liquefaction. *PGA slope* is the slope of the liquefaction
probability curve as a function of PGA, and *PGA int* is the *y*-intercept
of that curve. :math:`P_{ml}` is the Map Area Proportion, which gives the
area of liquefaction within each map unit conditional on liquefaction 
occurring in the map unit.


Geospatial models
^^^^^^^^^^^^^^^^^

Zhu et al. (2015)
~~~~~~~~~~~~~~~~~

The model by Zhu et al. (2015) is a logistic regression model requiring
specification of the :math:`Vs30 [m/s]`, the Compound Topographic Index 
(CTI), a proxy for soil wetness or groundwater depth :math:`gwd [m]`, 
the :math:`PGA_{M,SM} [g]` experienced at a site, and the magnitude of 
the causative earthquake.

The model is quite simple. An explanatory variable :math:`X` is
calculated as:

.. math:: X = 24.1 + 2.067\, ln\, PGA_{M,SM} + 0.355\,CTI − 4.784\, ln\, Vs30\ \(2)

and the final probability is the logistic function

.. math:: P(L) = \frac{1}{1+e^X}\ \(3)

The term :math:`PGA_{M,SM}` is the PGA corrected by magnitude scaling
factor (MSF) that serves as proxy for earthquake duration. The :math:`MSF`
is calculated as per Idriss et al. (1991):

.. math:: MSF = \{10^2.24}{M^2.56}\ \(4)

Both the :math:`CTI` and the :math:`Vs30` may be derived from digital 
elevation data. The :math:`Vs30` may be estimated from the topographic 
slope through the equations of Wald and Allen (2007), which uses a 
very low resolution DEM compared to modern offerings. As topographic 
slope tends to increase with increased DEM resolution, the estimated 
:math:`Vs30` does too; therefore a low-resolution DEM (i.e., a 1 km 
resolution) must be used to calculate :math:`Vs30`, rather than the 
30 m DEM that is the current standard. This results in a more accurate 
:math:`Vs30` for a given slope measurement, but it also means that in 
an urban setting, sub-km-scale variations in slope are not accounted for.

The CTI (Moore et al., 1991) is a proxy for soil wetness that relates
the topographic slope of a point to the upstream drainage area of that
point, through the relation

.. math:: CTI = \ln (d_a / \tan \delta)\ \(4)

where :math:`d_a` is the upstream drainage area per unit width through
the flow direction (i.e. relating to the DEM resolution). It was
developed for hillslopes, and is not meaningful in certain very flat
areas such as the valley floors of major low-gradient rivers, where the
upstream drainage areas are very large. Unfortunately, this is exactly
where liquefaction is most expected away from coastal settings.

Model's prediction can be transformed into binary class (liquefaction
occurrence or nonoccurrence) via probability threshold value. The authors
proposed a threshold of 0.2.


Bozzoni et al. (2021)
~~~~~~~~~~~~~~~~~~~~~

The parametric model developed by Bozzoni et al. (2021), keeps the same 
input variables (i.e., :math:`PGA_{M,SM}`, :math:`CTI`, :math:`Vs30`)
and functional form as in Zhu et al. (2015). Regression parameters are
calibrated based on the liquefaction case histories observed during 
seismic events in Europe. The implemented model is associated with the
ADASYN sampling algorithm. The explanatory variable :math:`X`is computed as:

.. math:: X = -11.489 + 3.864\, ln\, PGA_{M} + 2.328\,CTI − 0.091\, ln\, Vs30\ \(5)

and the probability of liquefaction in calculated using equation (3). 

The adopted probability threshold of 0.57 converts the probability of
liquefaction into binary outcome. 

Zhu et al. (2017)
~~~~~~~~~~~~~~~~~

Two parametric models are proposed by Zhu and others (2017), a coastal
model (Model 1), and a more general model (Model 2). A coastal event is
defined as one where the liquefaction occurrences are, on average, within 
20 km of the coast; or, for earthquakes with insignificant or no liquefaction,
epicentral distances less than 50 km.The implemented geospatial models 
are for global use. An extended set of input parameters is used to 
describe soil properties (its density and wetness). The ground shaking
is characterised by :math:`PGV [cm/s]`. Soil density is described by 
:math:`Vs30 [m/s]`. Soil wetness in Model 1 is chatacterised by a set of 
features: mean annual precipitation :math:`precip [mm]`, distance to the 
coast :math:`d_{c} [km]`, and distance to the river :math:`d_{r} [km]`. 
Distance to the coast also indicates the geologic age - younger deposits 
are found near the coast. Soil wetness in Model 2 is characterised by 
closest distance to the water body :math:`d_{w} [km]` which is determined 
as :math:`\min(d_{c}, d_{r})`, and the water table depth :math:`wtd [m]`. 
Mean annual precipitation is from a global layer developed by Hijmans 
et al. (2005). Distance to the nearest river is calculated based on the 
HydroSHEDS database (Lehner et al. 2008). Water table depth is retreived from a 
global dataset by Fan et al (2013).Distance to the nearest coastline data
was computed from https://oceancolor.gsfc.nasa.gov. 

The explanatory varibale :math:`X`is calculated as:

Model 1: 
.. math:: X = 12.435 + 0.301\, ln\, PGV - 2.615\, ln\, Vs30 + 0.0005556\, precip
.. math::     -0.0287\, \sqrt{d_{c}} + 0.0666\,d_{r} - 0.0369\, \sqrt{d_{c}} \cdot d_{r}\ \(6) 

Model 2:
.. math:: X = 8.801 + 0.334\, ln\, PGV - 1.918\, ln\, Vs30 + 0.0005408\, precip
.. math::     -0.2054\, d_{w} -0.0333\, wtd\ \(7)

and the probability of liquefaction is calculated using equation (3). 
Zero probability is heuristically assigned if :math:`PGV < 3 cm/s ` or 
:math:`Vs30 > 620 m/s`. 

The proposed probability threshold to convert to class outcome is 0.4. 

Another model's outcome is liquefaction spatial extent (LSE). After an 
earthquake LSE is the spatial area covered by surface manifestations of 
liquefaction reported as a percentage of liquefied material within that 
pixel. Logistic regression with the same form was fit for the two models, 
with only difference in squaring the denominator to improve the fit. The 
regression coefficients are given in Table 2.

.. math:: L(P) = \frac{a}{1+b\,e^(-c\,P)}^2\ \(8)

+--------------+-----------+-----------+
| Parameters   | Model 1   | Model 2   |
+==============+===========+===========+
| a            | 42.08     | 49.15     |
+--------------+-----------+-----------+
| b            | 62.59     | 42.40     |
+--------------+-----------+-----------+
| c            | 11.43     | 9.165     |
+--------------+-----------+-----------+
Table 2: Parameters for relating proba-
bilities to areal liquefaction percent.


Rashidian et al. (2020)
~~~~~~~~~~~~~~~~~~~~~~~

The model proposed by Rashidian et al. (2020) keeps the same functional form
as the general model (Model 2) proposed by Zhu et al. (2017); however, introdu-
cing two constraints to address the overestimation of liquefaction extent. The 
mean annual precipitation has been capped to 1700 mm. No liquefaction is heuri-
stically assign when :math:`pga < 0.1 g` as an additional measure to decrease the
overestimation of liquefaction. 
Additional novelty introduced in this model is the magnitude scaling factor
:math:`MSF` to multiply the :math:`PGV` to mitigate the potential over-prediction
in earthquake with low magnitude.

.. :math:: MSF = \frac{1}{1+e^(-2\,[M-6])}\ \(9)

The explanatory variable :math:`X` is evaluated using the equation (7) that corr-
esponds to the general model of Zhu et al. (2017). The spatial extent is evaluated
identically using the equation (8).

The proposed probability threshold to convert to class outcome is 0.4. 


Akhlagi et al. (2021)
~~~~~~~~~~~~~~~~~~~~~

Expanding the liquefaction inventory to include 51 earthquake, Akhlagi et al.
(2021) proposed two candidate models to predict probability of liquefaction. 
Shaking is expressed in terms of :math:`PGV [cm/s]`. Soil saturation is 
characterised using the set of proxies: distance to the nearest coastline
:math:`d_{c} [m]`, distance to the closest river :math:`d_{r} [m]`, elevation from 
the closest water body :math:`Z_{wb} [m]`. Soil density is characterised either by 
:math:`Vs30 [cm/s]` or topographic roughness index :math:`TRI` which is defined as 
the mean difference between a central pixel and its eight surrounding cells. The 
explanatory variables of two candidate models are:

Model 1: 
.. math:: X = 4.925 + 0.694\, ln\, PGV - 0.459\, \sqrt{TRI} - 0.403\, ln\, d_{c}+1
.. math::     -0.309\, \ln\, d_{r}+1 - 0.164\, \sqrt{Z_{wb}}\ \(10) 

Model 2:
.. math:: X = 9.504 + 0.706\, ln\, PGV - 0.994\, ln\, Vs30 - 0.389\, ln\, d_{c}+1
.. math::     -0.291\, \ln\, d_{r}+1 - 0.205\, \sqrt{Z_{wb}}\ \(11)

and the probability of liquefaction is calculated using equation (3). 
Zero probability is heuristically assigned if :math:`PGV < 3 cm` or 
:math:`Vs30 > 620 m/s`. 

The proposed probability threshold to convert to class outcome is 0.4. 


Allstadth et al. (2022)
~~~~~~~~~~~~~~~~~~~~~~~

The model proposed by Allstadth et al. (2022) uses the model proposed by 
Rashidian et al. (2020) as a base with slight changes to limit unrealistic 
extrapolations. The authors proposed capping the mean annual precipitation 
at 2500 mm, and PGV at 150 cm/s. The magnitude scaling factor :math:`MSF`, 
explanatory variables :math:`X`, probability of liquefaction :math:`P(L)`,
and liquefaction spatial extent :math:`LSE` are calculated using the set 
of equations previously shown. The proposed probability threshold to convert 
to class outcome is 0.4. 


Todorovic et al. (2022)
~~~~~~~~~~~~~~~~~~~~~~~

A non-parametric model was proposed to predict liquefaction occurrence and 
the associated probabilities. The general model was trained on the dataset
including inventories from over 40 events. A set of candidate variables 
were considered and the ones that correlate the best with liquefaction 
occurrence are identified as: strain proxy, a ratio between :math:`pgv [cm/s]`
and :math:`Vs30 [m/s]`; distance to the closest water body :math:`d_{w} [km]`, 
water table depth :math:`gwd [m]`, average precipitation :math:`precip [mm]`. 



Permanent ground displacements due to liquefaction 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Evaluation of the liquefaction induced permanent ground deformation is 
conducted using the methodology developed for the HAZUS software by the 
US Federal Emergency Management Agency. Lateral spreading and vertical
settlements can have detrimental effects on the built environement. 

Lateral spreading (Hazus)
~~~~~~~~~~~~~~~~~~~~~~~~~

The expected permanent displacement due to lateral spreading given the
susceptibility category can be determined as:

.. :math:: E[PGD_{SC}] = K_{\Delta}\times E[PGD|(PGA/PL_{SC})=a]\ \(12)

Where: 
:math:`E[PGD|(PGA/PL_{SC})=a]` is the expected ground displacement given
the susceptibility category under a specified level of normalised shaking,
and is calculated as:
.. :math:: 12\, x - 12  \text{for} 1 < PGA/PGA(t) < 2
.. :math:: 18\, x - 24  \text{for} 2 < PGA/PGA(t) < 3
.. :math:: 70\, x - 180 \text{for} 3 < PGA/PGA(t) < 4

:math:`(PGA/PGA(t))` 
:math:`PGA(t)` is theminimum shaking level to induce liquefaction (see Table 1)
:math:`K_{\Delta}` is the displacement correction factor given thhat modify 
the displacement term for magnitudes other than :math:`M7.5`:
.. :math:: K_{\Delta} = 0.0086\, M^3 - 0.0914\, M^2 + 0.4698\, M - 0.9835\ \(13)


Vertical settlements (Hazus)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ground settlements are assumed to be related to the area's susceptibility
category. The ground settlement amplitudes are given in Table 3 for the
portion of a soil deposit estimated to experience liquefaction at a given 
ground motion level. The expected settlements at the site is the product
of the probability of liquefaction (equation 1) and the characteristic 
settlement amplitude corresponding to the liquefaction susceptibility 
category (LSC). 

+----------------+-----------------------+
| LSC            | Settlements (inches)  |
+================+=======================+
| very high      |          12           |
+----------------+-----------------------+
| high           |           6           |
+----------------+-----------------------+
| moderate       |           2           |
+----------------+-----------------------+
| low            |           1           |
+----------------+-----------------------+
| very low       |           0           |
+----------------+-----------------------+
| none           |           0           |
+----------------+-----------------------+
Table 3: Ground settlements amplitudes for 
liquefaction susceptibility categories.


Landslide models
----------------

Landslides are considered as one of the most damaging secondary perils
associated with earthquakes. Earthquake-induced landslides occurs when 
the static and inertia forces within the sliding mass reduces the factor
of safety below 1. Factors contributing to a slope failure are rather 
complex. The permanent-displacement analysis developed by Newmark (1965)
is used to model the dynamic performance of slopes (Jibson 2020, 2007).
It considers a slope as a rigid block resting on an inclined plane at 
an angle :math:`\alpha` (derived from Digital Elevation Model, DEM). 
When the input motion which is expressed in terms of acceleration exceeds 
the critical acceleration :math:`a_{c}`, the block starts to move. The 
crtical acceleration accounts for the shear strength and geometrical 
characteristics of the sliding surface, and is calculated as:

.. :math:: a_{c} = (FS-1)\,g\,sin(\alpha)\ \(14)

The lower bound of :math:`a_{c}` is set to 0.05 to avoid unrealistically
large displacements.
The static factor of safety is calculated as:

.. :math:: FS = \frac{c'}{\gamma\, t\, sin(\alpha)} + frac{tan(\phi')}{tan(\alpha)} -
.. :math::       frac{m\, \gamma_{w}\, tan(\phi')}{\gamma\, tan(\alpha)}\ \(15) 

where:
:math:`c' [Pa]` is the effective cohession with typical values ranging
from 20 kPa for soils up to 20 MPa for unfaulted rocks.
:math:`\alpha [\degrees]` is the slope angle.
:math:`\phi' [\degrees]` is the effective friction angle with typical values 
ranging from 30 to 40 degrees.
:math:`\gamma [kg/m^3]` is the dry_density of the soil or rock. It ranges 
from ~1500 :math:`kg/m^3` for soils to ~ 2500 - 3200 :math:`kg/m^3`.
:math:`t [m]` is the slope-normal thickness of a failure slab with the default
value of 2.5 meters.
:math:`m` is the proportion of slab thickness that is saturated with default
value of 0.1.
:math:`\gamma_{w} [kg/m^3]` is the unit weight of water which equals to 
:math:`1000 kg/m^3`. 

Note that the units of the input parameters reported in this document 
corresponds to the format required by the Engine to produce correct results.
The first and second term of the the equation (15) corresponds to the cohesive
and frictional components of the strength, while the third component 
accounts for the strength reduction due to pore pressure.

A variety of regression equations can be used to estimate the Newmark
displacements, and within the engine, Newmark displacement as a 
function of critical acceleration ratio and moment magnitude is implemented.
The displacement is in units of meters.

.. :math:: logD_{N} = -2.710 + 
.. :math::             log[(1-\frac{a_{c}}{a_{max}})^2.335\, (\frac{a_{c}}{a_{max}})^-1.478] + 
.. :math::             0.424\, M \± 0.454\ \(16) 

The computed displacements do not necessarily correspond directly to  
measurable slope movements in the field, but the modeled displacements 
provide an index to correlate with field performance. Jibson (2000) compared 
the predicted displacements with observations from 1994 Northridge earthquake 
and fit the data with Weilbull curve. The following equation can be used 
to estimate the probability of slope failure as a function of Newmark 
displacement.

.. :math:: P(f) = 0.335\, [1-e^(-0.048\, D_{n}^1.565)]\ \(17)


The rock-slope failures are the other common effect observed in earthquakes.
The methodology proposed by Grant et al., (2016) captures the brittle behavior
associated with rock-slope failures and discontinuities common in rock masses.
The static factor of safety is computed as:

.. :math:: FS = \frac{2\, (c+c_{r})\, sin(\alpha)}{\gamma\, h\, sin(\beta)} +
.. :math::      \frac{tan(\phi)}{tan(\beta)}\ \(18)

where:
:math:`c [Pa]` is the cohession with typical values ranging from 20 kPa 
for soils up to 20 MPa for unfaulted rocks. 
:math:`c_{r}` is the cohesion provided by the root systems of vegetated 
hillslopes. Here, we adopted the default value of 0 root cohesion.
:math:`\alpha [\degrees]` is the slope angle.
:math:`\gamma [kg/m^3]` is the dry_density of the soil or rock. It ranges 
from ~1500 :math:`kg/m^3` for soils to ~ 2500 - 3200 :math:`kg/m^3`.
:math:`h [m]` is the vertical height of the failure mass and it corresponds
to 1/4 of the local relief :math:`H` calculated based on the moving
window analysis. 
:math:`\phi' [\degrees]` is the effective friction angle with typical values 
ranging from 30 to 40 degrees.
:math:`\beta` is the slope's critical angle calculated as:
.. :math:: \beta = \frac{\alpha + \phi}{0.5}\ \(19)

The critical acceleration is computed similarly to equation (14). For rock-
slope failures, the :math:`\alpha` term is replaced with :math:`\beta`.

.. :math:: a_{c} = (FS-1)\,g\,sin(\beta)\ \(20)

Finaly, the coseismic displacements are estimated using Jibson’s (2007) sliding 
block displacement regression equation:

.. :math:: logD_{N} = 0.215 + 
.. :math::             log[(1-\frac{a_{c}}{a_{max}})^2.341\, (\frac{a_{c}}{a_{max}})^-1.438]\ \(21) 




Reference
----------

[1] HAZUS-MH MR5 Earthquake Model Technical Manual (https://www.hsdl.org/?view&did=12760)

[2] Youd, T. L., & Idriss, I. M. (2001). Liquefaction Resistance of Soils: Summary Report 
    from the 1996 NCEER and 1998 NCEER/NSF Workshops on Evaluation of Liquefaction Resistance 
    of Soils. Journal of Geotechnical and Geoenvironmental Engineering, 127(4), 297–313.
    https://doi.org/10.1061/(asce)1090-0241(2001)127:4(297)

[3] I. D. Moore, R. B. Grayson & A. R. Ladson (1991). Digital terrain modelling: A review of 
    hydrological, geomorphological, and biological applications. Journal of Hydrological 
    Processes, 5(1), 3-30. https://doi.org/10.1002/hyp.3360050103 

[4] Wald, D.J., Allen, T.I., (2007). Topographic Slope as a Proxy for Seismic Site Conditions 
    and Amplification. Bull. Seism. Soc. Am. 97 (5), 1379–1395.

[5] Zhu et al., 2015, 'A Geospatial Liquefaction Model for Rapid Response and 
    Loss Estimation', Earthquake Spectra, 31(3), 1813-1837.

[6] Bozzoni, F., Bonì, R., Conca, D., Lai, C. G., Zuccolo, E., & Meisina, C. (2021). 
    Megazonation of earthquake-induced soil liquefaction hazard in continental Europe.
    Bulletin of Earthquake Engineering, 19(10), 4059–4082. https://doi.org/10.1007/s10518-020-01008-6

[7] Zhu, J., Baise, L. G., & Thompson, E. M. (2017). An updated geospatial liquefaction
    model for global application. Bulletin of the Seismological Society of America, 
    107(3), 1365–1385. https://doi.org/10.1785/0120160198

[8] Rashidian, V., & Baise, L. G. (2020). Regional efficacy of a global geospatial 
    liquefaction model. Engineering Geology, 272, 105644. 
    https://doi.org/10.1016/j.enggeo.2020.105644

[9] Allstadt, K. E., Thompson, E. M., Jibson, R. W., Wald, D. J., Hearne, M., Hunter, E. J., 
    Fee, J., Schovanec, H., Slosky, D., & Haynie, K. L. (2022). The US Geological Survey 
    ground failure product: Near-real-time estimates of earthquake-triggered landslides and 
    liquefaction. Earthquake Spectra, 38(1), 5–36. https://doi.org/10.1177/87552930211032685

[10] Baise, L. G., Akhlaghi, A., Chansky, A., Meyer, M., & Moeveni, B. (2021). USGS Award 
     #G20AP00029. Updating the Geospatial Liquefaction Database and Model. Tufts University. 
     Medford, Massachusetts, United States.

[11] Todorovic, L., Silva, V. (2022). A liquefaction occurrence model for regional analysis. 
     Soil Dynamics and Earthquake Engineering, 161, 1–12. https://doi.org/10.1016/j.soildyn.2022.107430

[12] Newmark, N.M., 1965. Effects of earthquakes on dams and embankments. Geotechnique 15, 139–159.

[13] Jibson, R.W., Harp, E.L., & Michael, J.A. (2000). A method for producing digital probabilistic 
     seismic landslide hazard maps. Engineering Geology, 58(3-4), 271-289.
     https://doi.org/10.1016/S0013-7952(00)00039-9 

[14] Jibson, R.W. (2007). Regression models for estimating coseismic landslide displacement.
     Engineering Geology, 91(2-4), 209-218. https://doi.org/10.1016/j.enggeo.2007.01.013 

[15] Grant, A., Wartman, J., & Grace, A.J. (2016). Multimodal method for coseismic landslide 
     hazard assessment. Engineering Geology, 212, 146-160. https://doi.org/10.1016/j.enggeo.2016.08.005
