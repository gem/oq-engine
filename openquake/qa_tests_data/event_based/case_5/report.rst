Germany_SHARE Combined Model event_based
========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_80584.hdf5 Thu Jan 26 05:26:37 2017
engine_version                                 2.3.0-gitd31dc69        
hazardlib_version                              0.23.0-git4d14bee       
============================================== ========================

num_sites = 100, sitecol = 5.21 KB

Parameters
----------
=============================== ==============================================================================================
calculation_mode                'event_based'                                                                                 
number_of_logic_tree_samples    0                                                                                             
maximum_distance                {'Shield': 80.0, 'Active Shallow Crust': 80.0, 'Volcanic': 80.0, 'Stable Shallow Crust': 80.0}
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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       complex(5,2,1,4) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   complex(5,2,1,4) 5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ complex(5,2,1,4) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    rake mag         
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rrup rhypo rx rjb z1pt0 vs30 vs30measured dip rake mag ztor
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
4      331       AreaSource        2,256        0.0       1         0        
4      247       AreaSource        564          0.0       13        0        
4      254       AreaSource        11,064       0.0       10        0        
4      246       AreaSource        564          0.0       14        0        
4      255       AreaSource        11,064       0.0       10        0        
4      258       AreaSource        348          0.0       11        0        
7      330052    PointSource       22           0.0       5         0        
4      314       AreaSource        476          0.0       34        0        
7      330077    PointSource       20           0.0       5         0        
4      250       AreaSource        1,236        0.0       8         0        
3      31        SimpleFaultSource 200          0.0       8         0        
4      323       AreaSource        12,288       0.0       5         0        
4      320       AreaSource        516          0.0       8         0        
4      256       AreaSource        11,064       0.0       10        0        
7      330047    PointSource       26           0.0       8         0        
7      330071    PointSource       12           0.0       9         0        
4      266       AreaSource        2,268        0.0       6         0        
4      329       AreaSource        61,740       0.0       100       0        
3      733       AreaSource        729          0.0       5         0        
7      330074    PointSource       14           0.0       6         0        
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
compute_ruptures   2.700 1.813  0.010 5.052 19       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           51        3.582     19    
managing sources                 13        0.0       1     
split/filter heavy sources       13        0.0       1     
reading composite source model   9.689     0.0       1     
filtering composite source model 0.125     0.0       1     
saving ruptures                  0.005     0.0       19    
setting event years              0.004     0.0       1     
filtering ruptures               0.003     0.0       8     
store source_info                0.002     0.0       1     
reading site collection          6.008E-04 0.0       1     
================================ ========= ========= ======