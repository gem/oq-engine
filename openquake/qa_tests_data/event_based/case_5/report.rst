Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,360,147,003      
date           2018-06-05T06:40:05
engine_version 3.2.0-git65c4735   
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
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
19        SimpleFaultSource 349          0.21696   1.974E-04  9.00000   12        0     
1339      AreaSource        168          0.11187   0.00385    7.75000   12        0     
246       AreaSource        156          0.07724   0.00453    4.46154   13        2     
247       AreaSource        156          0.07357   0.00439    4.46154   13        0     
264       AreaSource        1,022        0.05288   0.02338    1.22222   9         9     
263       AreaSource        1,022        0.05278   0.02313    1.22222   9         9     
257       AreaSource        96           0.04780   0.00413    5.87500   8         5     
258       AreaSource        96           0.04240   0.00328    5.87500   8         8     
249       AreaSource        384          0.04129   0.01214    2.00000   7         0     
248       AreaSource        384          0.04072   0.01222    2.00000   7         0     
250       AreaSource        384          0.04040   0.01230    1.85714   7         0     
259       AreaSource        96           0.03999   0.00314    5.87500   8         8     
20        SimpleFaultSource 31           0.02698   7.963E-05  9.00000   6         0     
330045    PointSource       22           0.02336   1.907E-06  7.00000   1         0     
22        SimpleFaultSource 34           0.02284   7.367E-05  1.00000   6         0     
330046    PointSource       20           0.01831   1.192E-06  5.00000   1         0     
330047    PointSource       26           0.01781   1.192E-06  8.00000   1         0     
330051    PointSource       34           0.01676   1.431E-06  16        1         0     
330048    PointSource       28           0.01477   1.431E-06  8.00000   1         0     
330054    PointSource       30           0.01467   1.431E-06  8.00000   1         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.63780   13    
PointSource       0.32695   51    
SimpleFaultSource 0.27674   4     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00735 0.01286 0.00163 0.07611 55       
compute_ruptures   0.16470 0.15707 0.02663 0.46662 8        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ =============================================================================== =========
task             sent                                                                            received 
RtreeFilter      srcs=188.61 KB monitor=18.58 KB srcfilter=14.99 KB                              118.06 KB
compute_ruptures sources=108.21 KB param=4.5 KB gsims=3.04 KB monitor=2.76 KB src_filter=1.82 KB 16.61 KB 
================ =============================================================================== =========

Slowest operations
------------------
=============================== ======== ========= ======
operation                       time_sec memory_mb counts
=============================== ======== ========= ======
EventBasedRuptureCalculator.run 1.39537  0.0       1     
total compute_ruptures          1.31761  8.29297   8     
managing sources                0.87829  0.0       1     
total prefilter                 0.40405  4.14062   55    
reading composite source model  0.19622  0.0       1     
splitting sources               0.11000  0.0       1     
unpickling prefilter            0.02270  0.0       55    
store source_info               0.01371  0.0       1     
saving ruptures                 0.01201  0.0       8     
making contexts                 0.00355  0.0       3     
unpickling compute_ruptures     0.00275  0.0       8     
setting event years             0.00222  0.0       1     
reading site collection         0.00193  0.0       1     
=============================== ======== ========= ======