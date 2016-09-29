Germany_SHARE Combined Model event_based
========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54435.hdf5 Tue Sep 27 14:08:00 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
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
==================================== ====== ==================== =========== ============ ======
source_model                         grp_id trt                  num_sources eff_ruptures weight
==================================== ====== ==================== =========== ============ ======
source_models/as_model.xml           1      Volcanic             2           2            2.100 
source_models/fs_bg_source_model.xml 4      Stable Shallow Crust 49          3            11,487
==================================== ====== ==================== =========== ============ ======

=============== ======
#TRT models     2     
#sources        51    
#eff_ruptures   5     
filtered_weight 11,489
=============== ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 32,787      
compute_ruptures_num_tasks             26          
compute_ruptures_sent.gsims            8,106       
compute_ruptures_sent.monitor          26,936      
compute_ruptures_sent.sitecol          68,510      
compute_ruptures_sent.sources          6,077,241   
compute_ruptures_tot_received          192,972     
hazard.input_weight                    15,687      
hazard.n_imts                          1           
hazard.n_levels                        1           
hazard.n_realizations                  120         
hazard.n_sites                         100         
hazard.n_sources                       142         
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
====== ========= ================= ====== ========= =========
grp_id source_id source_class      weight calc_time num_sites
====== ========= ================= ====== ========= =========
7      330054    PointSource       0.750  0.0       0        
3      279       SimpleFaultSource 17     0.0       0        
3      27        SimpleFaultSource 158    0.0       0        
4      321       AreaSource        12     0.0       0        
4      20        SimpleFaultSource 31     0.0       0        
4      251       AreaSource        27     0.0       0        
3      33        SimpleFaultSource 147    0.0       0        
3      426       SimpleFaultSource 21     0.0       0        
4      249       AreaSource        30     0.0       0        
7      330045    PointSource       0.550  0.0       0        
7      330064    PointSource       0.350  0.0       0        
3      29        SimpleFaultSource 80     0.0       0        
7      330051    PointSource       0.850  0.0       0        
3      111       SimpleFaultSource 32     0.0       0        
4      322       AreaSource        307    0.0       0        
4      330       AreaSource        56     0.0       0        
7      330046    PointSource       0.500  0.0       0        
1      2         AreaSource        1.050  0.0       0        
3      94        SimpleFaultSource 44     0.0       0        
3      423       SimpleFaultSource 44     0.0       0        
====== ========= ================= ====== ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.0       51    
PointSource       0.0       51    
SimpleFaultSource 0.0       40    
================= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   2.155 2.725  0.001 8.390 26       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         56        4.582     26    
reading composite source model 9.909     0.0       1     
managing sources               5.308     0.0       1     
filter/split heavy sources     5.271     0.0       1     
saving ruptures                0.024     0.0       26    
store source_info              0.003     0.0       1     
filtering ruptures             0.003     0.0       8     
reading site collection        5.701E-04 0.0       1     
============================== ========= ========= ======