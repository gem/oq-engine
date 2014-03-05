===============================
Ground-shaking intensity models
===============================

.. automodule:: openquake.hazardlib.gsim


--------------
Built-in GSIMs
--------------

.. toctree::

    abrahamson_silva_2008
    akkar_2013
    akkar_bommer_2010
    akkar_cagnan_2010
    allen_2012
    atkinson_boore_1995
    atkinson_boore_2003
    atkinson_boore_2006
    berge_thierry_2003
    boore_1993
    boore_1997
    boore_atkinson_2008
    boore_atkinson_2011
    campbell_2003
    campbell_bozorgnia_2008
    cauzzi_faccioli_2008
    chiou_youngs_2008
    faccioli_2010
    frankel_1996
    lin_lee_2008
    lin_2009
    pezeshk_2011
    sadigh_1997
    silva_2002
    si_midorikawa_1999
    somerville_2009
    toro_1997
    toro_2002
    youngs_1997
    zhao_2006


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
