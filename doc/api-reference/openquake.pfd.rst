.. _openquake-pfd-api:

openquake.pfd package
=====================

PFD model implementations
-------------------------

This API reference documents the model implementations available to PFD
logic trees. For model selection, references, and configuration examples,
see the :ref:`PFD user guide <probabilistic-fault-displacement>`.

Primary surface rupture
^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   pfd-models/primary_surf_rup/FixedPrimarySR
   pfd-models/primary_surf_rup/Mammarella2024PrimarySR
   pfd-models/primary_surf_rup/MammarellaEtAl2024PrimarySR
   pfd-models/primary_surf_rup/Moss2013PrimarySR
   pfd-models/primary_surf_rup/MossRoss2011PrimarySR
   pfd-models/primary_surf_rup/Pizza2023PrimarySR
   pfd-models/primary_surf_rup/Takao2013PrimarySR
   pfd-models/primary_surf_rup/WC1993PrimarySR
   pfd-models/primary_surf_rup/Yang2021PrimarySR
   pfd-models/primary_surf_rup/Youngs2003PrimarySR

Primary surface displacement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   pfd-models/primary_surf_displ/Chiou2025PrimaryFD
   pfd-models/primary_surf_displ/Kuehn2024PrimaryFD
   pfd-models/primary_surf_displ/Lavrentiadis2023PrimaryFD_aggregate
   pfd-models/primary_surf_displ/Lavrentiadis2023PrimaryFD_principal
   pfd-models/primary_surf_displ/Moss2022PrimaryFD
   pfd-models/primary_surf_displ/Moss2024PrimaryFD
   pfd-models/primary_surf_displ/MossRoss2011PrimaryFD
   pfd-models/primary_surf_displ/Petersen2011PrimaryFD
   pfd-models/primary_surf_displ/Takao2013PrimaryFD
   pfd-models/primary_surf_displ/Youngs2003PrimaryFD

Secondary surface rupture
^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   pfd-models/secondary_surf_rup/FerrarioLivio2021SecondarySR
   pfd-models/secondary_surf_rup/FixedSecondarySR
   pfd-models/secondary_surf_rup/Moss2022SecondarySR
   pfd-models/secondary_surf_rup/Petersen2011SecondarySR
   pfd-models/secondary_surf_rup/Petersen2011SecondarySR_default
   pfd-models/secondary_surf_rup/Rodriguez2023SecondarySR
   pfd-models/secondary_surf_rup/Takao2013SecondarySR
   pfd-models/secondary_surf_rup/Takao2014SecondarySR
   pfd-models/secondary_surf_rup/Visini2025SecondarySR
   pfd-models/secondary_surf_rup/Youngs2003SecondarySR

Secondary surface displacement
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1

   pfd-models/secondary_surf_displ/Moss2022SecondaryFD
   pfd-models/secondary_surf_displ/Petersen2011SecondaryFD
   pfd-models/secondary_surf_displ/Takao2013SecondaryFD
   pfd-models/secondary_surf_displ/Visini2025SecondaryFD
   pfd-models/secondary_surf_displ/Youngs2003SecondaryFD
