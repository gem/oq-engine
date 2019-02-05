Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     1,751,642,476      
date           2019-02-03T09:39:38
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================================= ======= =============== ================
smlt_path                                     weight  gsim_logic_tree num_realizations
============================================= ======= =============== ================
b11_b21_b32_b41_b52_b61_b72_b81_b92_b101_b112 0.10000 trivial(1)      1               
b11_b22_b32_b42_b52_b62_b72_b82_b92_b102_b112 0.10000 trivial(1)      1               
b11_b23_b32_b43_b52_b63_b72_b83_b92_b103_b112 0.10000 trivial(1)      1               
b11_b23_b33_b43_b53_b63_b73_b83_b93_b103_b113 0.10000 trivial(1)      1               
b11_b24_b33_b44_b53_b64_b73_b84_b93_b104_b113 0.10000 trivial(1)      1               
============================================= ======= =============== ================

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
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,025        2,025       
source_model.xml 1      Active Shallow Crust 2,025        2,025       
source_model.xml 2      Active Shallow Crust 2,025        2,025       
source_model.xml 3      Active Shallow Crust 2,295        2,025       
source_model.xml 4      Active Shallow Crust 2,295        2,025       
================ ====== ==================== ============ ============

============= ======
#TRT models   5     
#eff_ruptures 10,665
#tot_ruptures 10,125
#tot_weight   1,067 
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
4      5         A    96    100   425          0.0       0.08115    25        25        42    
4      4         A    92    96    425          0.0       0.11596    25        25        42    
4      3         A    88    92    510          0.0       0.12543    30        30        51    
4      2         A    84    88    510          0.0       0.12582    30        30        51    
4      1         A    80    84    425          0.0       0.09978    25        25        42    
3      5         A    76    80    425          0.0       0.07476    25        25        42    
3      4         A    72    76    425          0.0       0.09941    25        25        42    
3      3         A    68    72    510          0.0       0.12581    30        30        51    
3      2         A    64    68    510          0.0       0.12769    30        30        51    
3      1         A    60    64    425          0.0       0.09862    25        25        42    
2      5         A    56    60    375          0.0       0.07441    25        25        37    
2      4         A    52    56    375          0.0       0.10022    25        25        37    
2      3         A    48    52    450          0.0       0.14781    30        30        45    
2      2         A    44    48    450          0.0       0.12823    30        30        45    
2      1         A    40    44    375          0.0       0.10709    25        25        37    
1      5         A    36    40    375          0.0       0.07999    25        25        37    
1      4         A    32    36    375          0.0       0.10659    25        25        37    
1      3         A    28    32    450          0.0       0.13755    30        30        45    
1      2         A    24    28    450          0.0       0.15563    30        30        45    
1      1         A    20    24    375          0.0       0.10661    25        25        37    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       25    
==== ========= ======

Duplicated sources
------------------
Found 5 source(s) with the same ID and 0 true duplicate(s)
Here is a fake duplicate: 2

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.02387 7.171E-04 0.02309 0.02489 5      
split_filter       0.08587 0.09949   0.01552 0.15622 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=1.53 KB fnames=535 B          26.92 KB
split_filter       srcs=21.11 KB srcfilter=506 B seed=28 B 163.7 KB
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.17174  2.57422   2     
total read_source_models 0.11935  0.60938   5     
======================== ======== ========= ======