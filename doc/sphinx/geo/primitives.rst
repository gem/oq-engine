=====================
Geographic primitives
=====================

Various primitives are needed to define :mod:`seismic sources <openquake.hazardlib.source>`
location and shape. Those implemented include :mod:`~openquake.hazardlib.geo.point`,
:mod:`~openquake.hazardlib.geo.line` and :mod:`~openquake.hazardlib.geo.polygon`.

:mod:`Mesh <openquake.hazardlib.geo.mesh>` objects are used only internally.


-----
Point
-----

.. automodule:: openquake.hazardlib.geo.point
    :members:


----
Line
----

.. automodule:: openquake.hazardlib.geo.line
    :members:


-------
Polygon
-------

.. automodule:: openquake.hazardlib.geo.polygon
    :members:


------
Meshes
------

.. automodule:: openquake.hazardlib.geo.mesh


Simple mesh
-----------

.. autoclass:: Mesh
    :members:


Rectangular mesh
----------------

.. autoclass:: RectangularMesh
    :members:
