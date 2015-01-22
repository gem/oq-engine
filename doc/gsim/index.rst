===============================
Ground-shaking intensity models
===============================

.. automodule:: openquake.hazardlib.gsim


--------------
Built-in GSIMs
--------------

.. toctree::

    abrahamson_silva_1997
    abrahamson_silva_2008
    akkar_2013
    akkar_2014
    akkar_bommer_2010
    akkar_cagnan_2010
    allen_2012
    atkinson_boore_1995
    atkinson_boore_2003
    atkinson_boore_2006
    berge_thierry_2003
    bindi_2011
    bindi_2014
    boore_1993
    boore_1997
    boore_2014
    boore_atkinson_2008
    boore_atkinson_2011
    bradley_2013
    campbell_2003
    campbell_bozorgnia_2003
    campbell_bozorgnia_2008
    campbell_bozorgnia_2014
    cauzzi_2014
    cauzzi_faccioli_2008
    cauzzi_faccioli_2008_swiss
    chiou_youngs_2008
    chiou_youngs_2008_swiss
    chiou_youngs_2014
    climent_1994
    convertito_2012
    douglas_stochastic_2013
    edwards_fah_2013a
    edwards_fah_2013f
    faccioli_2010
    frankel_1996
    fukushima_tanaka_1990
    garcia_2005
    geomatrix_1993
    lin_lee_2008
    lin_2009
    mcverry_2006
    megawati_pan_2010
    pezeshk_2011
    sadigh_1997
    silva_2002
    si_midorikawa_1999
    somerville_2001
    somerville_2009
    tavakoli_pezeshk_2005
    toro_1997
    toro_2002
    youngs_1997
    zhao_2006
    zhao_2006_swiss


-----------------------------------
Base GSIM classes and functionality
-----------------------------------

.. automodule:: openquake.hazardlib.gsim.base


Intensity models
----------------

.. autoclass:: GroundShakingIntensityModel
    :members:

.. autoclass:: GMPE
    :members:
    :private-members:

.. autoclass:: IPE
    :members:
    :private-members:


Helper for coefficients tables
------------------------------

.. autoclass:: CoeffsTable
    :members:


Calculation context
-------------------

.. autoclass:: SitesContext

.. autoclass:: RuptureContext

.. autoclass:: DistancesContext
