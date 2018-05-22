Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     1,369,868,782      
date           2018-05-15T04:13:31
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 3, num_levels = 36

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      50.0              
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
gsim_logic_tree         `nbc_asc_logic_tree.xml <nbc_asc_logic_tree.xml>`_          
job_ini                 `job.ini <job.ini>`_                                        
sites                   `vancouver_school_sites.csv <vancouver_school_sites.csv>`_  
source                  `vancouver_area_source.xml <vancouver_area_source.xml>`_    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(3)       3/3             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================================================================================== ========= ========== ==========
grp_id gsims                                                                                                                                      distances siteparams ruptparams
====== ========================================================================================================================================== ========= ========== ==========
0      GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5') rhypo rjb            mag       
====== ========================================================================================================================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5'): [2]
  0,GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5'): [0]
  0,GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5'): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== ============ ============
source_model              grp_id trt                  eff_ruptures tot_ruptures
========================= ====== ==================== ============ ============
vancouver_area_source.xml 0      Active Shallow Crust 2,430        2,430       
========================= ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
VICM      AreaSource   2,430        6.936E-04 0.01066    90        30        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   6.936E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
prefilter          0.00391 0.00272   0.00114 0.01389 30       
count_ruptures     0.00220 4.623E-04 0.00138 0.00264 8        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=8, weight=84, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   2
weight   42      0.0    42  42  2
======== ======= ====== === === =

Slowest task
------------
taskno=3, weight=168, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   4
weight   42      0.0    42  42  4
======== ======= ====== === === =

Informational data
------------------
============== ============================================================================= ========
task           sent                                                                          received
prefilter      srcs=39.54 KB monitor=9.55 KB srcfilter=6.71 KB                               42.09 KB
count_ruptures gsims=1.23 MB sources=23.51 KB srcfilter=6.45 KB param=6.41 KB monitor=2.6 KB 2.83 KB 
============== ============================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.15559   0.0       1     
total prefilter                0.11732   3.43359   30    
reading composite source model 0.02814   0.0       1     
total count_ruptures           0.01757   1.25000   8     
splitting sources              0.01118   0.0       1     
store source_info              0.00498   0.0       1     
unpickling prefilter           0.00356   0.0       30    
reading site collection        6.022E-04 0.0       1     
unpickling count_ruptures      3.252E-04 0.0       8     
aggregate curves               1.650E-04 0.0       8     
saving probability maps        3.624E-05 0.0       1     
============================== ========= ========= ======