Germany_SHARE Combined Model event_based
========================================

gem-tstation:/home/michele/ssd/calc_45871.hdf5 updated Wed Aug 31 12:12:24 2016

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
engine_version               '2.1.0-git49748af'                                                                                
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
source_models/fs_bg_source_model.xml 4      Stable Shallow Crust 39          3            7,896 
==================================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        41   
#eff_ruptures   5    
filtered_weight 7,898
=============== =====

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 48,716      
compute_ruptures_num_tasks             10          
compute_ruptures_sent.monitor          8,790       
compute_ruptures_sent.rlzs_by_gsim     30,830      
compute_ruptures_sent.sitecol          26,989      
compute_ruptures_sent.sources          3,084,032   
compute_ruptures_tot_received          164,157     
hazard.input_weight                    15,687      
hazard.n_imts                          1           
hazard.n_levels                        1.000       
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
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
4            327       AreaSource   1,544  2,795     0.0         2.088      9.570         0.006         2,795    
4            329       AreaSource   1,544  2,789     0.0         2.080      9.562         0.006         2,789    
4            328       AreaSource   1,544  2,794     0.0         1.933      9.406         0.005         2,794    
4            318       AreaSource   449    0         0.002       0.0        4.510         4.510         1        
4            316       AreaSource   449    0         0.002       0.0        4.337         4.337         1        
4            317       AreaSource   449    0         0.002       0.0        4.198         4.198         1        
4            323       AreaSource   307    0         9.670E-04   0.0        3.051         3.051         1        
4            322       AreaSource   307    0         9.830E-04   0.0        2.968         2.968         1        
4            264       AreaSource   85     0         9.501E-04   0.0        0.799         0.799         1        
4            263       AreaSource   85     0         9.069E-04   0.0        0.795         0.795         1        
4            265       AreaSource   85     0         8.819E-04   0.0        0.793         0.793         1        
4            332       AreaSource   56     0         9.091E-04   0.0        0.554         0.554         1        
4            331       AreaSource   56     0         9.110E-04   0.0        0.554         0.554         1        
4            330       AreaSource   56     0         9.470E-04   0.0        0.553         0.553         1        
4            266       AreaSource   56     0         8.271E-04   0.0        0.534         0.534         1        
4            267       AreaSource   56     0         7.889E-04   0.0        0.532         0.532         1        
4            334       AreaSource   39     0         9.091E-04   0.0        0.399         0.399         1        
4            333       AreaSource   39     0         9.220E-04   0.0        0.375         0.375         1        
4            248       AreaSource   30     0         8.900E-04   0.0        0.374         0.374         1        
4            249       AreaSource   30     0         8.540E-04   0.0        0.331         0.331         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
AreaSource        0.033       6.101      56            28            8,413     38    
PointSource       4.704E-04   0.0        0.240         0.240         36        36    
SimpleFaultSource 0.013       0.0        0.140         0.140         6         6     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  5.720 4.078  0.057 9.629 10       
compute_ruptures.memory_mb 1.542 2.520  0.0   5.863 10       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         57        5.863     10    
reading composite source model 9.994     0.0       1     
managing sources               2.680     0.0       1     
store source_info              0.155     0.0       1     
filtering sources              0.126     0.0       139   
aggregate curves               0.005     0.0       10    
saving ruptures                0.004     0.0       1     
filtering ruptures             0.003     0.0       8     
reading site collection        6.862E-04 0.0       1     
============================== ========= ========= ======