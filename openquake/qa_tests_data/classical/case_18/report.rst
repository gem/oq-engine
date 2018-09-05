Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     1,369,868,782      
date           2018-09-05T10:04:53
engine_version 3.2.0-gitb4ef3a4b6c
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
====== ========================================================================================================================================== ========== ========== ==========
grp_id gsims                                                                                                                                      distances  siteparams ruptparams
====== ========================================================================================================================================== ========== ========== ==========
0      GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5') rhypo rrup            mag       
====== ========================================================================================================================================== ========== ========== ==========

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
VICM      AreaSource   2,430        0.02190   0.00849    3.00000   30        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.02190   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ========= ======= =========
operation-duration   mean    stddev    min       max     num_tasks
pickle_source_models 0.01015 NaN       0.01015   0.01015 1        
count_eff_ruptures   0.00345 9.073E-04 0.00251   0.00501 8        
preprocess           0.00168 3.641E-04 8.891E-04 0.00207 30       
==================== ======= ========= ========= ======= =========

Fastest task
------------
taskno=7, weight=168, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   4
weight   42      0.0    42  42  4
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=168, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   4
weight   42      0.0    42  42  4
======== ======= ====== === === =

Data transfer
-------------
==================== ============================================================================= ========
task                 sent                                                                          received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                          174 B   
count_eff_ruptures   gsims=1.23 MB sources=23.68 KB param=7.15 KB monitor=2.4 KB srcfilter=1.72 KB 2.83 KB 
preprocess           srcs=39.86 KB monitor=9.35 KB srcfilter=7.41 KB param=1.05 KB                 41.5 KB 
==================== ============================================================================= ========

Slowest operations
------------------
========================== ======== ========= ======
operation                  time_sec memory_mb counts
========================== ======== ========= ======
managing sources           0.11863  0.0       1     
total preprocess           0.05025  0.0       30    
total count_eff_ruptures   0.02758  0.0       8     
total pickle_source_models 0.01015  0.0       1     
splitting sources          0.00876  0.0       1     
store source_info          0.00508  0.0       1     
aggregate curves           0.00230  0.0       8     
========================== ======== ========= ======