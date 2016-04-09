scenario hazard
===============

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ==================
calculation_mode             'scenario'        
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           None              
ses_per_logic_tree_path      1                 
truncation_level             3.0               
rupture_mesh_spacing         2.0               
complex_fault_mesh_spacing   2.0               
width_of_mfd_bin             None              
area_source_discretization   None              
random_seed                  42                
master_seed                  0                 
concurrent_tasks             40                
============================ ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
exposure        `exposure_model.xml <exposure_model.xml>`_  
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job_haz.ini <job_haz.ini>`_                
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,BooreAtkinson2008: ['BooreAtkinson2008']
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
tax1     4      
tax2     2      
tax3     1      
======== =======

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.009     0.0       1     
reading exposure        0.005     0.0       1     
computing gmfs          0.002     0.0       1     
reading site collection 5.960E-06 0.0       1     
======================= ========= ========= ======