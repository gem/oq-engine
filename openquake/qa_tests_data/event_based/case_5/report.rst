Germany_SHARE Combined Model event_based
========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_81090.hdf5 Thu Jan 26 14:30:36 2017
engine_version                                 2.3.0-gite807292        
hazardlib_version                              0.23.0-gite1ea7ea       
============================================== ========================

num_sites = 100, sitecol = 5.21 KB

Parameters
----------
=============================== ==============================================================================================
calculation_mode                'event_based'                                                                                 
number_of_logic_tree_samples    0                                                                                             
maximum_distance                {'Active Shallow Crust': 80.0, 'Volcanic': 80.0, 'Stable Shallow Crust': 80.0, 'Shield': 80.0}
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
=============================== ==============================================================================================

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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(4,5,1,2) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(4,5,1,2) 5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(4,5,1,2) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rrup rhypo rjb rx vs30measured vs30 z1pt0 rake dip ztor mag
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
compute_ruptures_max_received_per_task    21,362      
compute_ruptures_num_tasks                19          
compute_ruptures_sent.gsims               6,931       
compute_ruptures_sent.monitor             19,114      
compute_ruptures_sent.sources             3,287,672   
compute_ruptures_sent.src_filter          50,502      
compute_ruptures_tot_received             145,772     
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
4      263       AreaSource        3,430        0.0       6         0        
4      319       AreaSource        516          0.0       8         0        
7      330056    PointSource       12           0.0       9         0        
7      330072    PointSource       14           0.0       9         0        
7      330046    PointSource       20           0.0       5         0        
7      330058    PointSource       14           0.0       8         0        
4      258       AreaSource        348          0.0       11        0        
4      315       AreaSource        476          0.0       34        0        
4      334       AreaSource        1,572        0.0       7         0        
7      330053    PointSource       28           0.0       6         0        
7      330054    PointSource       30           0.0       8         0        
4      329       AreaSource        61,740       0.0       100       0        
3      31        SimpleFaultSource 200          0.0       8         0        
4      331       AreaSource        2,256        0.0       1         0        
4      21        SimpleFaultSource 7            0.0       9         0        
4      338       AreaSource        574          0.0       17        0        
7      330051    PointSource       34           0.0       16        0        
4      320       AreaSource        516          0.0       8         0        
4      265       AreaSource        3,430        0.0       6         0        
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
compute_ruptures   2.782 1.877  0.009 5.175 19       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           52        3.777     19    
managing sources                 13        0.0       1     
split/filter heavy sources       13        0.0       1     
reading composite source model   9.978     0.0       1     
filtering composite source model 0.128     0.0       1     
saving ruptures                  0.010     0.0       19    
setting event years              0.004     0.0       1     
filtering ruptures               0.003     0.0       8     
store source_info                0.002     0.0       1     
reading site collection          5.786E-04 0.0       1     
================================ ========= ========= ======