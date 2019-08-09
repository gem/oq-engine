Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2019-07-30T15:04:16
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 1, num_levels = 14, num_rlzs = 9

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
=========== ======= =============== ================
smlt_path   weight  gsim_logic_tree num_realizations
=========== ======= =============== ================
b11_b21_b31 0.11089 trivial(1,1)    1               
b11_b21_b32 0.11089 trivial(1,1)    1               
b11_b21_b33 0.11122 trivial(1,1)    1               
b11_b22_b31 0.11089 trivial(1,1)    1               
b11_b22_b32 0.11089 trivial(1,1)    1               
b11_b22_b33 0.11122 trivial(1,1)    1               
b11_b23_b31 0.11122 trivial(1,1)    1               
b11_b23_b32 0.11122 trivial(1,1)    1               
b11_b23_b33 0.11156 trivial(1,1)    1               
=========== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[ToroEtAl2002]'      rjb                  mag       
2      '[BooreAtkinson2008]' rjb       vs30       mag rake  
3      '[ToroEtAl2002]'      rjb                  mag       
4      '[BooreAtkinson2008]' rjb       vs30       mag rake  
5      '[ToroEtAl2002]'      rjb                  mag       
6      '[BooreAtkinson2008]' rjb       vs30       mag rake  
7      '[ToroEtAl2002]'      rjb                  mag       
8      '[BooreAtkinson2008]' rjb       vs30       mag rake  
9      '[ToroEtAl2002]'      rjb                  mag       
10     '[BooreAtkinson2008]' rjb       vs30       mag rake  
11     '[ToroEtAl2002]'      rjb                  mag       
12     '[BooreAtkinson2008]' rjb       vs30       mag rake  
13     '[ToroEtAl2002]'      rjb                  mag       
14     '[BooreAtkinson2008]' rjb       vs30       mag rake  
15     '[ToroEtAl2002]'      rjb                  mag       
16     '[BooreAtkinson2008]' rjb       vs30       mag rake  
17     '[ToroEtAl2002]'      rjb                  mag       
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=18, rlzs=9)>

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
============= ======

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =======
source_id grp_id code num_ruptures calc_time num_sites weight speed  
========= ====== ==== ============ ========= ========= ====== =======
1         1      A    1,040        0.01344   3.00000   3,120  232,161
2         0      S    310          0.00987   3.00000   930    94,259 
========= ====== ==== ============ ========= ========= ====== =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.01344   9     
S    0.00987   9     
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00433 0.00203 0.00244 0.00813 6      
read_source_models 0.03369 0.01239 0.02083 0.06235 9      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================== ========
task               sent                                                     received
preclassical       srcs=9.3 KB params=3.56 KB srcfilter=1.29 KB gsims=906 B 2.06 KB 
read_source_models converter=2.76 KB fnames=900 B                           28.01 KB
================== ======================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15522               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.30321  0.19531   9     
total preclassical       0.02596  0.0       6     
managing sources         0.01037  0.0       1     
store source_info        0.00372  0.0       1     
aggregate curves         0.00273  0.0       6     
======================== ======== ========= ======