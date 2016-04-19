Classical PSHA with non-trivial logic tree (2 source models and 2 GMPEs per tectonic region type)
=================================================================================================

Datastore /home/michele/ssd/calc_10529.hdf5 last updated Tue Apr 19 05:57:12 2016 on gem-tstation

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.1                
area_source_discretization   5.0                
random_seed                  23                 
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.500  `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4             
b2        0.500  `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    4/4             
========= ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
1      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
2      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
3      Campbell2003 ToroEtAl2002         rjb rrup                            mag              
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008: ['<0,b1,b11_b21,w=0.125>', '<1,b1,b11_b22,w=0.125>']
  0,ChiouYoungs2008: ['<2,b1,b12_b21,w=0.125>', '<3,b1,b12_b22,w=0.125>']
  1,Campbell2003: ['<1,b1,b11_b22,w=0.125>', '<3,b1,b12_b22,w=0.125>']
  1,ToroEtAl2002: ['<0,b1,b11_b21,w=0.125>', '<2,b1,b12_b21,w=0.125>']
  2,BooreAtkinson2008: ['<4,b2,b11_b21,w=0.125>', '<5,b2,b11_b22,w=0.125>']
  2,ChiouYoungs2008: ['<6,b2,b12_b21,w=0.125>', '<7,b2,b12_b22,w=0.125>']
  3,Campbell2003: ['<5,b2,b11_b22,w=0.125>', '<7,b2,b12_b22,w=0.125>']
  3,ToroEtAl2002: ['<4,b2,b11_b21,w=0.125>', '<6,b2,b12_b21,w=0.125>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== =========== ============ ======
source_model       trt_id trt                      num_sources eff_ruptures weight
================== ====== ======================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust     1           1,334        1,334 
source_model_1.xml 1      Stable Continental Crust 1           4,100        102   
source_model_2.xml 2      Active Shallow Crust     1           1,297        1,297 
source_model_2.xml 3      Stable Continental Crust 1           5,920        148   
================== ====== ======================== =========== ============ ======

=============== ======
#TRT models     4     
#sources        4     
#eff_ruptures   12,651
filtered_weight 2,882 
=============== ======

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2702          
count_eff_ruptures_num_tasks             83            
count_eff_ruptures_sent.monitor          206421        
count_eff_ruptures_sent.rlzs_assoc       633539        
count_eff_ruptures_sent.sitecol          36271         
count_eff_ruptures_sent.siteidx          415           
count_eff_ruptures_sent.sources          10708250      
count_eff_ruptures_tot_received          224190        
hazard.input_weight                      2881.5        
hazard.n_imts                            1             
hazard.n_levels                          19.0          
hazard.n_realizations                    8             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     152.0         
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            2         SimpleFaultSource 1,334  1,334     0.003       0.296      0.0      
2            2         SimpleFaultSource 1,297  1,297     0.002       0.231      0.0      
3            1         AreaSource        148    296       8.860E-04   0.068      0.0      
1            1         AreaSource        102    205       8.950E-04   0.052      0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               1.038     0.0       1     
splitting sources              0.646     0.0       4     
reading composite source model 0.140     0.0       1     
total count_eff_ruptures       0.023     0.0       83    
filtering sources              0.006     0.0       4     
store source_info              0.004     0.0       1     
aggregate curves               0.001     0.0       83    
reading site collection        3.600E-05 0.0       1     
============================== ========= ========= ======