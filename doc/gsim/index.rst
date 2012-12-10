===============================
Ground-shaking intensity models
===============================

.. automodule:: nhlib.gsim


--------------
Built-in GSIMs
--------------

.. toctree::

    abrahamson_silva_2008
    akkar_bommer_2010
    akkar_cagnan_2010
    atkinson_boore_2006
    boore_atkinson_2008
    cauzzi_faccioli_2008
    chiou_youngs_2008
    faccioli_2010
    sadigh_1997
    zhao_2006


-----------------------------------
Base GSIM classes and functionality
-----------------------------------

.. automodule:: nhlib.gsim.base


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
