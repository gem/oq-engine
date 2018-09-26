Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,726,424,986      
date           2018-09-25T14:28:01
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 100, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              30.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.1              
area_source_discretization      18.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     42               
master_seed                     0                
ses_seed                        23               
=============================== =================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source                  `as_model.xml <as_model.xml>`_                                                
source                  `fs_bg_source_model.xml <fs_bg_source_model.xml>`_                            
source                  `ss_model_final_250km_Buffer.xml <ss_model_final_250km_Buffer.xml>`_          
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        0.50000 complex(4,5,2,1) 1/1             
b2        0.20000 complex(4,5,2,1) 5/5             
b3        0.30000 complex(4,5,2,1) 1/8             
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= ============================
grp_id gsims                                                                                            distances         siteparams              ruptparams                  
====== ================================================================================================ ================= ======================= ============================
0      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
1      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor           
2      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc()                       rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
3      Campbell2003SHARE() ToroEtAl2002SHARE()                                                          rjb rrup                                  mag rake                    
4      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
====== ================================================================================================ ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=7, rlzs=7)
  0,FaccioliEtAl2010(): [0]
  1,AkkarBommer2010(): [1]
  1,Campbell2003SHARE(): [5]
  1,CauzziFaccioli2008(): [2]
  1,ChiouYoungs2008(): [3]
  1,ToroEtAl2002SHARE(): [4]
  4,FaccioliEtAl2010(): [6]>

Number of ruptures per tectonic region type
-------------------------------------------
============================================= ====== ==================== ============ ============
source_model                                  grp_id trt                  eff_ruptures tot_ruptures
============================================= ====== ==================== ============ ============
source_models/as_model.xml                    0      Volcanic             14           14          
source_models/fs_bg_source_model.xml          1      Stable Shallow Crust 1,693        4,385       
source_models/ss_model_final_250km_Buffer.xml 4      Volcanic             640          640         
============================================= ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 2,347
#tot_ruptures 5,192
#tot_weight   0    
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         A    0     4     7            0.00998   0.00195    5.00000   1         1.00000
0      2         A    4     8     7            0.00540   0.00170    5.00000   1         0.0    
1      1339      A    0     10    168          0.14685   0.07533    93        12        0.0    
1      19        S    10    73    349          0.34330   0.00211    108       12        0.0    
1      20        S    73    92    31           0.02514   4.907E-04  54        6         0.0    
1      21        S    92    101   7            0.00865   2.317E-04  36        4         0.0    
1      22        S    101   115   34           0.04201   4.578E-04  6.00000   6         0.0    
1      246       A    115   121   156          0.11132   0.05351    58        13        1.00000
1      247       A    121   127   156          0.12990   0.05207    58        13        0.0    
1      248       A    127   138   384          0.07519   0.07538    14        7         0.0    
1      249       A    138   149   384          0.07426   0.07528    14        7         0.0    
1      250       A    149   160   384          0.06949   0.07607    13        7         0.0    
1      257       A    160   173   96           0.08509   0.02479    47        8         1.00000
1      258       A    173   186   96           0.06622   0.02252    47        8         0.0    
1      259       A    186   199   96           0.05775   0.02238    47        8         0.0    
1      263       A    199   211   1,022        0.11414   0.18429    11        9         0.0    
1      264       A    211   223   1,022        0.10685   0.18544    11        9         0.0    
2      101622    P    0     1     39           0.0       0.0        0.0       0         0.0    
2      101623    P    1     2     36           0.0       0.0        0.0       0         0.0    
3      323839    P    2     3     6            0.0       0.0        0.0       0         0.0    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    1.05245   13    
P    0.46321   51    
S    0.41909   4     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.05379 0.06733 0.01184 0.13146 3        
split_filter       0.20918 NaN     0.20918 0.20918 1        
build_ruptures     0.11309 0.03867 0.01974 0.20136 18       
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ======================================================================== =========
task               sent                                                                     received 
read_source_models monitor=993 B converter=957 B fnames=608 B                               45.33 KB 
split_filter       srcs=67.18 KB monitor=343 B srcfilter=220 B sample_factor=21 B seed=14 B 77.7 KB  
build_ruptures     srcs=99.43 KB param=17.42 KB monitor=6.06 KB srcfilter=3.87 KB           123.26 KB
================== ======================================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total build_ruptures     2.03556  0.16016   18    
updating source_info     0.23128  0.0       1     
total split_filter       0.20918  0.25781   1     
total read_source_models 0.16138  0.0       3     
store source_info        0.01003  0.0       1     
saving ruptures          0.00875  0.0       3     
making contexts          0.00300  0.0       3     
======================== ======== ========= ======