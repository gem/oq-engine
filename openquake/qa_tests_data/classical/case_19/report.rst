SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     561,276,680        
date           2019-10-01T06:32:48
engine_version 3.8.0-git66affb82eb
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.0       42,624       0.0         
1      0.0       210          0.0         
2      0.0       96,804       0.0         
3      0.0       81,154       0.0         
4      1.00000   93,219       7,770       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========= ====== ==== ============ ========= ========= ============ =========
s46       4      A    7,770        0.00218   1.00000   7,770        3,565,617
========= ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00218   16    
C    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       5.59039 NaN     5.59039 5.59039 1      
preclassical       0.00392 0.00311 0.00162 0.01310 17     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader                                             77.09 KB
preclassical srcs=58.66 KB params=21.05 KB gsims=7.63 KB 4.9 KB  
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6503              time_sec memory_mb counts
====================== ======== ========= ======
composite source model 5.60715  0.0       1     
total SourceReader     5.59039  0.41016   1     
total preclassical     0.06663  0.25391   17    
aggregate curves       0.00387  0.0       17    
store source_info      0.00260  0.0       1     
====================== ======== ========= ======