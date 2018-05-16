Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     172,806,574        
date           2018-05-15T04:12:49
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 7, num_levels = 24

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
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
exposure                `exposure_model_7.xml <exposure_model_7.xml>`_              
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
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
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
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 0.0    1   1   3         3         
Concrete 1.00000 0.0    1   1   2         2         
Steel    1.00000 0.0    1   1   2         2         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 482          5.007E-04 2.270E-04  105       15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 5.007E-04 1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =========
operation-duration mean    stddev    min       max     num_tasks
prefilter          0.00911 0.00201   0.00433   0.01211 15       
count_ruptures     0.00190 7.402E-04 8.230E-04 0.00266 6        
================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=1, weight=158, duration=0 s, sources="1"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   7.00000 NaN    7   7   1
weight   158     NaN    158 158 1
======== ======= ====== === === =

Slowest task
------------
taskno=5, weight=224, duration=0 s, sources="1"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   7.00000 0.0     7   7   2
weight   112     9.35414 105 119 2
======== ======= ======= === === =

Informational data
------------------
============== ============================================================================ ========
task           sent                                                                         received
prefilter      srcs=15.36 KB monitor=4.78 KB srcfilter=3.35 KB                              17.35 KB
count_ruptures sources=11.03 KB srcfilter=6.12 KB param=4.22 KB monitor=1.95 KB gsims=720 B 2.1 KB  
============== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total prefilter                0.13670   5.07031   15    
managing sources               0.06045   0.0       1     
total count_ruptures           0.01143   1.06250   6     
reading composite source model 0.00604   0.0       1     
store source_info              0.00388   0.0       1     
reading site collection        0.00277   0.0       1     
reading exposure               0.00131   0.0       1     
unpickling prefilter           0.00106   0.0       15    
splitting sources              7.052E-04 0.0       1     
unpickling count_ruptures      2.198E-04 0.0       6     
aggregate curves               1.085E-04 0.0       6     
saving probability maps        3.409E-05 0.0       1     
============================== ========= ========= ======