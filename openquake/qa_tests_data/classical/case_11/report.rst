Classical Hazard QA Test, Case 11
=================================

============== ====================
checksum32     3_864_872_563       
date           2020-11-02T08:42:52 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 3

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
====== ================ ====
grp_id gsim             rlzs
====== ================ ====
0      [SadighEtAl1997] [0] 
1      [SadighEtAl1997] [1] 
2      [SadighEtAl1997] [2] 
====== ================ ====

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
1     '[SadighEtAl1997]' rrup      vs30       mag rake  
2     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1;0       P    0.00495   1         3_500       
1;1       P    0.00420   1         3_000       
1;2       P    0.00341   1         2_500       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.01256  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       3      0.00468 13%    0.00392 0.00545
read_source_model  1      0.00268 nan    0.00268 0.00268
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 1.46 KB 
preclassical      srcfilter=29.21 KB srcs=3.54 KB 723 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46655, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.09927  0.0       1     
composite source model    0.09418  0.0       1     
total preclassical        0.01405  0.86328   3     
total read_source_model   0.00268  0.0       1     
========================= ======== ========= ======