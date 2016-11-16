Germany_SHARE Combined Model event_based
========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_67008.hdf5 Wed Nov  9 08:16:39 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 100, sitecol = 5.19 KB

Parameters
----------
============================ ==================================================================================================
calculation_mode             'event_based'                                                                                     
number_of_logic_tree_samples 0                                                                                                 
maximum_distance             {u'Volcanic': 80.0, u'Stable Shallow Crust': 80.0, u'Shield': 80.0, u'Active Shallow Crust': 80.0}
investigation_time           30.0                                                                                              
ses_per_logic_tree_path      1                                                                                                 
truncation_level             3.0                                                                                               
rupture_mesh_spacing         5.0                                                                                               
complex_fault_mesh_spacing   5.0                                                                                               
width_of_mfd_bin             0.1                                                                                               
area_source_discretization   10.0                                                                                              
random_seed                  23                                                                                                
master_seed                  0                                                                                                 
============================ ==================================================================================================

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
1      FaccioliEtAl2010()                                                                               rrup              vs30                    rake mag         
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rx rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ================================================================================================ ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  1,FaccioliEtAl2010(): ['<0,b1~@_@_@_b4_1,w=0.714285711245>']
  4,AkkarBommer2010(): ['<1,b2~@_b2_1_@_@,w=0.0571428577511>']
  4,Campbell2003SHARE(): ['<5,b2~@_b2_5_@_@,w=0.0571428577511>']
  4,CauzziFaccioli2008(): ['<2,b2~@_b2_2_@_@,w=0.0571428577511>']
  4,ChiouYoungs2008(): ['<3,b2~@_b2_3_@_@,w=0.0571428577511>']
  4,ToroEtAl2002SHARE(): ['<4,b2~@_b2_4_@_@,w=0.0571428577511>']>

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
====================================== ============
compute_ruptures_max_received_per_task 27,224      
compute_ruptures_num_tasks             19          
compute_ruptures_sent.gsims            6,626       
compute_ruptures_sent.monitor          19,627      
compute_ruptures_sent.sitecol          51,652      
compute_ruptures_sent.sources          3,510,048   
compute_ruptures_tot_received          176,264     
hazard.input_weight                    34,282      
hazard.n_imts                          1           
hazard.n_levels                        1           
hazard.n_realizations                  120         
hazard.n_sites                         100         
hazard.n_sources                       85          
hazard.output_weight                   3,600       
hostname                               gem-tstation
====================================== ============

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
7      330054    PointSource       30           0.0       8         0        
4      249       AreaSource        1,236        0.0       8         0        
7      330074    PointSource       14           0.0       6         0        
4      321       AreaSource        516          0.0       8         0        
4      313       AreaSource        476          0.0       34        0        
4      258       AreaSource        348          0.0       11        0        
1      1         AreaSource        42           0.0       8         0        
4      20        SimpleFaultSource 31           0.0       9         0        
7      330050    PointSource       28           0.0       8         0        
7      330077    PointSource       20           0.0       5         0        
4      263       AreaSource        3,430        0.0       6         0        
7      330065    PointSource       14           0.0       8         0        
4      317       AreaSource        17,964       0.0       40        0        
7      330047    PointSource       26           0.0       8         0        
4      255       AreaSource        11,064       0.0       10        0        
4      267       AreaSource        2,268        0.0       5         0        
7      330068    PointSource       18           0.0       5         0        
7      330055    PointSource       24           0.0       6         0        
4      248       AreaSource        1,236        0.0       8         0        
3      34        SimpleFaultSource 79           0.0       6         0        
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
compute_ruptures   2.654 1.760  0.009 4.726 19       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           50        1.988     19    
managing sources                 12        0.0       1     
split/filter heavy sources       12        0.0       1     
reading composite source model   9.241     0.0       1     
filtering composite source model 0.117     0.0       1     
saving ruptures                  0.012     0.0       19    
filtering ruptures               0.003     0.0       8     
store source_info                0.002     0.0       1     
reading site collection          4.308E-04 0.0       1     
================================ ========= ========= ======