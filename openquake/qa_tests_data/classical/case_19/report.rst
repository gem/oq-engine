SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     2_489_944_921      
date           2020-01-16T05:32:00
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 62, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
pointsource_distance            {'default': 50}   
ground_motion_correlation_model None              
minimum_intensity               {}                
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
========= ======= ===================== ================
smlt_path weight  gsim_logic_tree       num_realizations
========= ======= ===================== ================
b1        1.00000 simple(0,0,0,0,4,0,0) 4               
========= ======= ===================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================================================================================================== ================= ======================= =================
grp_id gsims                                                                                                                                                                              distances         siteparams              ruptparams       
====== ================================================================================================================================================================================== ================= ======================= =================
0      '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'                                                                                   rhypo rrup        vs30                    hypo_depth mag   
1      '[FaccioliEtAl2010]'                                                                                                                                                               rrup              vs30                    mag rake         
2      '[Campbell2003SHARE]' '[ToroEtAl2002SHARE]'                                                                                                                                        rjb rrup                                  mag rake         
3      '[AvgGMPE]\nb1.AkkarBommer2010.weight=0.20\nb2.CauzziFaccioli2008.weight=0.20\nb3.ChiouYoungs2008.weight=0.20\nb4.ToroEtAl2002SHARE.weight=0.20\nb5.Campbell2003SHARE.weight=0.20' rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      '[AtkinsonBoore2003SSlab]' '[LinLee2008SSlab]' '[YoungsEtAl1997SSlab]' '[ZhaoEtAl2006SSlab]'                                                                                       rhypo rrup        vs30                    hypo_depth mag   
====== ================================================================================================================================================================================== ================= ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=4)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       2_801        0.0         
1      NaN       35           0.0         
2      NaN       24_144       0.0         
3      NaN       20_362       0.0         
4      0.04762   23_352       1_974       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
s46       4      A    1_974        0.00821   0.04762   1_974       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00821  
C    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       1.22353 NaN     1.22353 1.22353 1      
preclassical       0.36570 0.75513 0.00881 2.95267 15     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================= ========
task         sent                                              received
SourceReader                                                   56.24 KB
preclassical params=333.16 KB srcfilter=88.65 KB srcs=56.61 KB 4.68 KB 
============ ================================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43343                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          5.48557   2.74609   15    
splitting/filtering sources 5.08059   1.75391   15    
composite source model      1.24209   0.0       1     
total SourceReader          1.22353   0.0       1     
store source_info           0.00244   0.0       1     
aggregate curves            1.791E-04 0.0       1     
=========================== ========= ========= ======