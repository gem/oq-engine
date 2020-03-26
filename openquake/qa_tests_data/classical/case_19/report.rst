SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     520_854_033        
date           2020-03-13T11:23:11
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 62, num_rlzs = 32

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
pointsource_distance            {'default': 50}   
ground_motion_correlation_model None              
minimum_intensity               {'default': 0.01} 
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 32              
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================================================================================================== ================= ======================= =================
grp_id gsims                                                                                                                                                                              distances         siteparams              ruptparams       
====== ================================================================================================================================================================================== ================= ======================= =================
0      '[Campbell2003SHARE]' '[ToroEtAl2002SHARE]'                                                                                                                                        rjb rrup                                  mag rake         
1      '[AvgGMPE]\nb1.AkkarBommer2010.weight=0.20\nb2.CauzziFaccioli2008.weight=0.20\nb3.ChiouYoungs2008.weight=0.20\nb4.ToroEtAl2002SHARE.weight=0.20\nb5.Campbell2003SHARE.weight=0.20' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[AtkinsonBoore2003SSlab]' '[LinLee2008SSlab]' '[YoungsEtAl1997SSlab]' '[ZhaoEtAl2006SSlab]'                                                                                       rhypo rrup        vs30                    hypo_depth mag   
3      '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'                                                                                   rhypo rrup        vs30                    hypo_depth mag   
4      '[FaccioliEtAl2010]'                                                                                                                                                               rrup              vs30                    mag rake         
====== ================================================================================================================================================================================== ================= ======================= =================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       24_144       0.0         
1      NaN       20_362       0.0         
2      0.04762   23_352       3_129       
3      0.01209   2_801        1_737       
4      NaN       35           0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
i17       3      C    2_190        0.03576   0.01209   1_737       
s46       2      A    1_974        0.00882   0.04762   1_974       
s13       2      A    3_150        0.00570   0.04762   1_155       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01452  
C    0.03576  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.39588 0.81821 0.00873 3.17884 15     
read_source_model  1.22086 NaN     1.22086 1.22086 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ================================================= ========
task              sent                                              received
read_source_model                                                   44.35 KB
preclassical      params=113.73 KB srcs=65.06 KB srcfilter=50.65 KB 4.82 KB 
================= ================================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67014                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          5.93813   2.03906   15    
splitting/filtering sources 5.48939   1.51172   15    
composite source model      1.24949   0.13672   1     
total read_source_model     1.22086   0.13672   1     
store source_info           0.00224   0.0       1     
aggregate curves            8.199E-04 0.0       3     
=========================== ========= ========= ======