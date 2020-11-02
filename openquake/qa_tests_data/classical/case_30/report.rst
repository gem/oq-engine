Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ====================
checksum32     2_014_937_050       
date           2020-11-02T09:14:45 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 5, num_levels = 20, num_rlzs = 12

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
complex_fault_mesh_spacing      50.0                                  
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
======================= ============================
Name                    File                        
======================= ============================
gsim_logic_tree         `gmmLT_3.xml <gmmLT_3.xml>`_
job_ini                 `job.ini <job.ini>`_        
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_    
======================= ============================

Composite source model
----------------------
====== =========================== =============
grp_id gsim                        rlzs         
====== =========================== =============
0      '[BooreAtkinson2008]'       [0, 1, 2]    
0      '[CampbellBozorgnia2008]'   [3, 4, 5]    
0      '[ChiouYoungs2008]'         [6, 7, 8]    
0      '[ZhaoEtAl2006Asc]'         [9, 10, 11]  
1      '[AtkinsonBoore2003SInter]' [0, 3, 6, 9] 
1      '[YoungsEtAl1997SInter]'    [1, 4, 7, 10]
1      '[ZhaoEtAl2006SInter]'      [2, 5, 8, 11]
====== =========================== =============

Required parameters per tectonic region type
--------------------------------------------
===== ======================================================================================= =========== ============================= ============================
et_id gsims                                                                                   distances   siteparams                    ruptparams                  
===== ======================================================================================= =========== ============================= ============================
0     '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
1     '[AtkinsonBoore2003SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'             rrup        vs30                          hypo_depth mag              
===== ======================================================================================= =========== ============================= ============================

Slowest sources
---------------
========== ==== ========= ========= ============
source_id  code calc_time num_sites eff_ruptures
========== ==== ========= ========= ============
sf_81      S    0.01522   3         348         
kt         C    0.01497   5         3_536       
sf_85      S    0.01485   3         348         
sf_84      S    0.01151   1         262         
sf_83      S    0.00987   1         113         
sf_82      S    0.00954   1         46          
ds_4_19558 P    1.979E-04 1         100         
ds_4_2111  P    1.938E-04 1         100         
ds_4_482   P    1.802E-04 1         100         
ds_4_36349 P    1.423E-04 1         100         
ds_4_8499  P    1.369E-04 4         100         
ds_4_18232 P    1.347E-04 3         100         
ds_4_5043  P    1.285E-04 2         100         
ds_4_6534  P    1.283E-04 3         100         
ds_4_8502  P    1.280E-04 4         100         
ds_4_15201 P    1.261E-04 4         100         
ds_4_464   P    1.223E-04 1         100         
========== ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.01497  
P    0.00162  
S    0.06099  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       15     0.00590 178%   8.254E-04 0.03144
read_source_model  3      0.01504 8%     0.01319   0.01601
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ================================ ========
task              sent                             received
read_source_model converter=996 B fname=338 B      60.93 KB
preclassical      srcs=74.61 KB srcfilter=36.78 KB 3.69 KB 
================= ================================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47008, maxmem=1.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.54976  0.0       1     
composite source model    1.54490  0.0       1     
total preclassical        0.08851  0.32812   15    
total read_source_model   0.04512  0.93750   3     
========================= ======== ========= ======