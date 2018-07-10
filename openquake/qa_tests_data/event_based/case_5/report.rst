Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,726,424,986      
date           2018-06-26T14:58:35
engine_version 3.2.0-gitb0cd949   
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
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
0      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
1      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
====== ================================================================================================ ================= ======================= =================

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
#tot_ruptures 5,039
#tot_weight   9,119
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
19        SimpleFaultSource 16           0.40192   0.0        9.00000   12        0     
1339      PointSource       14           0.20183   0.0        7.75000   12        0     
264       PointSource       14           0.12124   0.0        1.22222   9         0     
258       PointSource       12           0.11832   0.0        5.87500   8         3     
246       PointSource       12           0.11829   0.0        4.46154   13        6     
257       PointSource       12           0.10986   0.0        5.87500   8         5     
247       PointSource       12           0.10517   0.0        4.46154   13        0     
263       PointSource       14           0.10493   0.0        1.22222   9         0     
249       PointSource       12           0.09161   0.0        2.00000   7         0     
248       PointSource       12           0.08654   0.0        2.00000   7         0     
259       PointSource       12           0.08376   0.0        5.87500   8         0     
250       PointSource       12           0.06939   0.0        1.85714   7         0     
22        SimpleFaultSource 2            0.05401   0.0        1.00000   6         0     
20        SimpleFaultSource 2            0.04281   0.0        9.00000   6         0     
330045    PointSource       22           0.03732   0.0        7.00000   1         0     
330076    PointSource       18           0.03663   0.0        5.00000   1         0     
330077    PointSource       20           0.02000   0.0        5.00000   1         0     
330046    PointSource       20           0.01868   0.0        5.00000   1         0     
330047    PointSource       26           0.01699   0.0        8.00000   1         0     
21        SimpleFaultSource 1            0.01653   0.0        9.00000   4         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
PointSource       1.61568   49    
SimpleFaultSource 0.51528   4     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00777 0.01509 0.00167 0.08656 55       
compute_hazard     0.11961 0.05401 0.03092 0.31442 20       
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== =================================================================================================== =========
task           sent                                                                                                received 
RtreeFilter    srcs=188.61 KB monitor=17.29 KB srcfilter=14.99 KB                                                  118.06 KB
compute_hazard sources_or_ruptures=116.44 KB param=62.4 KB rlzs_by_gsim=13.74 KB monitor=6.31 KB src_filter=4.8 KB 19.69 KB 
============== =================================================================================================== =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_hazard           2.39221  8.62891   20    
building ruptures              2.31520  7.96094   20    
total prefilter                0.42756  4.23828   55    
managing sources               0.38657  0.0       1     
reading composite source model 0.18598  0.0       1     
splitting sources              0.10374  0.0       1     
unpickling prefilter           0.01845  0.0       55    
saving ruptures                0.01770  0.0       20    
making contexts                0.01598  0.0       3     
store source_info              0.01518  0.0       1     
GmfGetter.init                 0.00655  0.05859   20    
unpickling compute_hazard      0.00591  0.0       20    
aggregating hcurves            0.00455  0.0       20    
reading site collection        0.00105  0.0       1     
============================== ======== ========= ======