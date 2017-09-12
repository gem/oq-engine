Germany_SHARE Combined Model event_based
========================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_14495.hdf5 Thu Aug 17 11:48:59 2017
checksum32                                       479,109,370             
engine_version                                   2.6.0-gitbdd9d17        
================================================ ========================

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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(2,1,4,5) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(2,1,4,5) 20/20           
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(2,1,4,5) 1/1             
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
============================ ===================================================================================
compute_ruptures.received    tot 111.7 KB, max_per_task 33.53 KB                                                
compute_ruptures.sent        sources 3.12 MB, src_filter 30.48 KB, param 4.83 KB, gsims 2.85 KB, monitor 2.82 KB
hazard.input_weight          2146182.0999999987                                                                 
hazard.n_imts                1                                                                                  
hazard.n_levels              1                                                                                  
hazard.n_realizations        120                                                                                
hazard.n_sites               100                                                                                
hazard.n_sources             85                                                                                 
hazard.output_weight         30.0                                                                               
hostname                     tstation.gem.lan                                                                   
require_epsilons             False                                                                              
============================ ===================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
4      330       AreaSource   2,256        0.0       1         0        
4      264       AreaSource   3,430        0.0       6         0        
7      330052    PointSource  22           0.0       5         0        
4      329       AreaSource   61,740       0.0       100       0        
7      330078    PointSource  12           0.0       12        0        
4      316       AreaSource   17,964       0.0       40        0        
7      330049    PointSource  22           0.0       5         0        
7      330068    PointSource  18           0.0       5         0        
7      330051    PointSource  34           0.0       16        0        
4      267       AreaSource   2,268        0.0       5         0        
7      330046    PointSource  20           0.0       5         0        
7      330061    PointSource  18           0.0       5         0        
4      332       AreaSource   2,256        0.0       1         0        
4      256       AreaSource   11,064       0.0       10        0        
4      334       AreaSource   1,572        0.0       7         0        
4      331       AreaSource   2,256        0.0       1         0        
4      246       AreaSource   564          0.0       14        0        
7      330060    PointSource  16           0.0       5         0        
7      330058    PointSource  14           0.0       8         0        
4      327       AreaSource   61,740       0.0       100       0        
====== ========= ============ ============ ========= ========= =========

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
compute_ruptures   5.718 4.610  0.060 11  9        
================== ===== ====== ===== === =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         51        7.910     9     
reading composite source model 9.676     0.0       1     
managing sources               6.037     0.0       1     
prefiltering source model      0.105     0.0       1     
store source_info              0.016     0.0       1     
saving ruptures                0.008     0.0       9     
setting event years            0.004     0.0       1     
filtering ruptures             0.003     0.0       8     
reading site collection        4.973E-04 0.0       1     
============================== ========= ========= ======