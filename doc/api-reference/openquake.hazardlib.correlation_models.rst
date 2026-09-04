.. _openquake-hazardlib-correlation-models:

openquake.hazardlib.correlation_models package
================================================

Base interfaces
---------------

.. automodule:: openquake.hazardlib.correlation_models.base
    :members:
    :undoc-members:
    :show-inheritance:

Registry
--------

.. automodule:: openquake.hazardlib.correlation_models.registry
    :members:
    :undoc-members:
    :show-inheritance:

Scalable sampling
-----------------

.. currentmodule:: openquake.hazardlib.correlation_models.circulant_embedding

.. autoclass:: RegularGridLayout
    :members:

.. autoclass:: CirculantEmbeddingFactor
    :members:

.. currentmodule:: openquake.hazardlib.correlation_models.local_kriging

.. autoclass:: LocalKrigingFactor
    :members:

Spatial models
--------------

.. currentmodule:: openquake.hazardlib.correlation_models.spatial.jayaram_baker_2009

.. autoclass:: JayaramBaker2009
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.spatial.heresi_miranda_2019

.. autoclass:: HeresiMiranda2019
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.spatial.aldea_et_al_2022

.. autoclass:: AldeaEtAl2022
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.spatial.schiappapietra_et_al_2022

.. autoclass:: SchiappapietraEtAl2022NorthernItaly
    :members:
    :show-inheritance:

.. autoclass:: SchiappapietraEtAl2022CentralItaly
    :members:
    :show-inheritance:

.. autoclass:: SchiappapietraEtAl2022SouthernItaly
    :members:
    :show-inheritance:

Joint spatial and cross-IMT models
----------------------------------

.. currentmodule:: openquake.hazardlib.correlation_models.spatial_cross_imt.loth_baker_2013

.. autoclass:: LothBaker2013
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.spatial_cross_imt.markhvida_et_al_2018

.. autoclass:: MarkhvidaEtAl2018
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.spatial_cross_imt.wang_du_2013

.. autoclass:: WangDu2013PGAIAPGV
    :members:
    :show-inheritance:

.. autoclass:: WangDu2013SpectralAcceleration
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.spatial_cross_imt.du_ning_2021

.. autoclass:: DuNing2021
    :members:
    :show-inheritance:

.. autoclass:: DuNing2021Interpolated
    :members:
    :show-inheritance:

Cross-IMT models
----------------

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.baker_bradley_2017

.. autoclass:: BakerBradley2017
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.baker_cornell_2006

.. autoclass:: BakerCornell2006
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.baker_jayaram_2008

.. autoclass:: BakerJayaram2008
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.bradley_2012

.. autoclass:: Bradley2012
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.goda_atkinson_2009

.. autoclass:: GodaAtkinson2009
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.no_cross_correlation

.. autoclass:: NoCrossCorrelation
    :members:
    :show-inheritance:

.. currentmodule:: openquake.hazardlib.correlation_models.cross_imt.full_cross_correlation

.. autoclass:: FullCrossCorrelation
    :members:
    :show-inheritance:

Compatibility modules
---------------------

``openquake.hazardlib.correlation`` and
``openquake.hazardlib.cross_correlation`` are compatibility modules for the
historical APIs. New code should import canonical classes from
``openquake.hazardlib.correlation_models`` subpackages or resolve configured
models through the registry.
