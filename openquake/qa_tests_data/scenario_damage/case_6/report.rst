oq-test03, depth=15km
=====================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48235.hdf5 updated Wed Sep  7 15:55:41 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ =================
calculation_mode             'scenario'       
number_of_logic_tree_samples 0                
maximum_distance             {u'default': 300}
investigation_time           None             
ses_per_logic_tree_path      1                
truncation_level             3.0              
rupture_mesh_spacing         0.1              
complex_fault_mesh_spacing   0.1              
width_of_mfd_bin             None             
area_source_discretization   None             
random_seed                  3                
master_seed                  0                
============================ =================

Input files
-----------
==================== ============================================================================
Name                 File                                                                        
==================== ============================================================================
exposure             `exposure_model_Antioquia_test03.xml <exposure_model_Antioquia_test03.xml>`_
job_ini              `job_h.ini <job_h.ini>`_                                                    
rupture_model        `rupture_Romeral_15km.xml <rupture_Romeral_15km.xml>`_                      
structural_fragility `fragility_model_test03.xml <fragility_model_test03.xml>`_                  
==================== ============================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=============== ========
#assets         5       
#taxonomies     5       
deductibile     absolute
insurance_limit absolute
=============== ========

============== ===== ====== === === ========= ==========
taxonomy       mean  stddev min max num_sites num_assets
MUR/LWAL/HEX:1 1.000 NaN    1   1   1         1         
MUR/LWAL/HEX:2 1.000 NaN    1   1   1         1         
MUR/LWAL/HEX:3 1.000 NaN    1   1   1         1         
MUR/LWAL/HEX:4 1.000 NaN    1   1   1         1         
MUR/LWAL/HEX:5 1.000 NaN    1   1   1         1         
*ALL*          5.000 NaN    5   5   1         5         
============== ===== ====== === === ========= ==========

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading exposure        0.003     0.0       1     
filtering sites         0.001     0.0       1     
reading site collection 5.007E-06 0.0       1     
======================= ========= ========= ======