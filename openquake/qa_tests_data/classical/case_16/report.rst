Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66992.hdf5 Wed Nov  9 08:15:47 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 10                              
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `1.8 0.8 <1.8 0.8>`_                                        
source                  `1.8 0.8 <1.8 0.8>`_                                        
source                  `1.8 0.8 <1.8 0.8>`_                                        
source                  `1.8 0.8 <1.8 0.8>`_                                        
source                  `1.8 0.8 <1.8 0.8>`_                                        
source                  `1.9 0.9 <1.9 0.9>`_                                        
source                  `1.9 0.9 <1.9 0.9>`_                                        
source                  `1.9 0.9 <1.9 0.9>`_                                        
source                  `1.9 0.9 <1.9 0.9>`_                                        
source                  `1.9 0.9 <1.9 0.9>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.1 1.1 <2.1 1.1>`_                                        
source                  `2.1 1.1 <2.1 1.1>`_                                        
source                  `2.1 1.1 <2.1 1.1>`_                                        
source                  `2.1 1.1 <2.1 1.1>`_                                        
source                  `2.1 1.1 <2.1 1.1>`_                                        
source                  `2.2 1.2 <2.2 1.2>`_                                        
source                  `2.2 1.2 <2.2 1.2>`_                                        
source                  `2.2 1.2 <2.2 1.2>`_                                        
source                  `2.2 1.2 <2.2 1.2>`_                                        
source                  `2.2 1.2 <2.2 1.2>`_                                        
source                  `6.3 <6.3>`_                                                
source                  `6.3 <6.3>`_                                                
source                  `6.3 <6.3>`_                                                
source                  `6.3 <6.3>`_                                                
source                  `6.3 <6.3>`_                                                
source                  `6.5 <6.5>`_                                                
source                  `6.5 <6.5>`_                                                
source                  `6.5 <6.5>`_                                                
source                  `6.5 <6.5>`_                                                
source                  `6.5 <6.5>`_                                                
source                  `6.7 <6.7>`_                                                
source                  `6.7 <6.7>`_                                                
source                  `6.7 <6.7>`_                                                
source                  `6.7 <6.7>`_                                                
source                  `6.7 <6.7>`_                                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================================= ====== ====================================== =============== ================
smlt_path                                     weight source_model_file                      gsim_logic_tree num_realizations
============================================= ====== ====================================== =============== ================
b11_b20_b31_b43_b52_b62_b72_b82_b91_b103_b112 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b21_b32_b43_b52_b62_b72_b82_b92_b102_b112 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b21_b32_b43_b52_b62_b73_b82_b92_b103_b113 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b22_b31_b43_b52_b64_b73_b84_b92_b104_b112 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b22_b32_b42_b51_b61_b72_b83_b91_b101_b111 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b22_b32_b42_b53_b62_b72_b81_b92_b103_b112 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b22_b33_b42_b52_b62_b72_b82_b92_b100_b112 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b23_b32_b43_b52_b62_b73_b82_b93_b101_b113 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b24_b32_b41_b51_b62_b71_b84_b93_b101_b111 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b11_b24_b33_b40_b52_b62_b72_b81_b91_b102_b112 0.100  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
============================================= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       rake mag  
1      BooreAtkinson2008() rjb       vs30       rake mag  
2      BooreAtkinson2008() rjb       vs30       rake mag  
3      BooreAtkinson2008() rjb       vs30       rake mag  
4      BooreAtkinson2008() rjb       vs30       rake mag  
5      BooreAtkinson2008() rjb       vs30       rake mag  
6      BooreAtkinson2008() rjb       vs30       rake mag  
7      BooreAtkinson2008() rjb       vs30       rake mag  
8      BooreAtkinson2008() rjb       vs30       rake mag  
9      BooreAtkinson2008() rjb       vs30       rake mag  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=10, rlzs=10)
  0,BooreAtkinson2008(): ['<0,b11_b20_b31_b43_b52_b62_b72_b82_b91_b103_b112~b11,w=0.1>']
  1,BooreAtkinson2008(): ['<1,b11_b21_b32_b43_b52_b62_b72_b82_b92_b102_b112~b11,w=0.1>']
  2,BooreAtkinson2008(): ['<2,b11_b21_b32_b43_b52_b62_b73_b82_b92_b103_b113~b11,w=0.1>']
  3,BooreAtkinson2008(): ['<3,b11_b22_b31_b43_b52_b64_b73_b84_b92_b104_b112~b11,w=0.1>']
  4,BooreAtkinson2008(): ['<4,b11_b22_b32_b42_b51_b61_b72_b83_b91_b101_b111~b11,w=0.1>']
  5,BooreAtkinson2008(): ['<5,b11_b22_b32_b42_b53_b62_b72_b81_b92_b103_b112~b11,w=0.1>']
  6,BooreAtkinson2008(): ['<6,b11_b22_b33_b42_b52_b62_b72_b82_b92_b100_b112~b11,w=0.1>']
  7,BooreAtkinson2008(): ['<7,b11_b23_b32_b43_b52_b62_b73_b82_b93_b101_b113~b11,w=0.1>']
  8,BooreAtkinson2008(): ['<8,b11_b24_b32_b41_b51_b62_b71_b84_b93_b101_b111~b11,w=0.1>']
  9,BooreAtkinson2008(): ['<9,b11_b24_b33_b40_b52_b62_b72_b81_b91_b102_b112~b11,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 5           1925         1,925       
source_model.xml 1      Active Shallow Crust 5           2025         2,025       
source_model.xml 2      Active Shallow Crust 5           2135         2,135       
source_model.xml 3      Active Shallow Crust 5           2035         2,035       
source_model.xml 4      Active Shallow Crust 5           1865         1,865       
source_model.xml 5      Active Shallow Crust 5           2085         2,085       
source_model.xml 6      Active Shallow Crust 5           2075         2,075       
source_model.xml 7      Active Shallow Crust 5           2185         2,185       
source_model.xml 8      Active Shallow Crust 5           1905         1,905       
source_model.xml 9      Active Shallow Crust 5           2025         2,025       
================ ====== ==================== =========== ============ ============

============= ======
#TRT models   10    
#sources      50    
#eff_ruptures 20,260
#tot_ruptures 20,260
#tot_weight   2,026 
============= ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,255       
count_eff_ruptures_num_tasks             17          
count_eff_ruptures_sent.gsims            1,581       
count_eff_ruptures_sent.monitor          17,255      
count_eff_ruptures_sent.sitecol          7,361       
count_eff_ruptures_sent.sources          59,482      
count_eff_ruptures_tot_received          21,335      
hazard.input_weight                      2,026       
hazard.n_imts                            1           
hazard.n_levels                          3           
hazard.n_realizations                    10          
hazard.n_sites                           1           
hazard.n_sources                         50          
hazard.output_weight                     30          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
7      5         AreaSource   425          0.0       1         0        
0      4         AreaSource   325          0.0       1         0        
4      2         AreaSource   390          0.0       1         0        
9      3         AreaSource   450          0.0       1         0        
1      1         AreaSource   375          0.0       1         0        
3      5         AreaSource   375          0.0       1         0        
2      5         AreaSource   425          0.0       1         0        
7      2         AreaSource   450          0.0       1         0        
8      3         AreaSource   390          0.0       1         0        
3      1         AreaSource   325          0.0       1         0        
2      2         AreaSource   450          0.0       1         0        
5      2         AreaSource   510          0.0       1         0        
2      1         AreaSource   375          0.0       1         0        
6      3         AreaSource   450          0.0       1         0        
0      3         AreaSource   450          0.0       1         0        
7      3         AreaSource   510          0.0       1         0        
4      1         AreaSource   375          0.0       1         0        
8      2         AreaSource   390          0.0       1         0        
1      2         AreaSource   450          0.0       1         0        
3      2         AreaSource   450          0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       50    
============ ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ===== =========
operation-duration mean      stddev    min       max   num_tasks
count_eff_ruptures 9.092E-04 1.541E-04 6.299E-04 0.001 17       
================== ========= ========= ========= ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.257     0.0       1     
filtering composite source model 0.023     0.0       1     
managing sources                 0.018     0.0       1     
total count_eff_ruptures         0.015     0.0       17    
store source_info                7.291E-04 0.0       1     
aggregate curves                 2.189E-04 0.0       17    
reading site collection          2.813E-05 0.0       1     
saving probability maps          2.193E-05 0.0       1     
================================ ========= ========= ======