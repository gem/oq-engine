Mutex sources for Nankai, Japan, case_27
========================================

============== ===================
checksum32     1,195,921,690      
date           2018-06-05T06:39:08
engine_version 3.2.0-git65c4735   
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
case_01   NonParametricSeismicSource 1            0.00500   0.0        1.00000   1         0     
case_02   NonParametricSeismicSource 1            1.740E-05 0.0        1.00000   1         0     
case_03   NonParametricSeismicSource 1            1.049E-05 0.0        1.00000   1         0     
case_04   NonParametricSeismicSource 1            8.583E-06 0.0        1.00000   1         0     
case_05   NonParametricSeismicSource 1            7.868E-06 0.0        1.00000   1         0     
case_07   NonParametricSeismicSource 1            7.868E-06 0.0        1.00000   1         0     
case_08   NonParametricSeismicSource 1            7.868E-06 0.0        1.00000   1         0     
case_06   NonParametricSeismicSource 1            7.629E-06 0.0        1.00000   1         0     
case_09   NonParametricSeismicSource 1            7.391E-06 0.0        1.00000   1         0     
case_10   NonParametricSeismicSource 1            7.391E-06 0.0        1.00000   1         0     
case_11   NonParametricSeismicSource 1            7.391E-06 0.0        1.00000   1         0     
case_12   NonParametricSeismicSource 2            7.391E-06 0.0        1.00000   1         0     
case_13   NonParametricSeismicSource 2            7.391E-06 0.0        1.00000   1         0     
case_14   NonParametricSeismicSource 2            7.153E-06 0.0        1.00000   1         0     
case_15   NonParametricSeismicSource 2            7.153E-06 0.0        1.00000   1         0     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.00512   15    
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00609 0.00139 0.00277 0.00871 15       
count_eff_ruptures 0.01009 NaN     0.01009 0.01009 1        
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
RtreeFilter        srcs=1.09 MB monitor=5.07 KB srcfilter=4.09 KB                        1.09 MB 
count_eff_ruptures sources=1.08 MB param=447 B monitor=353 B srcfilter=233 B gsims=135 B 1.34 KB 
================== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.79387   0.82422   1     
reading composite source model 0.33199   0.01172   1     
managing sources               0.26108   0.0       1     
total prefilter                0.09135   3.66406   15    
total count_eff_ruptures       0.01009   5.86719   1     
unpickling prefilter           0.00690   0.0       15    
store source_info              0.00525   0.0       1     
reading site collection        9.785E-04 0.0       1     
unpickling count_eff_ruptures  3.798E-04 0.0       1     
aggregate curves               3.431E-04 0.0       1     
splitting sources              3.309E-04 0.0       1     
saving probability maps        2.027E-04 0.0       1     
============================== ========= ========= ======