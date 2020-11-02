SHARE OpenQuake Computational Settings
======================================

============== ====================
checksum32     3_663_895_060       
date           2020-11-02T08:43:00 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 90, num_rlzs = 16

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 600), (10.0, 600)]}
investigation_time              50.0                                  
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            20.0                                  
complex_fault_mesh_spacing      20.0                                  
width_of_mfd_bin                0.2                                   
area_source_discretization      20.0                                  
pointsource_distance            {'default': [(1.0, 200), (10.0, 200)]}
ground_motion_correlation_model None                                  
minimum_intensity               {'default': 0.01}                     
random_seed                     23                                    
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                 `job.ini <job.ini>`_                                                      
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
====== ========================= ================
grp_id gsim                      rlzs            
====== ========================= ================
0      [AtkinsonBoore2003SInter] [0, 4, 8, 12]   
0      [LinLee2008SInter]        [1, 5, 9, 13]   
0      [YoungsEtAl1997SInter]    [2, 6, 10, 14]  
0      [ZhaoEtAl2006SInter]      [3, 7, 11, 15]  
1      [AtkinsonBoore2003SSlab]  [0, 1, 2, 3]    
1      [LinLee2008SSlab]         [4, 5, 6, 7]    
1      [YoungsEtAl1997SSlab]     [8, 9, 10, 11]  
1      [ZhaoEtAl2006SSlab]       [12, 13, 14, 15]
====== ========================= ================

Required parameters per tectonic region type
--------------------------------------------
===== ================================================================================================ ========== ========== ==============
et_id gsims                                                                                            distances  siteparams ruptparams    
===== ================================================================================================ ========== ========== ==============
0     '[AtkinsonBoore2003SSlab]' '[LinLee2008SSlab]' '[YoungsEtAl1997SSlab]' '[ZhaoEtAl2006SSlab]'     rhypo rrup vs30       hypo_depth mag
1     '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]' rhypo rrup vs30       hypo_depth mag
===== ================================================================================================ ========== ========== ==============

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
i17       C    0.00589   1         2_190       
s13       A    7.963E-05 1         3_150       
s46       A    6.986E-05 1         1_974       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.495E-04
C    0.00589  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.00651 nan    0.00651 0.00651
read_source_model  1      0.01462 nan    0.01462 0.01462
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      13.03 KB
preclassical           328 B   
================= ==== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46662, maxmem=0.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.32669  0.12891   1     
composite source model    0.32150  0.12891   1     
total read_source_model   0.01462  0.0       1     
total preclassical        0.00651  0.0       1     
========================= ======== ========= ======