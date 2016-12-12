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
    abrahamson_2014
    abrahamson_2015
    akkar_2013
    akkar_2014
    akkar_bommer_2010
    akkar_cagnan_2010
    allen_2012
    allen_2012_ipe
    atkinson_boore_1995
    atkinson_boore_2003
    atkinson_boore_2006
    atkinson_macias_2009
    atkinson_2015
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
    dost_2004
    douglas_stochastic_2013
    dowrickrhoades_2005
    drouet_2015_brazil
    edwards_fah_2013a
    edwards_fah_2013f
    faccioli_2010
    frankel_1996
    fukushima_tanaka_1990
    garcia_2005
    gupta_2010
    geomatrix_1993
    ghofrani_atkinson_2014
    gsim_table
    hong_goda_2007
    idriss_2014
    kanno_2006
    kale_2015
    kotha_2016
    lin_lee_2008
    lin_2009
    mcverry_2006
    megawati_pan_2010
    montalva_2016
    nath_2012
    nshmp_2014
    pezeshk_2011
    raghukanth_iyengar_2007
    rietbrock_2013
    sadigh_1997
    sharma_2009
    silva_2002
    si_midorikawa_1999
    somerville_2001
    somerville_2009
    tavakoli_pezeshk_2005
    toro_1997
    toro_2002
    travasarou_2003
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

