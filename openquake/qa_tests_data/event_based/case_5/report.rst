Germany_SHARE Combined Model event_based
========================================

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85590.hdf5 Tue Feb 14 15:48:58 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

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
random_seed                     23               
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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(1,4,5,2) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(1,4,5,2) 5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(1,4,5,2) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rrup rjb rx rhypo vs30 z1pt0 vs30measured mag dip rake ztor
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
========================================= ============
compute_ruptures_max_received_per_task    21,354      
compute_ruptures_num_tasks                19          
compute_ruptures_sent.gsims               6,931       
compute_ruptures_sent.monitor             18,962      
compute_ruptures_sent.sources             3,287,636   
compute_ruptures_sent.src_filter          66,386      
compute_ruptures_tot_received             145,626     
hazard.input_weight                       34,282      
hazard.n_imts                             1           
hazard.n_levels                           1           
hazard.n_realizations                     120         
hazard.n_sites                            100         
hazard.n_sources                          85          
hazard.output_weight                      3,600       
hostname                                  gem-tstation
require_epsilons                          False       
========================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 5    
Total number of events   5    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
4      247       AreaSource        564          0.0       13        0        
4      267       AreaSource        2,268        0.0       5         0        
7      330061    PointSource       18           0.0       5         0        
1      2         AreaSource        42           0.0       8         0        
7      330073    PointSource       14           0.0       8         0        
4      340       AreaSource        574          0.0       17        0        
4      333       AreaSource        1,572        0.0       7         0        
7      330064    PointSource       14           0.0       9         0        
7      330069    PointSource       12           0.0       12        0        
7      330045    PointSource       22           0.0       7         0        
4      246       AreaSource        564          0.0       14        0        
4      331       AreaSource        2,256        0.0       1         0        
4      248       AreaSource        1,236        0.0       8         0        
4      22        SimpleFaultSource 34           0.0       1         0        
7      330053    PointSource       28           0.0       6         0        
4      21        SimpleFaultSource 7            0.0       9         0        
4      316       AreaSource        17,964       0.0       40        0        
7      330067    PointSource       16           0.0       5         0        
7      330070    PointSource       12           0.0       10        0        
4      263       AreaSource        3,430        0.0       6         0        
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
compute_ruptures   2.761 1.864  0.010 5.160 19       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           52        0.770     19    
managing sources                 13        0.0       1     
reading composite source model   10        0.0       1     
filtering composite source model 0.126     0.0       1     
saving ruptures                  0.005     0.0       19    
setting event years              0.004     0.0       1     
filtering ruptures               0.003     0.0       8     
store source_info                0.002     0.0       1     
reading site collection          6.242E-04 0.0       1     
================================ ========= ========= ======