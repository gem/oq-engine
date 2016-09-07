Germany_SHARE Combined Model event_based
========================================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48309.hdf5 updated Wed Sep  7 15:57:52 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

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
compute_ruptures_max_received_per_task 48,814      
compute_ruptures_num_tasks             10          
compute_ruptures_sent.gsims            3,170       
compute_ruptures_sent.monitor          9,210       
compute_ruptures_sent.sitecol          26,989      
compute_ruptures_sent.sources          3,083,360   
compute_ruptures_tot_received          164,962     
hazard.input_weight                    15,687      
hazard.n_imts                          1           
hazard.n_levels                        1           
hazard.n_realizations                  120         
hazard.n_sites                         100         
hazard.n_sources                       142         
hazard.output_weight                   3,600       
hostname                               gem-tstation
====================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
4            328       AreaSource   1,544  2,794     0.0         2.137      9.092         0.007         2,794    
4            327       AreaSource   1,544  2,795     0.0         2.010      8.990         0.005         2,795    
4            329       AreaSource   1,544  2,789     0.0         2.030      8.742         0.006         2,789    
4            318       AreaSource   449    0         0.002       0.0        4.329         4.329         1        
4            316       AreaSource   449    0         0.002       0.0        4.127         4.127         1        
4            317       AreaSource   449    0         0.002       0.0        4.056         4.056         1        
4            323       AreaSource   307    0         9.868E-04   0.0        2.811         2.811         1        
4            322       AreaSource   307    0         0.001       0.0        2.774         2.774         1        
4            264       AreaSource   85     0         9.081E-04   0.0        0.763         0.763         1        
4            265       AreaSource   85     0         9.189E-04   0.0        0.762         0.762         1        
4            263       AreaSource   85     0         9.081E-04   0.0        0.760         0.760         1        
4            332       AreaSource   56     0         9.389E-04   0.0        0.531         0.531         1        
4            330       AreaSource   56     0         9.780E-04   0.0        0.530         0.530         1        
4            331       AreaSource   56     0         9.420E-04   0.0        0.529         0.529         1        
4            267       AreaSource   56     0         8.140E-04   0.0        0.508         0.508         1        
4            266       AreaSource   56     0         8.152E-04   0.0        0.507         0.507         1        
4            334       AreaSource   39     0         9.348E-04   0.0        0.359         0.359         1        
4            333       AreaSource   39     0         9.489E-04   0.0        0.356         0.356         1        
4            248       AreaSource   30     0         9.069E-04   0.0        0.312         0.312         1        
4            249       AreaSource   30     0         8.900E-04   0.0        0.286         0.286         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
AreaSource        0.034       6.177      53            26            8,413     38    
PointSource       5.705E-04   0.0        0.232         0.232         36        36    
SimpleFaultSource 0.014       0.0        0.147         0.147         6         6     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   5.399 3.849  0.054 9.151 10       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         53        5.480     10    
reading composite source model 10        0.0       1     
managing sources               2.722     0.0       1     
store source_info              0.162     0.0       1     
filtering sources              0.153     0.0       139   
saving ruptures                0.011     0.0       10    
filtering ruptures             0.003     0.0       8     
reading site collection        4.549E-04 0.0       1     
============================== ========= ========= ======