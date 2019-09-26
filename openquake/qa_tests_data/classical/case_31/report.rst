Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ===================
checksum32     283,798,826        
date           2019-09-24T15:21:20
engine_version 3.7.0-git749bb363b3
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
========= ====== ==== ============ ========= ========= ============ =========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========= ====== ==== ============ ========= ========= ============ =========
2         0      S    310          0.00887   3.00000   930          104,798  
1         1      A    1,040        4.668E-04 3.00000   3,120        6,683,467
========= ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    4.668E-04 9     
S    0.00887   9     
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 6 duplicate sources with multiplicity 3.0: ['1' '1' '1' '2' '2' '2']

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
preclassical       0.00194 0.00164 3.397E-04 0.00372 6      
read_source_models 0.02511 0.00302 0.01784   0.02819 9      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
preclassical       srcs=9.34 KB srcfilter=3.79 KB params=3.56 KB 2.06 KB 
read_source_models converter=2.76 KB fnames=963 B                28.07 KB
================== ============================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1833                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.22597   0.0       9     
total preclassical       0.01165   0.0       6     
store source_info        0.00246   0.0       1     
aggregate curves         0.00187   0.0       6     
managing sources         3.746E-04 0.0       1     
======================== ========= ========= ======