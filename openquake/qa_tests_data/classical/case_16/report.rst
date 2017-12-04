Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     1,751,642,476      
date           2017-11-08T18:07:15
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================================= ====== =============== ================
smlt_path                                     weight gsim_logic_tree num_realizations
============================================= ====== =============== ================
b11_b21_b32_b41_b52_b61_b72_b81_b92_b101_b112 0.100  trivial(1)      1/1             
b11_b22_b32_b42_b52_b62_b72_b82_b92_b102_b112 0.100  trivial(1)      4/1             
b11_b23_b32_b43_b52_b63_b72_b83_b92_b103_b112 0.100  trivial(1)      1/1             
b11_b23_b33_b43_b53_b63_b73_b83_b93_b103_b113 0.100  trivial(1)      3/1             
b11_b24_b33_b44_b53_b64_b73_b84_b93_b104_b113 0.100  trivial(1)      1/1             
============================================= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
2      BooreAtkinson2008() rjb       vs30       mag rake  
3      BooreAtkinson2008() rjb       vs30       mag rake  
4      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): [0]
  1,BooreAtkinson2008(): [1 2 3 4]
  2,BooreAtkinson2008(): [5]
  3,BooreAtkinson2008(): [6 7 8]
  4,BooreAtkinson2008(): [9]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 5           2,025        2,025       
source_model.xml 1      Active Shallow Crust 5           2,025        2,025       
source_model.xml 2      Active Shallow Crust 5           2,025        2,025       
source_model.xml 3      Active Shallow Crust 5           2,295        2,295       
source_model.xml 4      Active Shallow Crust 5           2,295        2,295       
================ ====== ==================== =========== ============ ============

============= ======
#TRT models   5     
#sources      25    
#eff_ruptures 10,665
#tot_ruptures 10,665
#tot_weight   0     
============= ======

Informational data
------------------
=========================== ================================================================================
count_eff_ruptures.received tot 6.42 KB, max_per_task 698 B                                                 
count_eff_ruptures.sent     sources 30.15 KB, srcfilter 6.68 KB, param 5.78 KB, monitor 3.2 KB, gsims 1020 B
hazard.input_weight         2133.0                                                                          
hazard.n_imts               1                                                                               
hazard.n_levels             3                                                                               
hazard.n_realizations       10                                                                              
hazard.n_sites              1                                                                               
hazard.n_sources            25                                                                              
hazard.output_weight        9.0                                                                             
hostname                    tstation.gem.lan                                                                
require_epsilons            False                                                                           
=========================== ================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
3      1         AreaSource   425          0.002     1         1        
0      5         AreaSource   375          0.001     1         1        
0      1         AreaSource   375          0.001     1         1        
4      1         AreaSource   425          0.001     1         1        
1      1         AreaSource   375          0.001     1         1        
2      1         AreaSource   375          0.001     1         1        
2      5         AreaSource   375          0.001     1         1        
3      5         AreaSource   425          0.001     1         1        
1      2         AreaSource   450          0.001     1         1        
0      3         AreaSource   450          0.001     1         1        
4      2         AreaSource   510          0.001     1         1        
2      3         AreaSource   450          0.001     1         1        
3      4         AreaSource   425          0.001     1         1        
3      2         AreaSource   510          0.001     1         1        
2      2         AreaSource   450          0.001     1         1        
0      2         AreaSource   450          0.001     1         1        
0      4         AreaSource   375          0.001     1         1        
3      3         AreaSource   510          0.001     1         1        
1      3         AreaSource   450          0.001     1         1        
1      4         AreaSource   375          0.001     1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.033     25    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.004 0.002  0.001 0.007 10       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.130     0.0       1     
total count_eff_ruptures       0.042     0.0       10    
prefiltering source model      0.016     0.0       1     
managing sources               0.014     0.0       1     
store source_info              0.007     0.0       1     
aggregate curves               2.618E-04 0.0       10    
saving probability maps        4.530E-05 0.0       1     
reading site collection        4.292E-05 0.0       1     
============================== ========= ========= ======