SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     561,276,680        
date           2019-07-30T15:04:23
engine_version 3.7.0-git3b3dff46da
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
========= ====== ==== ============ ========= ========= ====== ==========
source_id grp_id code num_ruptures calc_time num_sites weight speed     
========= ====== ==== ============ ========= ========= ====== ==========
s46       4      A    7,770        3.235E-04 1.00000   7,770  24,016,022
========= ====== ==== ============ ========= ========= ====== ==========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    3.235E-04 16    
C    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00347 0.00206 0.00171 0.00854 11     
read_source_models 4.90706 NaN     4.90706 4.90706 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================= ========
task               sent                                                          received
preclassical       srcs=51.97 KB params=13.62 KB gsims=4.52 KB srcfilter=2.56 KB 3.19 KB 
read_source_models converter=314 B fnames=112 B                                  45.09 KB
================== ============================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15530               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 4.90706  0.0       1     
total preclassical       0.03817  0.0       11    
managing sources         0.00592  0.0       1     
store source_info        0.00211  0.0       1     
aggregate curves         0.00134  0.0       11    
======================== ======== ========= ======