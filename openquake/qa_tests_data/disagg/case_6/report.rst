GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ====================
checksum32     1_106_876_662       
date           2020-11-02T09:35:34 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 20, num_rlzs = 3

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 300), (10.0, 300)]}
investigation_time              1.0                                   
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            5.0                                   
complex_fault_mesh_spacing      10.0                                  
width_of_mfd_bin                0.1                                   
area_source_discretization      10.0                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     23                                    
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
====== ===================== ====
grp_id gsim                  rlzs
====== ===================== ====
0      '[BooreAtkinson2008]' [0] 
0      '[ChiouYoungs2008]'   [1] 
0      '[ZhaoEtAl2006Asc]'   [2] 
====== ===================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ============================================================= =========== ======================= ============================
et_id gsims                                                         distances   siteparams              ruptparams                  
===== ============================================================= =========== ======================= ============================
0     '[BooreAtkinson2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
===== ============================================================= =========== ======================= ============================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
32        S    0.02264   1         80          
19        S    0.02205   1         86          
36        S    0.01971   1         67          
39        S    0.01935   1         61          
28        S    0.01599   1         55          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.09974  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       5      0.02045 11%    0.01652 0.02314
read_source_model  1      0.03854 nan    0.03854 0.03854
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 28.2 KB 
preclassical      srcs=33.03 KB srcfilter=4.96 KB 1.17 KB 
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47240, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.54000  0.00391   1     
composite source model    0.53222  0.00391   1     
total preclassical        0.10227  0.32422   5     
total read_source_model   0.03854  0.0       1     
========================= ======== ========= ======