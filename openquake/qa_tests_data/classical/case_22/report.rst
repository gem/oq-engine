Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     1,554,747,528      
date           2018-06-26T14:57:31
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 21, num_levels = 114

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
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
======================= ================================================================
Name                    File                                                            
======================= ================================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                    
job_ini                 `job.ini <job.ini>`_                                            
sites                   `sites.csv <sites.csv>`_                                        
source                  `Alaska_asc_grid_NSHMP2007.xml <Alaska_asc_grid_NSHMP2007.xml>`_
source                  `extra_source_model.xml <extra_source_model.xml>`_              
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_    
======================= ================================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
Alaska_asc_grid_NSHMP2007 1.00000 simple(4)       4/4             
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================================= ========= ========== =======================
grp_id gsims                                                                                                   distances siteparams ruptparams             
====== ======================================================================================================= ========= ========== =======================
1      AbrahamsonSilva1997() CampbellBozorgnia2003NSHMP2007() SadighEtAl1997() YoungsEtAl1997SInterNSHMP2008() rjb rrup  vs30       dip hypo_depth mag rake
====== ======================================================================================================= ========= ========== =======================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  1,AbrahamsonSilva1997(): [0]
  1,CampbellBozorgnia2003NSHMP2007(): [1]
  1,SadighEtAl1997(): [2]
  1,YoungsEtAl1997SInterNSHMP2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
==================================================== ====== ==================== ============ ============
source_model                                         grp_id trt                  eff_ruptures tot_ruptures
==================================================== ====== ==================== ============ ============
Alaska_asc_grid_NSHMP2007.xml extra_source_model.xml 1      Active Shallow Crust 368          1,104       
==================================================== ====== ==================== ============ ============

Slowest sources
---------------
========= ================ ============ ========= ========== ========= ========= ======
source_id source_class     num_ruptures calc_time split_time num_sites num_split events
========= ================ ============ ========= ========== ========= ========= ======
2         MultiPointSource 1,104        0.00614   4.699E-04  1.25000   4         0     
1         MultiPointSource 160          0.0       1.643E-04  0.0       0         0     
========= ================ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 0.00614   2     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00325 9.220E-04 0.00182 0.00443 14       
count_eff_ruptures 0.00928 NaN       0.00928 0.00928 1        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=162, duration=0 s, sources="2"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.25000 0.50000 1   2   4
weight   40      7.62153 36  52  4
======== ======= ======= === === =

Slowest task
------------
taskno=1, weight=162, duration=0 s, sources="2"

======== ======= ======= === === =
variable mean    stddev  min max n
======== ======= ======= === === =
nsites   1.25000 0.50000 1   2   4
weight   40      7.62153 36  52  4
======== ======= ======= === === =

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
RtreeFilter        srcs=21.95 KB monitor=4.4 KB srcfilter=3.81 KB                          7.04 KB 
count_eff_ruptures sources=4.04 KB param=1.64 KB gsims=422 B monitor=329 B srcfilter=246 B 359 B   
================== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.23360   0.0       1     
total prefilter                0.04549   1.71094   14    
total count_eff_ruptures       0.00928   6.56641   1     
store source_info              0.00726   0.0       1     
reading composite source model 0.00515   0.0       1     
unpickling prefilter           0.00307   0.0       14    
splitting sources              9.668E-04 0.0       1     
reading site collection        5.791E-04 0.0       1     
unpickling count_eff_ruptures  2.720E-04 0.0       1     
aggregate curves               2.656E-04 0.0       1     
============================== ========= ========= ======