Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     1,369,868,782      
date           2018-06-05T06:39:13
engine_version 3.2.0-git65c4735   
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
VICM      AreaSource   2,430        0.05229   0.01070    3.00000   30        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.05229   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00361 0.00212   0.00113 0.01096 30       
count_eff_ruptures 0.00967 8.317E-04 0.00838 0.01051 8        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=6, weight=168, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   4
weight   42      0.0    42  42  4
======== ======= ====== === === =

Slowest task
------------
taskno=2, weight=168, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   4
weight   42      0.0    42  42  4
======== ======= ====== === === =

Data transfer
-------------
================== ============================================================================== ========
task               sent                                                                           received
RtreeFilter        srcs=39.54 KB monitor=10.14 KB srcfilter=8.17 KB                               42.09 KB
count_eff_ruptures gsims=1.23 MB sources=23.51 KB param=6.56 KB monitor=2.76 KB srcfilter=1.82 KB 2.83 KB 
================== ============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.47386   0.19141   1     
managing sources               0.22836   0.0       1     
total prefilter                0.10832   3.46875   30    
total count_eff_ruptures       0.07738   5.65234   8     
reading composite source model 0.02884   0.0       1     
splitting sources              0.01107   0.0       1     
unpickling prefilter           0.00981   0.0       30    
store source_info              0.00608   0.0       1     
aggregate curves               0.00233   0.0       8     
unpickling count_eff_ruptures  0.00182   0.0       8     
reading site collection        0.00100   0.0       1     
saving probability maps        1.972E-04 0.0       1     
============================== ========= ========= ======