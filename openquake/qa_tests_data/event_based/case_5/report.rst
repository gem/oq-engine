Germany_SHARE Combined Model event_based
========================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7631.hdf5 Wed Apr 26 15:56:31 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 100, sitecol = 6.03 KB

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
area_source_discretization      10.0             
ground_motion_correlation_model None             
random_seed                     42               
master_seed                     0                
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
========= ====== ================================================================================================ ================ ================
smlt_path weight source_model_file                                                                                gsim_logic_tree  num_realizations
========= ====== ================================================================================================ ================ ================
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(5,4,1,2) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(5,4,1,2) 5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(5,4,1,2) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    rake mag         
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rx rjb rhypo rrup vs30 vs30measured z1pt0 dip ztor rake mag
====== ================================================================================================ ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  1,FaccioliEtAl2010(): ['<0,b1~@_@_@_b4_1,w=0.7142857112446609>']
  4,AkkarBommer2010(): ['<1,b2~@_b2_1_@_@,w=0.057142857751067797>']
  4,Campbell2003SHARE(): ['<5,b2~@_b2_5_@_@,w=0.057142857751067797>']
  4,CauzziFaccioli2008(): ['<2,b2~@_b2_2_@_@,w=0.057142857751067797>']
  4,ChiouYoungs2008(): ['<3,b2~@_b2_3_@_@,w=0.057142857751067797>']
  4,ToroEtAl2002SHARE(): ['<4,b2~@_b2_4_@_@,w=0.057142857751067797>']>

Number of ruptures per tectonic region type
-------------------------------------------
==================================== ====== ==================== =========== ============ ============
source_model                         grp_id trt                  num_sources eff_ruptures tot_ruptures
==================================== ====== ==================== =========== ============ ============
source_models/as_model.xml           1      Volcanic             2           2            84          
source_models/fs_bg_source_model.xml 4      Stable Shallow Crust 43          3            332,676     
==================================== ====== ==================== =========== ============ ============

============= =======
#TRT models   2      
#sources      45     
#eff_ruptures 5      
#tot_ruptures 332,760
#tot_weight   34,282 
============= =======

Informational data
------------------
============================ ====================================================================================
compute_ruptures.received    tot 127.94 KB, max_per_task 20.02 KB                                                
compute_ruptures.sent        sources 3.14 MB, src_filter 64.35 KB, monitor 14.73 KB, gsims 6.77 KB, param 1.21 KB
hazard.input_weight          34,282                                                                              
hazard.n_imts                1 B                                                                                 
hazard.n_levels              1 B                                                                                 
hazard.n_realizations        120 B                                                                               
hazard.n_sites               100 B                                                                               
hazard.n_sources             85 B                                                                                
hazard.output_weight         3,600                                                                               
hostname                     tstation.gem.lan                                                                    
require_epsilons             0 B                                                                                 
============================ ====================================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
7      330056    PointSource       12           0.0       9         0        
7      330054    PointSource       30           0.0       8         0        
7      330050    PointSource       28           0.0       8         0        
4      263       AreaSource        3,430        0.0       6         0        
4      259       AreaSource        348          0.0       11        0        
4      322       AreaSource        12,288       0.0       5         0        
4      256       AreaSource        11,064       0.0       10        0        
7      330078    PointSource       12           0.0       12        0        
4      340       AreaSource        574          0.0       17        0        
4      19        SimpleFaultSource 349          0.0       9         0        
4      266       AreaSource        2,268        0.0       6         0        
7      330080    PointSource       12           0.0       9         0        
4      316       AreaSource        17,964       0.0       40        0        
4      320       AreaSource        516          0.0       8         0        
4      318       AreaSource        17,964       0.0       40        0        
7      330047    PointSource       26           0.0       8         0        
7      330057    PointSource       14           0.0       9         0        
1      1         AreaSource        42           0.0       8         0        
4      333       AreaSource        1,572        0.0       7         0        
7      330064    PointSource       14           0.0       9         0        
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.0       41    
PointSource       0.0       36    
SimpleFaultSource 0.0       8     
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   2.654 1.785  0.010 4.918 19       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           50        3.344     19    
reading composite source model   9.515     0.0       1     
filtering composite source model 0.124     0.0       1     
saving ruptures                  0.007     0.0       19    
setting event years              0.004     0.0       1     
filtering ruptures               0.002     0.0       8     
store source_info                0.002     0.0       1     
reading site collection          6.366E-04 0.0       1     
managing sources                 1.044E-04 0.0       1     
================================ ========= ========= ======