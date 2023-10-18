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
