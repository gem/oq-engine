Classical Hazard QA Test, Case 10
=================================

============== ====================
checksum32     3_216_683_212       
date           2020-11-02T09:36:56 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                0.0                                       
rupture_mesh_spacing            0.01                                      
complex_fault_mesh_spacing      0.01                                      
width_of_mfd_bin                0.001                                     
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
1      '[SadighEtAl1997]' [1] 
====== ================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
1     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1;1       P    0.00405   1         3_000       
1;0       P    0.00376   1         3_000       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00781  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       2      0.00438 3%     0.00423 0.00454
read_source_model  1      0.00186 nan    0.00186 0.00186
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 1.46 KB 
preclassical      srcfilter=16.94 KB srcs=2.36 KB 482 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47335, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.08287  0.00391   1     
composite source model    0.07774  0.00391   1     
total preclassical        0.00877  0.89453   2     
total read_source_model   0.00186  0.0       1     
========================= ======== ========= ======