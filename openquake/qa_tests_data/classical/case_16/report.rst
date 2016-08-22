Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

gem-tstation:/home/michele/ssd/calc_40729.hdf5 updated Mon Aug 22 13:03:18 2016

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
engine_version               '2.1.0-git8cbb23e'              
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
====== ======================= ============ ============= ==========
grp_id gsims                   distances    siteparams    ruptparams
====== ======================= ============ ============= ==========
0      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
1      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
2      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
3      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
4      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
5      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
6      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
7      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
8      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
9      ['BooreAtkinson2008()'] set(['rjb']) set(['vs30']) rake mag  
====== ======================= ============ ============= ==========

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
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 5           1925         48    
source_model.xml 1      Active Shallow Crust 5           2025         50    
source_model.xml 2      Active Shallow Crust 5           2135         53    
source_model.xml 3      Active Shallow Crust 5           2035         50    
source_model.xml 4      Active Shallow Crust 5           1865         46    
source_model.xml 5      Active Shallow Crust 5           2085         52    
source_model.xml 6      Active Shallow Crust 5           2075         51    
source_model.xml 7      Active Shallow Crust 5           2185         54    
source_model.xml 8      Active Shallow Crust 5           1905         47    
source_model.xml 9      Active Shallow Crust 5           2025         50    
================ ====== ==================== =========== ============ ======

=============== ======
#TRT models     10    
#sources        50    
#eff_ruptures   20,260
filtered_weight 506   
=============== ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,828       
classical_num_tasks             22          
classical_sent.monitor          17,776      
classical_sent.rlzs_by_gsim     13,838      
classical_sent.sitecol          9,526       
classical_sent.sources          64,946      
classical_tot_received          39,990      
hazard.input_weight             506         
hazard.n_imts                   1           
hazard.n_levels                 3.000       
hazard.n_realizations           10          
hazard.n_sites                  1           
hazard.n_sources                50          
hazard.output_weight            30          
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
3            3         AreaSource   12     1         8.159E-04   0.0        0.431         0.431         1        
2            3         AreaSource   12     1         8.180E-04   0.0        0.424         0.424         1        
2            5         AreaSource   10     1         8.209E-04   0.0        0.391         0.391         1        
4            1         AreaSource   9.375  1         8.290E-04   0.0        0.387         0.387         1        
5            2         AreaSource   12     1         8.180E-04   0.0        0.353         0.353         1        
1            3         AreaSource   11     1         8.152E-04   0.0        0.349         0.349         1        
1            2         AreaSource   11     1         8.299E-04   0.0        0.347         0.347         1        
4            3         AreaSource   11     1         8.140E-04   0.0        0.346         0.346         1        
7            3         AreaSource   12     1         8.199E-04   0.0        0.345         0.345         1        
3            2         AreaSource   11     1         8.199E-04   0.0        0.340         0.340         1        
0            2         AreaSource   11     1         8.368E-04   0.0        0.335         0.335         1        
6            3         AreaSource   11     1         8.130E-04   0.0        0.335         0.335         1        
1            4         AreaSource   9.375  1         8.111E-04   0.0        0.324         0.324         1        
1            1         AreaSource   9.375  1         8.149E-04   0.0        0.323         0.323         1        
0            3         AreaSource   11     1         8.159E-04   0.0        0.320         0.320         1        
2            2         AreaSource   11     1         8.199E-04   0.0        0.317         0.317         1        
6            2         AreaSource   11     1         8.159E-04   0.0        0.315         0.315         1        
5            4         AreaSource   9.375  1         8.111E-04   0.0        0.315         0.315         1        
6            1         AreaSource   10     1         8.311E-04   0.0        0.304         0.304         1        
7            2         AreaSource   11     1         8.111E-04   0.0        0.300         0.300         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.041       0.0        14            14            50        50    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.682 0.202  0.281 1.025 22       
classical.memory_mb 0.0   0.0    0.0   0.0   22       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                15        0.0       22    
making contexts                5.533     0.0       20,260
computing poes                 3.779     0.0       20,260
reading composite source model 0.245     0.0       1     
managing sources               0.095     0.0       1     
filtering sources              0.041     0.0       50    
store source_info              0.029     0.0       1     
saving probability maps        0.017     0.0       1     
read poes                      0.006     0.0       1     
aggregate curves               6.213E-04 0.0       22    
reading site collection        3.886E-05 0.0       1     
============================== ========= ========= ======