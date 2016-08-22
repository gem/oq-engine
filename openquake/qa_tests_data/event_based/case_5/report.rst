Germany_SHARE Combined Model event_based
========================================

gem-tstation:/home/michele/ssd/calc_40595.hdf5 updated Mon Aug 22 12:33:53 2016

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
engine_version               '2.1.0-git8cbb23e'                                                                                
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
1      ['FaccioliEtAl2010()']                                                                           set(['rrup'])     set(['vs30'])           rake mag         
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
compute_ruptures_max_received_per_task 40,475      
compute_ruptures_num_tasks             12          
compute_ruptures_sent.monitor          61,488      
compute_ruptures_sent.rlzs_by_gsim     37,614      
compute_ruptures_sent.sitecol          29,064      
compute_ruptures_sent.sources          5,175,656   
compute_ruptures_tot_received          224,362     
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
4            327       AreaSource   1,544  5,145     0.003       1.543      9.161         0.006         2,795    
4            328       AreaSource   1,544  5,145     0.003       1.515      9.005         0.014         2,794    
4            329       AreaSource   1,544  5,145     0.003       1.546      8.711         0.004         2,789    
4            318       AreaSource   449    1         0.002       0.0        4.376         4.376         1        
4            317       AreaSource   449    1         0.002       0.0        4.207         4.207         1        
4            316       AreaSource   449    1         0.002       0.0        4.201         4.201         1        
4            322       AreaSource   307    1         9.840E-04   0.0        3.005         3.005         1        
4            323       AreaSource   307    1         9.701E-04   0.0        2.959         2.959         1        
4            263       AreaSource   85     1         9.151E-04   0.0        0.765         0.765         1        
4            265       AreaSource   85     1         8.860E-04   0.0        0.760         0.760         1        
4            264       AreaSource   85     1         8.881E-04   0.0        0.759         0.759         1        
4            332       AreaSource   56     1         9.170E-04   0.0        0.533         0.533         1        
4            330       AreaSource   56     1         9.470E-04   0.0        0.532         0.532         1        
4            331       AreaSource   56     1         9.129E-04   0.0        0.531         0.531         1        
4            266       AreaSource   56     1         7.889E-04   0.0        0.511         0.511         1        
4            267       AreaSource   56     1         7.920E-04   0.0        0.511         0.511         1        
4            334       AreaSource   39     1         8.969E-04   0.0        0.360         0.360         1        
4            333       AreaSource   39     1         9.391E-04   0.0        0.359         0.359         1        
4            248       AreaSource   30     1         8.862E-04   0.0        0.313         0.313         1        
4            249       AreaSource   30     1         8.500E-04   0.0        0.287         0.287         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================= =========== ========== ============= ============= ========= ======
source_class      filter_time split_time cum_calc_time max_calc_time num_tasks counts
================= =========== ========== ============= ============= ========= ======
AreaSource        0.042       4.604      54            27            8,413     38    
PointSource       4.487E-04   0.0        0.234         0.234         36        36    
SimpleFaultSource 0.013       0.0        0.135         0.135         6         6     
================= =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  4.579 2.920  0.054 8.580 12       
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   12       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         54        0.0       12    
reading composite source model 9.576     0.0       1     
managing sources               5.239     0.0       1     
splitting sources              4.604     0.0       3     
store source_info              0.148     0.0       1     
filtering sources              0.132     0.0       142   
saving ruptures                0.005     0.0       1     
aggregate curves               0.005     0.0       12    
filtering ruptures             0.003     0.0       8     
reading site collection        3.200E-04 0.0       1     
============================== ========= ========= ======