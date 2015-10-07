oq-test03, depth=15km
=====================

Parameters
----------
============================ ========
calculation_mode             scenario
number_of_logic_tree_samples 0       
maximum_distance             300.0   
investigation_time           None    
ses_per_logic_tree_path      1       
truncation_level             3.0     
rupture_mesh_spacing         0.1     
complex_fault_mesh_spacing   0.1     
width_of_mfd_bin             None    
area_source_discretization   None    
random_seed                  3       
master_seed                  0       
concurrent_tasks             64      
============================ ========

Input files
-----------
============= ============================================================================
Name          File                                                                        
============= ============================================================================
exposure      `exposure_model_Antioquia_test03.xml <exposure_model_Antioquia_test03.xml>`_
fragility     `fragility_model_test03.xml <fragility_model_test03.xml>`_                  
job_ini       `job_h.ini <job_h.ini>`_                                                    
rupture_model `rupture_Romeral_15km.xml <rupture_Romeral_15km.xml>`_                      
============= ============================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,SadighEtAl1997: ['SadighEtAl1997']>

Exposure model
--------------
=========== =
#assets     5
#sites      1
#taxonomies 5
=========== =

============== =======
Taxonomy       #Assets
============== =======
MUR/LWAL/HEX:1 1      
MUR/LWAL/HEX:2 1      
MUR/LWAL/HEX:3 1      
MUR/LWAL/HEX:4 1      
MUR/LWAL/HEX:5 1      
============== =======