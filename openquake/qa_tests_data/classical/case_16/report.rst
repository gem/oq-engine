Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     1,751,642,476      
date           2018-10-03T15:01:39
engine_version 3.3.0-gitd9f5dca908
============== ===================

num_sites = 1, num_levels = 3

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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================================= ======= =============== ================
smlt_path                                     weight  gsim_logic_tree num_realizations
============================================= ======= =============== ================
b11_b21_b32_b41_b52_b61_b72_b81_b92_b101_b112 0.10000 trivial(1)      1/1             
b11_b22_b32_b42_b52_b62_b72_b82_b92_b102_b112 0.10000 trivial(1)      4/1             
b11_b23_b32_b43_b52_b63_b72_b83_b92_b103_b112 0.10000 trivial(1)      1/1             
b11_b23_b33_b43_b53_b63_b73_b83_b93_b103_b113 0.10000 trivial(1)      3/1             
b11_b24_b33_b44_b53_b64_b73_b84_b93_b104_b113 0.10000 trivial(1)      1/1             
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
0      1         A    0     4     375          0.0       0.20697    0.0       25        0.0   
0      2         A    4     8     450          0.0       0.24976    0.0       30        0.0   
0      3         A    8     12    450          0.0       0.72839    0.0       30        0.0   
0      4         A    12    16    375          0.0       0.19612    0.0       25        0.0   
0      5         A    16    20    375          0.0       0.56030    0.0       25        0.0   
1      1         A    0     4     375          0.0       0.19681    0.0       25        0.0   
1      2         A    4     8     450          0.0       0.73304    0.0       30        0.0   
1      3         A    8     12    450          0.0       0.24941    0.0       30        0.0   
1      4         A    12    16    375          0.0       0.20078    0.0       25        0.0   
1      5         A    16    20    375          0.0       0.15849    0.0       25        0.0   
2      1         A    0     4     375          0.0       0.19681    0.0       25        0.0   
2      2         A    4     8     450          0.0       0.24875    0.0       30        0.0   
2      3         A    8     12    450          0.0       0.27233    0.0       30        0.0   
2      4         A    12    16    375          0.0       0.19936    0.0       25        0.0   
2      5         A    16    20    375          0.0       0.15932    0.0       25        0.0   
3      1         A    0     4     425          0.0       0.20080    0.0       25        0.0   
3      2         A    4     8     510          0.0       0.25932    0.0       30        0.0   
3      3         A    8     12    510          0.0       0.73947    0.0       30        0.0   
3      4         A    12    16    425          0.0       0.60251    0.0       25        0.0   
3      5         A    16    20    425          0.0       0.16704    0.0       25        0.0   
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
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04186 NaN     0.04186 0.04186 1      
split_filter       0.20352 0.25538 0.02294 0.38410 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================================== ========
task               sent                                                                     received
read_source_models monitor=0 B fnames=0 B converter=0 B                                     5.26 KB 
split_filter       srcs=20.59 KB monitor=850 B srcfilter=506 B sample_factor=42 B seed=28 B 162.9 KB
================== ======================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
updating source_info     0.42910  0.0       1     
total split_filter       0.40704  0.25781   2     
total read_source_models 0.04186  0.0       1     
======================== ======== ========= ======