Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     3,886,657,983      
date           2018-05-15T04:12:48
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 8

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================== ========= ========== ==========
grp_id gsims                              distances siteparams ruptparams
====== ================================== ========= ========== ==========
0      AkkarBommer2010() SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 482          6.483E-04 2.096E-04  15        15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 6.483E-04 1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =========
operation-duration mean    stddev    min       max     num_tasks
prefilter          0.00778 0.00172   0.00494   0.01034 15       
count_ruptures     0.00160 5.231E-04 8.504E-04 0.00253 12       
================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=8, weight=90, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   90      NaN    90  90  1
======== ======= ====== === === =

Slowest task
------------
taskno=2, weight=120, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 NaN    1   1   1
weight   120     NaN    120 120 1
======== ======= ====== === === =

Informational data
------------------
============== =========================================================================== ========
task           sent                                                                        received
prefilter      srcs=15.36 KB monitor=4.78 KB srcfilter=3.35 KB                             17 KB   
count_ruptures sources=15.34 KB srcfilter=8.4 KB param=5.3 KB monitor=3.9 KB gsims=2.45 KB 4.2 KB  
============== =========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.11666   5.07031   15    
managing sources               0.06251   0.0       1     
total count_ruptures           0.01922   1.74609   12    
reading composite source model 0.00668   0.0       1     
store source_info              0.00402   0.0       1     
reading site collection        0.00182   0.0       1     
unpickling prefilter           0.00109   0.0       15    
reading exposure               8.080E-04 0.0       1     
splitting sources              6.928E-04 0.0       1     
unpickling count_ruptures      4.473E-04 0.0       12    
aggregate curves               2.000E-04 0.0       12    
saving probability maps        3.481E-05 0.0       1     
============================== ========= ========= ======