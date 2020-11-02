Classical Hazard QA Test, Case 2
================================

============== ====================
checksum32     1_768_482_896       
date           2020-11-02T08:42:57 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                0.0                                       
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
width_of_mfd_bin                0.001                                     
area_source_discretization      None                                      
pointsource_distance            {'default': [(1.0, 0), (10.0, 0)]}        
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1066                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
========================= ============================================================
Name                      File                                                        
========================= ============================================================
gsim_logic_tree           `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                   `job.ini <job.ini>`_                                        
reqv:active shallow crust `lookup_asc.hdf5 <lookup_asc.hdf5>`_                        
reqv:stable shallow crust `lookup_sta.hdf5 <lookup_sta.hdf5>`_                        
source_model_logic_tree   `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
========================= ============================================================

Composite source model
----------------------
====== ================ ====
grp_id gsim             rlzs
====== ================ ====
0      [SadighEtAl1997] [0] 
1      [SadighEtAl1997] [0] 
====== ================ ====

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
1         P    0.00390   1         3_000       
2         P    0.00382   1         3_000       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00772  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       2      0.00436 1%     0.00431 0.00441
read_source_model  1      0.00320 nan    0.00320 0.00320
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 1.93 KB 
preclassical      srcfilter=32.28 KB srcs=2.32 KB 478 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46659, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.08757  0.0       1     
composite source model    0.08229  0.0       1     
total preclassical        0.00872  0.57422   2     
total read_source_model   0.00320  0.0       1     
========================= ======== ========= ======