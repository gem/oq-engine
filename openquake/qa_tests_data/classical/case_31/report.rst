Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2018-10-05T03:05:06
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 1, num_levels = 14

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
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
=========== ======= =============== ================
smlt_path   weight  gsim_logic_tree num_realizations
=========== ======= =============== ================
b11_b21_b31 0.11089 trivial(1,1)    1/1             
b11_b21_b32 0.11089 trivial(1,1)    1/1             
b11_b21_b33 0.11122 trivial(1,1)    1/1             
b11_b22_b31 0.11089 trivial(1,1)    1/1             
b11_b22_b32 0.11089 trivial(1,1)    1/1             
b11_b22_b33 0.11122 trivial(1,1)    1/1             
b11_b23_b31 0.11122 trivial(1,1)    1/1             
b11_b23_b32 0.11122 trivial(1,1)    1/1             
b11_b23_b33 0.11156 trivial(1,1)    1/1             
=========== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
1      ToroEtAl2002()      rjb                  mag       
2      BooreAtkinson2008() rjb       vs30       mag rake  
3      ToroEtAl2002()      rjb                  mag       
4      BooreAtkinson2008() rjb       vs30       mag rake  
5      ToroEtAl2002()      rjb                  mag       
6      BooreAtkinson2008() rjb       vs30       mag rake  
7      ToroEtAl2002()      rjb                  mag       
8      BooreAtkinson2008() rjb       vs30       mag rake  
9      ToroEtAl2002()      rjb                  mag       
10     BooreAtkinson2008() rjb       vs30       mag rake  
11     ToroEtAl2002()      rjb                  mag       
12     BooreAtkinson2008() rjb       vs30       mag rake  
13     ToroEtAl2002()      rjb                  mag       
14     BooreAtkinson2008() rjb       vs30       mag rake  
15     ToroEtAl2002()      rjb                  mag       
16     BooreAtkinson2008() rjb       vs30       mag rake  
17     ToroEtAl2002()      rjb                  mag       
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=18, rlzs=9)
  0,BooreAtkinson2008(): [0]
  1,ToroEtAl2002(): [0]
  2,BooreAtkinson2008(): [1]
  3,ToroEtAl2002(): [1]
  4,BooreAtkinson2008(): [2]
  5,ToroEtAl2002(): [2]
  6,BooreAtkinson2008(): [3]
  7,ToroEtAl2002(): [3]
  8,BooreAtkinson2008(): [4]
  9,ToroEtAl2002(): [4]
  10,BooreAtkinson2008(): [5]
  11,ToroEtAl2002(): [5]
  12,BooreAtkinson2008(): [6]
  13,ToroEtAl2002(): [6]
  14,BooreAtkinson2008(): [7]
  15,ToroEtAl2002(): [7]
  16,BooreAtkinson2008(): [8]
  17,ToroEtAl2002(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======================== ============ ============
source_model     grp_id trt                      eff_ruptures tot_ruptures
================ ====== ======================== ============ ============
source_model.xml 0      Active Shallow Crust     310          310         
source_model.xml 1      Stable Continental Crust 1,040        1,040       
source_model.xml 2      Active Shallow Crust     310          310         
source_model.xml 3      Stable Continental Crust 1,040        1,040       
source_model.xml 4      Active Shallow Crust     310          310         
source_model.xml 5      Stable Continental Crust 1,040        1,040       
source_model.xml 6      Active Shallow Crust     310          310         
source_model.xml 7      Stable Continental Crust 1,040        1,040       
source_model.xml 8      Active Shallow Crust     310          310         
source_model.xml 9      Stable Continental Crust 1,040        1,040       
source_model.xml 10     Active Shallow Crust     310          310         
source_model.xml 11     Stable Continental Crust 1,040        1,040       
source_model.xml 12     Active Shallow Crust     310          310         
source_model.xml 13     Stable Continental Crust 1,040        1,040       
source_model.xml 14     Active Shallow Crust     310          310         
source_model.xml 15     Stable Continental Crust 1,040        1,040       
source_model.xml 16     Active Shallow Crust     310          310         
source_model.xml 17     Stable Continental Crust 1,040        1,040       
================ ====== ======================== ============ ============

============= ======
#TRT models   18    
#eff_ruptures 12,150
#tot_ruptures 12,150
#tot_weight   3,726 
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      2         S    0     3     310          0.0       0.00265    0.0       10        0.0   
1      1         A    3     7     1,040        0.0       1.00198    0.0       52        0.0   
2      2         S    0     3     310          0.0       0.00121    0.0       10        0.0   
3      1         A    3     7     1,040        0.0       0.76336    0.0       52        0.0   
4      2         S    0     3     310          0.0       0.00117    0.0       10        0.0   
5      1         A    3     7     1,040        0.0       0.73870    0.0       52        0.0   
6      2         S    0     3     310          0.0       0.00116    0.0       10        0.0   
7      1         A    3     7     1,040        0.0       0.74276    0.0       52        0.0   
8      2         S    0     3     310          0.0       0.00133    0.0       10        0.0   
9      1         A    3     7     1,040        0.0       1.64890    0.0       52        0.0   
10     2         S    0     3     310          0.0       0.00124    0.0       10        0.0   
11     1         A    3     7     1,040        0.0       0.73250    0.0       52        0.0   
12     2         S    0     3     310          0.0       0.00117    0.0       10        0.0   
13     1         A    3     7     1,040        0.0       0.74025    0.0       52        0.0   
14     2         S    0     3     310          0.0       0.00118    0.0       10        0.0   
15     1         A    3     7     1,040        0.0       0.79225    0.0       52        0.0   
16     2         S    0     3     310          0.0       0.00143    0.0       10        0.0   
17     1         A    3     7     1,040        0.0       0.71500    0.0       52        0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       9     
S    0.0       9     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.01860 NaN     0.01860 0.01860 1      
split_filter       0.12926 0.11700 0.04652 0.21199 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================================== =========
task               sent                                                                     received 
read_source_models monitor=0 B fnames=0 B converter=0 B                                     3.02 KB  
split_filter       srcs=12.54 KB monitor=850 B srcfilter=506 B sample_factor=42 B seed=28 B 129.69 KB
================== ======================================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.25851  0.10156   2     
updating source_info     0.23230  0.0       1     
total read_source_models 0.01860  0.0       1     
======================== ======== ========= ======