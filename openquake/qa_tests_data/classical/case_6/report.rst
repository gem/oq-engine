Classical Hazard QA Test, Case 6
================================

============== ====================
checksum32     1_182_982_716       
date           2020-11-02T09:36:52 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                0.0                                       
rupture_mesh_spacing            0.1                                       
complex_fault_mesh_spacing      0.1                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1066                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ================== ====
grp_id gsim               rlzs
====== ================== ====
0      '[SadighEtAl1997]' [0] 
====== ================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         S    0.00197   1         91          
2         C    0.00146   1         49          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00146  
S    0.00197  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       2      0.00221 12%    0.00195 0.00248
read_source_model  1      0.00551 nan    0.00551 0.00551
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ============================= ========
task              sent                          received
read_source_model                               1.97 KB 
preclassical      srcs=2.43 KB srcfilter=1.7 KB 478 B   
================= ============================= ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47329, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.24007  0.0       1     
composite source model    0.23530  0.0       1     
total read_source_model   0.00551  0.0       1     
total preclassical        0.00443  0.25781   2     
========================= ======== ========= ======