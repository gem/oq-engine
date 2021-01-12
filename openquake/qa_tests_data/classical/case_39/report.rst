Reduced USGS 1998 Hawaii model
==============================

============== ====================
checksum32     3_138_901_998       
date           2020-11-02T09:36:57 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 80, num_rlzs = 8

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
pointsource_distance            {'default': [(1.0, 0), (10.0, 0)]}    
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
====== ============================== ========================
grp_id gsim                           rlzs                    
====== ============================== ========================
0      '[BooreEtAl1997GeometricMean]' [0, 1]                  
0      '[Campbell1997]'               [2, 3]                  
0      '[MunsonThurber1997Hawaii]'    [4, 5]                  
0      '[SadighEtAl1997]'             [6, 7]                  
1      '[MunsonThurber1997Hawaii]'    [0, 2, 4, 6]            
1      '[SadighEtAl1997]'             [1, 3, 5, 7]            
2      '[YoungsEtAl1997SSlab]'        [0, 1, 2, 3, 4, 5, 6, 7]
====== ============================== ========================

Required parameters per tectonic region type
--------------------------------------------
===== ============================================================================================== ========= ========== ==============
et_id gsims                                                                                          distances siteparams ruptparams    
===== ============================================================================================== ========= ========== ==============
0     '[YoungsEtAl1997SSlab]'                                                                        rrup      vs30       hypo_depth mag
1     '[BooreEtAl1997GeometricMean]' '[Campbell1997]' '[MunsonThurber1997Hawaii]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake      
2     '[MunsonThurber1997Hawaii]' '[SadighEtAl1997]'                                                 rjb rrup  vs30       mag rake      
===== ============================================================================================== ========= ========== ==============

Slowest sources
---------------
========== ==== ========= ========= ============
source_id  code calc_time num_sites eff_ruptures
========== ==== ========= ========= ============
HLEKAOSFL  C    0.00230   1         104         
HLE        A    3.424E-04 1         6_945       
Deep_10014 P    2.983E-04 1         45          
========== ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    3.424E-04
C    0.00230  
P    2.983E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.00368 nan    0.00368 0.00368
read_source_model  3      0.00238 26%    0.00153 0.00298
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =========================== ========
task              sent                        received
read_source_model converter=996 B fname=341 B 5.55 KB 
preclassical                                  341 B   
================= =========================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47336, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.26366  0.0       1     
composite source model    1.25846  0.0       1     
total read_source_model   0.00714  0.68750   3     
total preclassical        0.00368  0.0       1     
========================= ======== ========= ======