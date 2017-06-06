Germany_SHARE Combined Model event_based
========================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_26096.hdf5 Tue Jun  6 14:59:25 2017
engine_version                                   2.5.0-gitb270b98        
hazardlib_version                                0.25.0-git6276f16       
================================================ ========================

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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(2,5,1,4) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(2,5,1,4) 20/20           
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(2,5,1,4) 1/1             
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
  1,FaccioliEtAl2010(): ['<0,b1~@_@_@_b4_1,w=0.4999999925494195>']
  3,AkkarBommer2010(): ['<1,b2~b1_1_b2_1_@_@,w=0.014000000000000002>', '<2,b2~b1_1_b2_2_@_@,w=0.014000000000000002>', '<3,b2~b1_1_b2_3_@_@,w=0.014000000000000002>', '<4,b2~b1_1_b2_4_@_@,w=0.014000000000000002>', '<5,b2~b1_1_b2_5_@_@,w=0.014000000000000002>']
  3,CauzziFaccioli2008(): ['<6,b2~b1_2_b2_1_@_@,w=0.014000000000000002>', '<7,b2~b1_2_b2_2_@_@,w=0.014000000000000002>', '<8,b2~b1_2_b2_3_@_@,w=0.014000000000000002>', '<9,b2~b1_2_b2_4_@_@,w=0.014000000000000002>', '<10,b2~b1_2_b2_5_@_@,w=0.014000000000000002>']
  3,ChiouYoungs2008(): ['<11,b2~b1_3_b2_1_@_@,w=0.008>', '<12,b2~b1_3_b2_2_@_@,w=0.008>', '<13,b2~b1_3_b2_3_@_@,w=0.008>', '<14,b2~b1_3_b2_4_@_@,w=0.008>', '<15,b2~b1_3_b2_5_@_@,w=0.008>']
  3,ZhaoEtAl2006Asc(): ['<16,b2~b1_4_b2_1_@_@,w=0.004>', '<17,b2~b1_4_b2_2_@_@,w=0.004>', '<18,b2~b1_4_b2_3_@_@,w=0.004>', '<19,b2~b1_4_b2_4_@_@,w=0.004>', '<20,b2~b1_4_b2_5_@_@,w=0.004>']
  4,AkkarBommer2010(): ['<1,b2~b1_1_b2_1_@_@,w=0.014000000000000002>', '<6,b2~b1_2_b2_1_@_@,w=0.014000000000000002>', '<11,b2~b1_3_b2_1_@_@,w=0.008>', '<16,b2~b1_4_b2_1_@_@,w=0.004>']
  4,Campbell2003SHARE(): ['<5,b2~b1_1_b2_5_@_@,w=0.014000000000000002>', '<10,b2~b1_2_b2_5_@_@,w=0.014000000000000002>', '<15,b2~b1_3_b2_5_@_@,w=0.008>', '<20,b2~b1_4_b2_5_@_@,w=0.004>']
  4,CauzziFaccioli2008(): ['<2,b2~b1_1_b2_2_@_@,w=0.014000000000000002>', '<7,b2~b1_2_b2_2_@_@,w=0.014000000000000002>', '<12,b2~b1_3_b2_2_@_@,w=0.008>', '<17,b2~b1_4_b2_2_@_@,w=0.004>']
  4,ChiouYoungs2008(): ['<3,b2~b1_1_b2_3_@_@,w=0.014000000000000002>', '<8,b2~b1_2_b2_3_@_@,w=0.014000000000000002>', '<13,b2~b1_3_b2_3_@_@,w=0.008>', '<18,b2~b1_4_b2_3_@_@,w=0.004>']
  4,ToroEtAl2002SHARE(): ['<4,b2~b1_1_b2_4_@_@,w=0.014000000000000002>', '<9,b2~b1_2_b2_4_@_@,w=0.014000000000000002>', '<14,b2~b1_3_b2_4_@_@,w=0.008>', '<19,b2~b1_4_b2_4_@_@,w=0.004>']
  7,FaccioliEtAl2010(): ['<21,b3~@_@_@_b4_1,w=0.3000000074505805>']>

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
============================ ====================================================================================
compute_ruptures.received    tot 119.3 KB, max_per_task 19.54 KB                                                 
compute_ruptures.sent        sources 3.14 MB, src_filter 64.35 KB, param 10.19 KB, gsims 6.77 KB, monitor 5.77 KB
hazard.input_weight          34,282                                                                              
hazard.n_imts                1 B                                                                                 
hazard.n_levels              1 B                                                                                 
hazard.n_realizations        120 B                                                                               
hazard.n_sites               100 B                                                                               
hazard.n_sources             85 B                                                                                
hazard.output_weight         30                                                                                  
hostname                     tstation.gem.lan                                                                    
require_epsilons             0 B                                                                                 
============================ ====================================================================================

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
4      247       AreaSource        564          0.0       13        0        
4      317       AreaSource        17,964       0.0       40        0        
7      330054    PointSource       30           0.0       8         0        
7      330059    PointSource       14           0.0       6         0        
4      257       AreaSource        348          0.0       11        0        
7      330070    PointSource       12           0.0       10        0        
4      329       AreaSource        61,740       0.0       100       0        
4      338       AreaSource        574          0.0       17        0        
4      321       AreaSource        516          0.0       8         0        
7      330047    PointSource       26           0.0       8         0        
7      330055    PointSource       24           0.0       6         0        
4      254       AreaSource        11,064       0.0       10        0        
7      330071    PointSource       12           0.0       9         0        
4      323       AreaSource        12,288       0.0       5         0        
7      330064    PointSource       14           0.0       9         0        
4      20        SimpleFaultSource 31           0.0       9         0        
7      330052    PointSource       22           0.0       5         0        
4      333       AreaSource        1,572        0.0       7         0        
4      266       AreaSource        2,268        0.0       6         0        
3      30        SimpleFaultSource 158          0.0       1         0        
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
compute_ruptures   2.801 1.904  0.010 5.387 19       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         53        4.336     19    
reading composite source model 10        0.0       1     
managing sources               6.381     0.0       1     
prefiltering source model      0.112     0.0       1     
store source_info              0.016     0.0       1     
saving ruptures                0.007     0.0       19    
setting event years            0.004     0.0       1     
filtering ruptures             0.003     0.0       8     
reading site collection        6.180E-04 0.0       1     
============================== ========= ========= ======