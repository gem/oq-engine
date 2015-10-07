Scenario Damage QA Test 4
=========================

Parameters
----------
============================ ========
calculation_mode             scenario
number_of_logic_tree_samples 0       
maximum_distance             300.0   
investigation_time           None    
ses_per_logic_tree_path      1       
truncation_level             3.0     
rupture_mesh_spacing         10.0    
complex_fault_mesh_spacing   10.0    
width_of_mfd_bin             None    
area_source_discretization   None    
random_seed                  3       
master_seed                  0       
concurrent_tasks             64      
============================ ========

Input files
-----------
============= ============================================
Name          File                                        
============= ============================================
exposure      `exposure_model.xml <exposure_model.xml>`_  
fragility     `fragility_model.xml <fragility_model.xml>`_
job_ini       `job_haz.ini <job_haz.ini>`_                
rupture_model `fault_rupture.xml <fault_rupture.xml>`_    
============= ============================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== =
#assets     3
#sites      3
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
RC       1      
RM       1      
W        1      
======== =======