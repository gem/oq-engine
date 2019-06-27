SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     561,276,680        
date           2019-06-24T15:34:30
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 1, num_levels = 78, num_rlzs = 4

Parameters
----------
=============================== ===========================================
calculation_mode                'preclassical'                             
number_of_logic_tree_samples    0                                          
maximum_distance                {'default': [(6, 100), (7, 150), (9, 200)]}
investigation_time              50.0                                       
ses_per_logic_tree_path         1                                          
truncation_level                3.0                                        
rupture_mesh_spacing            5.0                                        
complex_fault_mesh_spacing      5.0                                        
width_of_mfd_bin                0.2                                        
area_source_discretization      10.0                                       
ground_motion_correlation_model None                                       
minimum_intensity               {'default': 0.01}                          
random_seed                     23                                         
master_seed                     0                                          
ses_seed                        42                                         
=============================== ===========================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ======= ===================== ================
smlt_path weight  gsim_logic_tree       num_realizations
========= ======= ===================== ================
b1        1.00000 simple(0,0,0,0,4,0,0) 4               
========= ======= ===================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================================================== ================= ======================= =================
grp_id gsims                                                                                                      distances         siteparams              ruptparams       
====== ========================================================================================================== ================= ======================= =================
0      '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'           rhypo rrup        vs30                    hypo_depth mag   
1      '[FaccioliEtAl2010]'                                                                                       rrup              vs30                    mag rake         
2      '[Campbell2003SHARE]' '[ToroEtAl2002SHARE]'                                                                rjb rrup                                  mag rake         
3      '[AkkarBommer2010]' '[Campbell2003SHARE]' '[CauzziFaccioli2008]' '[ChiouYoungs2008]' '[ToroEtAl2002SHARE]' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      '[AtkinsonBoore2003SSlab]' '[LinLee2008SSlab]' '[YoungsEtAl1997SSlab]' '[ZhaoEtAl2006SSlab]'               rhypo rrup        vs30                    hypo_depth mag   
====== ========================================================================================================== ================= ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=4)>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= ============ ============
source_model                 grp_id trt               eff_ruptures tot_ruptures
============================ ====== ================= ============ ============
simple_area_source_model.xml 4      Subduction Inslab 7,770        93,219      
============================ ====== ================= ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
4      s46       A    657   683   7,770        0.00197   1.00000   7,770  2,852,734,143
4      s72       A    711   739   17,871       0.0       0.0       0.0    1,977,114,719
4      s70       A    683   711   17,871       0.0       0.0       0.0    3,832,569,365
4      s40       A    631   657   12,327       0.0       0.0       0.0    3,956,227,801
4      s35       A    605   631   12,327       0.0       0.0       0.0    990,461,867  
4      s34       A    579   605   12,327       0.0       0.0       0.0    2,274,246,164
4      s13       A    553   579   12,726       0.0       0.0       0.0    1,042,234,960
3      scr304    A    543   553   574          0.0       0.0       0.0    3,910,288,631
3      scr301    A    506   543   17,268       0.0       0.0       0.0    3,347,111,836
3      scr299    A    496   506   1,572        0.0       0.0       0.0    3,735,043,013
3      scr293    A    369   496   61,740       0.0       0.0       0.0    2,028,214,874
2      sh6       A    362   369   12,900       0.0       0.0       0.0    3,234,145,728
2      sh14      A    350   362   41,952       0.0       0.0       0.0    1,218,226,378
2      sh13      A    338   350   41,952       0.0       0.0       0.0    3,658,982,998
1      v4        A    327   338   168          0.0       0.0       0.0    283,848,614  
1      v1        A    323   327   42           0.0       0.0       0.0    3,293,169,139
0      i20       C    217   323   9,241        0.0       0.0       0.0    3,818,613,729
0      i17       C    0     217   33,383       0.0       0.0       0.0    1,465,178,582
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00197   16    
C    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00391 0.00290 0.00161 0.01340 17     
read_source_models 5.61911 NaN     5.61911 5.61911 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ ========
task               sent                                                         received
preclassical       srcs=58.85 KB params=20.4 KB gsims=7.63 KB srcfilter=3.95 KB 4.9 KB  
read_source_models converter=313 B fnames=119 B                                 45.1 KB 
================== ============================================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 5.61911  0.82812   1     
total preclassical       0.06642  0.0       17    
managing sources         0.01662  0.0       1     
aggregate curves         0.00263  0.0       17    
store source_info        0.00194  0.0       1     
======================== ======== ========= ======