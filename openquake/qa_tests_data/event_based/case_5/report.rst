Germany_SHARE Combined Model event_based
========================================

==================================================== ========================
tstation.gem.lan:/home/michele/oqdata/calc_5555.hdf5 Fri Sep 22 11:30:31 2017
checksum32                                           479,109,370             
engine_version                                       2.6.0-gite59d75a        
==================================================== ========================

num_sites = 100, num_imts = 1

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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(4,2,5,1) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(4,2,5,1) 20/20           
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(4,2,5,1) 1/1             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= ============================
grp_id gsims                                                                                            distances         siteparams              ruptparams                  
====== ================================================================================================ ================= ======================= ============================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
3      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc()                       rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor           
7      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
====== ================================================================================================ ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=11, rlzs=22)
  1,FaccioliEtAl2010(): [0]
  3,AkkarBommer2010(): [1 2 3 4 5]
  3,CauzziFaccioli2008(): [ 6  7  8  9 10]
  3,ChiouYoungs2008(): [11 12 13 14 15]
  3,ZhaoEtAl2006Asc(): [16 17 18 19 20]
  4,AkkarBommer2010(): [ 1  6 11 16]
  4,Campbell2003SHARE(): [ 5 10 15 20]
  4,CauzziFaccioli2008(): [ 2  7 12 17]
  4,ChiouYoungs2008(): [ 3  8 13 18]
  4,ToroEtAl2002SHARE(): [ 4  9 14 19]
  7,FaccioliEtAl2010(): [21]>

Number of ruptures per tectonic region type
-------------------------------------------
============================================= ====== ==================== =========== ============ ============
source_model                                  grp_id trt                  num_sources eff_ruptures tot_ruptures
============================================= ====== ==================== =========== ============ ============
source_models/as_model.xml                    1      Volcanic             2           84           84          
source_models/fs_bg_source_model.xml          3      Active Shallow Crust 4           1008         1,166       
source_models/fs_bg_source_model.xml          4      Stable Shallow Crust 43          214741       332,676     
source_models/ss_model_final_250km_Buffer.xml 7      Volcanic             36          640          640         
============================================= ====== ==================== =========== ============ ============

============= =======
#TRT models   4      
#sources      85     
#eff_ruptures 216,473
#tot_ruptures 334,566
#tot_weight   0      
============= =======

Informational data
------------------
========================= ===================================================================================
compute_ruptures.received tot 111.88 KB, max_per_task 33.53 KB                                               
compute_ruptures.sent     sources 3.12 MB, src_filter 30.48 KB, param 4.83 KB, monitor 2.86 KB, gsims 2.85 KB
hazard.input_weight       2146182.0999999987                                                                 
hazard.n_imts             1                                                                                  
hazard.n_levels           1                                                                                  
hazard.n_realizations     120                                                                                
hazard.n_sites            100                                                                                
hazard.n_sources          85                                                                                 
hazard.output_weight      30.0                                                                               
hostname                  tstation.gem.lan                                                                   
require_epsilons          False                                                                              
========================= ===================================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
4      338       AreaSource        574          0.0       17        0        
3      34        SimpleFaultSource 79           0.0       6         0        
4      246       AreaSource        564          0.0       14        0        
7      330055    PointSource       24           0.0       6         0        
7      330047    PointSource       26           0.0       8         0        
7      330057    PointSource       14           0.0       9         0        
4      20        SimpleFaultSource 31           0.0       9         0        
4      267       AreaSource        2,268        0.0       5         0        
4      23        SimpleFaultSource 59           0.0       1         0        
7      330050    PointSource       28           0.0       8         0        
7      330069    PointSource       12           0.0       12        0        
4      320       AreaSource        516          0.0       8         0        
7      330068    PointSource       18           0.0       5         0        
7      330048    PointSource       28           0.0       8         0        
4      331       AreaSource        2,256        0.0       1         0        
4      263       AreaSource        3,430        0.0       6         0        
4      333       AreaSource        1,572        0.0       7         0        
3      31        SimpleFaultSource 200          0.0       8         0        
1      1         AreaSource        42           0.0       8         0        
7      330065    PointSource       14           0.0       8         0        
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

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== === =========
operation-duration mean  stddev min   max num_tasks
compute_ruptures   5.863 4.730  0.052 11  9        
================== ===== ====== ===== === =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         52        9.000     9     
reading composite source model 9.981     0.0       1     
managing sources               6.138     0.0       1     
prefiltering source model      0.106     0.0       1     
store source_info              0.017     0.0       1     
saving ruptures                0.008     0.0       9     
setting event years            0.004     0.0       1     
filtering ruptures             0.002     0.0       8     
reading site collection        6.497E-04 0.0       1     
============================== ========= ========= ======