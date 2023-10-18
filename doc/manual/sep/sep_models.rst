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

.. math:: `X = 24.1 + 2.067\, ln\, PGA_{M,SM} + 0.355\, CTI - 4.784\, ln\, Vs30`

