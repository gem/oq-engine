QA test for disaggregation case_2
=================================

============== ====================
checksum32     15_434_903          
date           2020-11-02T09:35:46 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 1, num_rlzs = 4

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    0                                       
maximum_distance                {'default': [(1.0, 80.0), (10.0, 80.0)]}
investigation_time              1.0                                     
ses_per_logic_tree_path         1                                       
truncation_level                3.0                                     
rupture_mesh_spacing            4.0                                     
complex_fault_mesh_spacing      4.0                                     
width_of_mfd_bin                1.0                                     
area_source_discretization      100.0                                   
pointsource_distance            None                                    
ground_motion_correlation_model None                                    
minimum_intensity               {}                                      
random_seed                     23                                      
master_seed                     0                                       
ses_seed                        42                                      
=============================== ========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
site_model              `site_model.csv <site_model.csv>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ===================== ====
grp_id gsim                  rlzs
====== ===================== ====
0      '[BooreAtkinson2008]' [0] 
0      '[ChiouYoungs2008]'   [1] 
1      '[BooreAtkinson2008]' [2] 
1      '[ChiouYoungs2008]'   [3] 
====== ===================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ========================================= =========== ======================= =================
et_id gsims                                     distances   siteparams              ruptparams       
===== ========================================= =========== ======================= =================
0     '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1     '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== ========================================= =========== ======================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1;1       S    0.00266   1         148         
1;0       A    1.762E-04 1         2           
3         A    1.469E-04 1         2           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    3.231E-04
S    0.00266  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       3      0.00148 79%    6.478E-04 0.00315
read_source_model  2      0.00251 42%    0.00144   0.00359
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model converter=704 B fname=190 B    3.53 KB 
preclassical      srcs=5.28 KB srcfilter=2.58 KB 721 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47247, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.05213  0.00391   1     
composite source model    1.04509  0.00391   1     
total read_source_model   0.00503  0.81641   2     
total preclassical        0.00445  0.45703   3     
========================= ======== ========= ======