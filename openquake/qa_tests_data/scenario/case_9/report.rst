Scenario QA Test, Case 9, Multiple GSIMs
========================================

============== ===================
checksum32     2_644_086_889      
date           2020-01-16T05:30:41
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 3, num_levels = 1, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                1.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                None              
area_source_discretization      None              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job.ini <job.ini>`_                        
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 simple(2)       2               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
========== ======== ========= ======
calc_43201 time_sec memory_mb counts
========== ======== ========= ======
========== ======== ========= ======