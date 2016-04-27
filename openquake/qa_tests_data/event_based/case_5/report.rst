Germany_SHARE Combined Model event_based
========================================

gem-tstation:/home/michele/ssd/calc_113.hdf5 updated Wed Apr 27 10:57:12 2016

num_sites = 100, sitecol = 5.19 KB

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 80.0}  
investigation_time           30.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         5.0                
complex_fault_mesh_spacing   5.0                
width_of_mfd_bin             0.1                
area_source_discretization   10.0               
random_seed                  23                 
master_seed                  0                  
oqlite_version               '0.13.0-gitcbbc4a8'
============================ ===================

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
b1        0.500  `source_models/as_model.xml <source_models/as_model.xml>`_                                       trivial(1,0,0,0) 1/1             
b2        0.200  `source_models/fs_bg_source_model.xml <source_models/fs_bg_source_model.xml>`_                   simple(0,0,5,0)  5/5             
b3        0.300  `source_models/ss_model_final_250km_Buffer.xml <source_models/ss_model_final_250km_Buffer.xml>`_ trivial(0,0,0,0) 0/0             
========= ====== ================================================================================================ ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================================================== ================= ======================= =================
trt_id gsims                                                                                  distances         siteparams              ruptparams       
====== ====================================================================================== ================= ======================= =================
1      FaccioliEtAl2010                                                                       rrup              vs30                    rake mag         
4      AkkarBommer2010 Campbell2003SHARE CauzziFaccioli2008 ChiouYoungs2008 ToroEtAl2002SHARE rhypo rjb rx rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ====================================================================================== ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  1,FaccioliEtAl2010: ['<0,b1,@_@_@_b4_1,w=0.714285714286>']
  4,AkkarBommer2010: ['<1,b2,@_b2_1_@_@,w=0.0571428571429>']
  4,Campbell2003SHARE: ['<5,b2,@_b2_5_@_@,w=0.0571428571429>']
  4,CauzziFaccioli2008: ['<2,b2,@_b2_2_@_@,w=0.0571428571429>']
  4,ChiouYoungs2008: ['<3,b2,@_b2_3_@_@,w=0.0571428571429>']
  4,ToroEtAl2002SHARE: ['<4,b2,@_b2_4_@_@,w=0.0571428571429>']>

Number of ruptures per tectonic region type
-------------------------------------------
==================================== ====== ==================== =========== ============ ======
source_model                         trt_id trt                  num_sources eff_ruptures weight
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
======== ==============
hostname 'gem-tstation'
======== ==============

Specific information for event based
------------------------------------
Total number of ruptures: 5
Total number of events: 5

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
4            329       AreaSource   1,544  5,145     0.003       1.761      14       
4            327       AreaSource   1,544  5,145     0.009       2.803      12       
4            328       AreaSource   1,544  5,145     0.003       1.794      11       
4            316       AreaSource   449    1         0.002       0.0        7.077    
4            317       AreaSource   449    1         0.002       0.0        6.955    
4            323       AreaSource   307    1         9.902E-04   0.0        5.662    
4            322       AreaSource   307    1         0.001       0.0        5.642    
4            318       AreaSource   449    1         0.002       0.0        4.897    
4            331       AreaSource   56     1         9.458E-04   0.0        1.056    
4            332       AreaSource   56     1         9.460E-04   0.0        1.047    
4            330       AreaSource   56     1         9.840E-04   0.0        1.023    
4            264       AreaSource   85     1         9.170E-04   0.0        0.921    
4            265       AreaSource   85     1         9.229E-04   0.0        0.894    
4            263       AreaSource   85     1         9.160E-04   0.0        0.860    
4            333       AreaSource   39     1         0.001       0.0        0.788    
4            334       AreaSource   39     1         9.840E-04   0.0        0.726    
4            267       AreaSource   56     1         8.190E-04   0.0        0.572    
4            266       AreaSource   56     1         8.271E-04   0.0        0.571    
4            248       AreaSource   30     1         9.151E-04   0.0        0.390    
4            249       AreaSource   30     1         8.869E-04   0.0        0.357    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         82        0.035     21    
reading composite source model 11        0.0       1     
managing sources               7.033     0.0       1     
splitting sources              6.357     0.0       3     
filtering sources              0.157     0.0       142   
store source_info              0.124     0.0       1     
total compute_gmfs_and_curves  0.012     0.0       5     
compute poes                   0.007     0.0       5     
saving gmfs                    0.006     0.0       17    
saving ruptures                0.005     0.0       1     
filtering ruptures             0.003     0.0       8     
make contexts                  0.003     0.0       5     
aggregate curves               0.002     0.0       21    
reading site collection        6.280E-04 0.0       1     
============================== ========= ========= ======