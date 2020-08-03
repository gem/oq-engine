Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

============== ===================
checksum32     2_398_350_176      
date           2020-03-13T11:21:24
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         150               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        123456789         
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    1            0.00142   2.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00142  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00210 NaN    0.00210 0.00210 1      
read_source_model  0.00102 NaN    0.00102 0.00102 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model                                           1.45 KB 
preclassical      srcs=1.11 KB params=612 B srcfilter=223 B 369 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66937                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01031   0.0       1     
store source_info           0.00272   0.0       1     
total preclassical          0.00210   0.50000   1     
total read_source_model     0.00102   0.0       1     
aggregate curves            4.146E-04 0.0       1     
splitting/filtering sources 2.005E-04 0.0       1     
=========================== ========= ========= ======