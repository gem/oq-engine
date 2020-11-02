Event Based Bogota
==================

============== ====================
checksum32     13_057_122          
date           2020-11-02T08:41:24 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 5, num_levels = 4, num_rlzs = 100

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    100                                   
maximum_distance                {'default': [(1.0, 100), (10.0, 100)]}
investigation_time              1.0                                   
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            5.0                                   
complex_fault_mesh_spacing      5.0                                   
width_of_mfd_bin                0.2                                   
area_source_discretization      10.0                                  
pointsource_distance            None                                  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     113                                   
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================== ==================================================================
Name                     File                                                              
======================== ==================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                        
gsim_logic_tree          `logic_tree_gmpe_simplified.xml <logic_tree_gmpe_simplified.xml>`_
job_ini                  `job.ini <job.ini>`_                                              
site_model               `site_model_bog.xml <site_model_bog.xml>`_                        
source_model_logic_tree  `logic_tree_source_model.xml <logic_tree_source_model.xml>`_      
structural_vulnerability `vulnerability_model_bog.xml <vulnerability_model_bog.xml>`_      
======================== ==================================================================

Composite source model
----------------------
====== ========================== =================================================================================================================================================================
grp_id gsim                       rlzs                                                                                                                                                             
====== ========================== =================================================================================================================================================================
0      [AbrahamsonEtAl2015SInter] [4, 6, 8, 9, 13, 16, 20, 21, 24, 31, 32, 33, 35, 39, 40, 41, 44, 45, 46, 57, 58, 60, 62, 64, 65, 69, 72, 73, 81, 84, 92, 94, 99]                                 
0      [YoungsEtAl1997SInter]     [1, 2, 3, 5, 10, 12, 15, 23, 25, 27, 30, 34, 36, 37, 43, 48, 50, 53, 54, 55, 61, 66, 68, 70, 74, 75, 77, 79, 80, 82, 83, 85, 89, 95, 97, 98]                     
0      [ZhaoEtAl2006SInter]       [0, 7, 11, 14, 17, 18, 19, 22, 26, 28, 29, 38, 42, 47, 49, 51, 52, 56, 59, 63, 67, 71, 76, 78, 86, 87, 88, 90, 91, 93, 96]                                       
1      [AkkarCagnan2010]          [0, 3, 7, 10, 20, 21, 23, 33, 42, 43, 47, 55, 65, 66, 72, 73, 74, 78, 82, 91, 92, 93, 94]                                                                        
1      [AkkarEtAlRhyp2014]        [5, 6, 8, 13, 14, 16, 17, 22, 26, 27, 29, 30, 32, 34, 35, 36, 37, 39, 45, 46, 48, 49, 50, 51, 53, 59, 62, 63, 69, 70, 71, 75, 77, 79, 80, 84, 86, 87, 89, 97, 99]
1      [BindiEtAl2014Rjb]         [1, 2, 4, 9, 11, 12, 15, 18, 19, 24, 25, 28, 31, 38, 40, 41, 44, 52, 54, 56, 57, 58, 60, 61, 64, 67, 68, 76, 81, 83, 85, 88, 90, 95, 96, 98]                     
====== ========================== =================================================================================================================================================================

Required parameters per tectonic region type
--------------------------------------------
===== ============================================================================ ========= ============ ==============
et_id gsims                                                                        distances siteparams   ruptparams    
===== ============================================================================ ========= ============ ==============
0     '[AkkarCagnan2010]' '[AkkarEtAlRhyp2014]' '[BindiEtAl2014Rjb]'               rhypo rjb vs30         mag rake      
1     '[AbrahamsonEtAl2015SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]' rrup      backarc vs30 hypo_depth mag
===== ============================================================================ ========= ============ ==============

Exposure model
--------------
=========== =
#assets     5
#taxonomies 4
=========== =

===================== ========== ======= ====== === === =========
taxonomy              num_assets mean    stddev min max num_sites
MCF/LWAL+DUC/HBET:3,6 2          1.00000 0%     1   1   2        
MUR/HBET:4,5          1          1.00000 nan    1   1   1        
CR/LDUAL+DUC          1          1.00000 nan    1   1   1        
CR/LFINF+DUC          1          1.00000 nan    1   1   1        
*ALL*                 5          1.00000 0%     1   1   5        
===================== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
CC_03_3   P    2.627E-04 5         108         
CC_64_406 P    2.615E-04 3         84          
CC_64_412 P    2.613E-04 3         84          
CC_67_172 P    2.544E-04 5         63          
CC_64_407 P    1.926E-04 5         84          
CC_67_173 P    1.912E-04 5         63          
CC_57_58  P    1.876E-04 5         15          
CC_64_408 P    1.874E-04 3         84          
CC_67_167 P    1.807E-04 2         63          
CC_66_82  P    1.795E-04 5         30          
CC_67_168 P    1.788E-04 3         63          
CC_03_31  P    1.786E-04 5         108         
CC_67_174 P    1.783E-04 5         63          
CC_64_411 P    1.760E-04 3         84          
CC_02_38  P    1.743E-04 5         108         
CC_67_175 P    1.733E-04 5         63          
CC_03_70  P    1.705E-04 5         108         
CC_02_63  P    1.698E-04 5         108         
CC_64_409 P    1.695E-04 5         84          
CC_03_77  P    1.688E-04 5         108         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.0      
P    0.01501  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       18     0.00170 54%    0.00120 0.00538
read_source_model  2      0.02536 73%    0.00677 0.04396
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model converter=664 B fname=221 B     68.02 KB
preclassical      srcs=87.4 KB srcfilter=32.17 KB 9.25 KB 
================= =============================== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46568, maxmem=1.5 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          1.72290   0.75000   1     
composite source model    1.67037   0.75000   1     
total read_source_model   0.05073   1.86328   2     
total preclassical        0.03060   0.28906   18    
reading exposure          5.550E-04 0.0       1     
========================= ========= ========= ======