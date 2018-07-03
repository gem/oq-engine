Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     1,195,921,690      
date           2018-06-26T14:57:44
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 6

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                None              
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================== ========= ========== ==============
grp_id gsims                    distances siteparams ruptparams    
====== ======================== ========= ========== ==============
0      SiMidorikawa1999SInter() rrup                 hypo_depth mag
====== ======================== ========= ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SiMidorikawa1999SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Subduction Interface 19           19          
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ========================== ============ ========= ========== ========= ========= ======
source_id source_class               num_ruptures calc_time split_time num_sites num_split events
========= ========================== ============ ========= ========== ========= ========= ======
case_01   NonParametricSeismicSource 1            0.00509   0.0        1.00000   1         0     
case_02   NonParametricSeismicSource 1            1.717E-05 0.0        1.00000   1         0     
case_03   NonParametricSeismicSource 1            1.121E-05 0.0        1.00000   1         0     
case_04   NonParametricSeismicSource 1            9.060E-06 0.0        1.00000   1         0     
case_05   NonParametricSeismicSource 1            8.821E-06 0.0        1.00000   1         0     
case_10   NonParametricSeismicSource 1            8.345E-06 0.0        1.00000   1         0     
case_07   NonParametricSeismicSource 1            8.106E-06 0.0        1.00000   1         0     
case_09   NonParametricSeismicSource 1            8.106E-06 0.0        1.00000   1         0     
case_14   NonParametricSeismicSource 2            8.106E-06 0.0        1.00000   1         0     
case_06   NonParametricSeismicSource 1            7.868E-06 0.0        1.00000   1         0     
case_11   NonParametricSeismicSource 1            7.868E-06 0.0        1.00000   1         0     
case_12   NonParametricSeismicSource 2            7.868E-06 0.0        1.00000   1         0     
case_13   NonParametricSeismicSource 2            7.868E-06 0.0        1.00000   1         0     
case_08   NonParametricSeismicSource 1            7.629E-06 0.0        1.00000   1         0     
case_15   NonParametricSeismicSource 2            7.629E-06 0.0        1.00000   1         0     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.00522   15    
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00600 0.00133 0.00257 0.00786 15       
count_eff_ruptures 0.01033 NaN     0.01033 0.01033 1        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=1, weight=1, duration=0 s, sources="case_01 case_02 case_03 case_04 case_05 case_06 case_07 case_08 case_09 case_10 case_11 case_12 case_13 case_14 case_15"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   1.00000 0.0     1       1       15
weight   1.26667 0.45774 1.00000 2.00000 15
======== ======= ======= ======= ======= ==

Slowest task
------------
taskno=1, weight=1, duration=0 s, sources="case_01 case_02 case_03 case_04 case_05 case_06 case_07 case_08 case_09 case_10 case_11 case_12 case_13 case_14 case_15"

======== ======= ======= ======= ======= ==
variable mean    stddev  min     max     n 
======== ======= ======= ======= ======= ==
nsites   1.00000 0.0     1       1       15
weight   1.26667 0.45774 1.00000 2.00000 15
======== ======= ======= ======= ======= ==

Data transfer
-------------
================== ===================================================================== ========
task               sent                                                                  received
RtreeFilter        srcs=1.09 MB monitor=4.72 KB srcfilter=4.09 KB                        1.09 MB 
count_eff_ruptures sources=1.08 MB param=447 B monitor=329 B srcfilter=246 B gsims=135 B 1.34 KB 
================== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.26372   0.0       1     
managing sources               0.17893   0.0       1     
total prefilter                0.09005   3.25781   15    
total count_eff_ruptures       0.01033   6.39844   1     
store source_info              0.00616   0.0       1     
unpickling prefilter           0.00458   0.0       15    
reading site collection        3.293E-04 0.0       1     
unpickling count_eff_ruptures  3.035E-04 0.0       1     
aggregate curves               2.816E-04 0.0       1     
splitting sources              2.294E-04 0.0       1     
============================== ========= ========= ======