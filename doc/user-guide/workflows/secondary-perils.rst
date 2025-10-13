.. _secondary-perils-intro:

Secondary perils
================

Starting from OpenQuake engine v3.18, it is possible to perform either scenario-based or event-based liquefaction hazard 
assessment using several geospatial models available in the secondary perils module. The input files do not differ 
significantly for what is typically used for ground-shaking hazard assessment. All relevant details on the workflow are 
reported in :ref:`Scenario Hazard <scenario-hazard-intro>` and :ref:`Event Based PSHA <event-based-psha-intro>`.
Site model is expanded to account for information on soil density and wetness conditions as explained in the relevant 
sections of this manual. The `job.ini` file requires additional parameter ``secondary_perils``. Various outputs resulting
from these analyses are stored in `gmf-data.csv`.
