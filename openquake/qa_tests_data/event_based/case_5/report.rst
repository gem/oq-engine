Germany_SHARE Combined Model event_based
========================================

gem-tstation:/home/michele/ssd/calc_22618.hdf5 updated Tue May 31 15:39:10 2016

num_sites = 100, sitecol = 5.19 KB

Parameters
----------
============================ ==============================================================================================
calculation_mode             'event_based'                                                                                 
number_of_logic_tree_samples 0                                                                                             
maximum_distance             {'Volcanic': 80.0, 'Stable Shallow Crust': 80.0, 'Shield': 80.0, 'Active Shallow Crust': 80.0}
investigation_time           30.0                                                                                          
ses_per_logic_tree_path      1                                                                                             
truncation_level             3.0                                                                                           
rupture_mesh_spacing         5.0                                                                                           
complex_fault_mesh_spacing   5.0                                                                                           
width_of_mfd_bin             0.1                                                                                           
area_source_discretization   10.0                                                                                          
random_seed                  23                                                                                            
master_seed                  0                                                                                             
engine_version               '2.0.0-git4fb4450'                                                                            
============================ ==============================================================================================

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
======== ============
hostname gem-tstation
======== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 5    
Total number of events   5    
Rupture multiplicity     1.000
======================== =====

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
4            327       AreaSource   1,544  5,145     0.003       1.720      9.144    
4            329       AreaSource   1,544  5,145     0.003       1.543      9.107    
4            328       AreaSource   1,544  5,145     0.003       1.613      8.934    
4            316       AreaSource   449    1         0.002       0.0        4.111    
4            318       AreaSource   449    1         0.002       0.0        4.070    
4            317       AreaSource   449    1         0.002       0.0        4.063    
4            322       AreaSource   307    1         0.001       0.0        3.169    
4            323       AreaSource   307    1         0.001       0.0        2.854    
4            265       AreaSource   85     1         9.060E-04   0.0        0.800    
4            263       AreaSource   85     1         9.091E-04   0.0        0.796    
4            264       AreaSource   85     1         9.811E-04   0.0        0.766    
4            333       AreaSource   39     1         9.720E-04   0.0        0.556    
4            332       AreaSource   56     1         0.001       0.0        0.521    
4            266       AreaSource   56     1         8.042E-04   0.0        0.514    
4            331       AreaSource   56     1         9.859E-04   0.0        0.513    
4            330       AreaSource   56     1         9.639E-04   0.0        0.513    
4            267       AreaSource   56     1         8.080E-04   0.0        0.508    
4            334       AreaSource   39     1         9.191E-04   0.0        0.381    
4            248       AreaSource   30     1         9.730E-04   0.0        0.364    
4            249       AreaSource   30     1         9.031E-04   0.0        0.319    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
================= =========== ========== ========= ======
source_class      filter_time split_time calc_time counts
================= =========== ========== ========= ======
AreaSource        0.044       4.876      54        38    
PointSource       5.014E-04   0.0        0.336     36    
SimpleFaultSource 0.014       0.0        0.132     6     
================= =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         2.630 1.471  0.027 4.634 21       
compute_ruptures.memory_mb        0.0   0.0    0.0   0.0   21       
compute_gmfs_and_curves.time_sec  0.006 0.004  0.002 0.012 5        
compute_gmfs_and_curves.memory_mb 0.0   0.0    0.0   0.0   5        
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         55        0.0       21    
reading composite source model 10        0.0       1     
managing sources               5.499     0.0       1     
splitting sources              4.876     0.0       3     
filtering sources              0.137     0.0       142   
store source_info              0.088     0.0       1     
total compute_gmfs_and_curves  0.028     0.0       5     
compute poes                   0.021     0.0       5     
saving gmfs                    0.012     0.0       17    
saving ruptures                0.005     0.0       1     
aggregate curves               0.005     0.0       21    
make contexts                  0.004     0.0       5     
filtering ruptures             0.002     0.0       8     
reading site collection        4.439E-04 0.0       1     
============================== ========= ========= ======