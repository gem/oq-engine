===============================
Ground-shaking intensity models
===============================

.. automodule:: nhlib.gsim


--------------
Built-in GSIMs
--------------

.. toctree::

    chiou_youngs_2008
    sadigh_1997
    boore_atkinson_2008
    zhao_2006
    atkinson_boore_2006


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
