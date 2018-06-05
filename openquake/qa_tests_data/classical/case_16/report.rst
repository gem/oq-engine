Classical PSHA with non-trivial logic tree (1 source model + 5 (a, b) pairs per source + 3 Mmax per source
==========================================================================================================

============== ===================
checksum32     1,751,642,476      
date           2018-06-05T06:39:15
engine_version 3.2.0-git65c4735   
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
source_model.xml 0      Active Shallow Crust 2,970        2,025       
source_model.xml 1      Active Shallow Crust 2,970        2,025       
source_model.xml 2      Active Shallow Crust 2,965        2,025       
source_model.xml 3      Active Shallow Crust 2,957        2,025       
source_model.xml 4      Active Shallow Crust 2,754        2,025       
================ ====== ==================== ============ ============

============= ======
#TRT models   5     
#eff_ruptures 14,616
#tot_ruptures 10,125
#tot_weight   1,067 
============= ======

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
3         AreaSource   510          0.02229   0.00647    1.00000   163       0     
5         AreaSource   425          0.01977   0.00451    1.00000   168       0     
2         AreaSource   510          0.01668   0.00655    1.00000   241       0     
4         AreaSource   425          0.01589   0.00601    1.00000   127       0     
1         AreaSource   425          0.00871   0.00617    1.00000   225       0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.08334   5     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00638 0.00263 0.00127 0.01549 57       
count_eff_ruptures 0.01354 0.00129 0.01187 0.01594 11       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=5, weight=99, duration=0 s, sources="1 2 3 5"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       66
weight   1.50000 0.0    1.50000 1.50000 66
======== ======= ====== ======= ======= ==

Slowest task
------------
taskno=3, weight=99, duration=0 s, sources="1 2 3 5"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   1.00000 0.0    1       1       66
weight   1.50000 0.0    1.50000 1.50000 66
======== ======= ====== ======= ======= ==

Data transfer
-------------
================== ============================================================================== =========
task               sent                                                                           received 
RtreeFilter        srcs=182.63 KB monitor=19.26 KB srcfilter=15.53 KB                             213.08 KB
count_eff_ruptures sources=188.51 KB param=4.63 KB monitor=3.79 KB srcfilter=2.5 KB gsims=1.41 KB 5.46 KB  
================== ============================================================================== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             1.03699   0.0       1     
managing sources               0.50337   0.0       1     
total prefilter                0.36345   3.03516   57    
reading composite source model 0.18492   0.0       1     
splitting sources              0.14906   0.0       1     
total count_eff_ruptures       0.14897   5.75781   11    
unpickling prefilter           0.03546   0.0       57    
store source_info              0.00660   0.0       1     
aggregate curves               0.00337   0.0       11    
unpickling count_eff_ruptures  0.00325   0.0       11    
reading site collection        9.158E-04 0.0       1     
saving probability maps        2.031E-04 0.0       1     
============================== ========= ========= ======