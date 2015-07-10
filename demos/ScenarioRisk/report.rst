Calculation of the ground motion fields for a scenario
======================================================

Parameters
----------
============================ ========
calculation_mode             scenario
number_of_logic_tree_samples 0       
maximum_distance             200.0   
investigation_time           None    
ses_per_logic_tree_path      1       
truncation_level             3.0     
rupture_mesh_spacing         15.0    
complex_fault_mesh_spacing   15.0    
width_of_mfd_bin             None    
area_source_discretization   None    
random_seed                  3       
master_seed                  0       
============================ ========

Input files
-----------
============= =====================================
Name          File                                 
exposure      demos/ScenarioRisk/exposure_model.xml
job_ini       demos/ScenarioRisk/job_hazard.ini    
rupture_model demos/ScenarioRisk/fault_rupture.xml 
============= =====================================

Realizations per (TRT, GSIM)
----------------------------

::

  <openquake.commonlib.logictree.RlzsAssoc object at 0x7ff57abf1e10>