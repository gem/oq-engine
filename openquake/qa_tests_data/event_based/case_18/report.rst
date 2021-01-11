Event-Based Hazard QA Test, Case 18
===================================

============== ====================
checksum32     3_211_005_400       
date           2020-11-02T09:36:25 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 3

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    3                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         350                                       
truncation_level                0.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.001                                     
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1064                                      
master_seed                     0                                         
ses_seed                        1064                                      
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ====================== ======
grp_id gsim                   rlzs  
====== ====================== ======
0      '[AkkarBommer2010]'    [0]   
0      '[CauzziFaccioli2008]' [1, 2]
====== ====================== ======

Required parameters per tectonic region type
--------------------------------------------
===== ============================================================== ================= ======================= =================
et_id gsims                                                          distances         siteparams              ruptparams       
===== ============================================================== ================= ======================= =================
0     '[AkkarBommer2010]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== ============================================================== ================= ======================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         P    0.00410   1         3_000       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00410  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.00453 nan    0.00453 0.00453
read_source_model  1      0.00263 nan    0.00263 0.00263
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.47 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47302, maxmem=0.3 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.07007  0.0       1     
composite source model    0.06488  0.0       1     
total preclassical        0.00453  0.0       1     
total read_source_model   0.00263  0.0       1     
========================= ======== ========= ======