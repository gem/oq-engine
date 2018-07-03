Demo Classical PSHA for Vancouver Schools
=========================================

============== ===================
checksum32     1,369,868,782      
date           2018-06-26T14:57:48
engine_version 3.2.0-gitb0cd949   
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
VICM      AreaSource   2,430        0.05959   0.01042    3.00000   30        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.05959   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00308 0.00154   0.00104 0.00585 30       
count_eff_ruptures 0.01101 4.281E-04 0.01029 0.01158 8        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=4, weight=168, duration=0 s, sources="VICM"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   3.00000 0.0    3   3   4
weight   42      0.0    42  42  4
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

Data transfer
-------------
================== ============================================================================== ========
task               sent                                                                           received
RtreeFilter        srcs=39.54 KB monitor=9.43 KB srcfilter=8.17 KB                                42.09 KB
count_eff_ruptures gsims=1.23 MB sources=23.51 KB param=6.56 KB monitor=2.57 KB srcfilter=1.92 KB 2.83 KB 
================== ============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.33439   0.0       1     
total prefilter                0.09232   3.15625   30    
total count_eff_ruptures       0.08810   6.33594   8     
reading composite source model 0.02691   0.0       1     
splitting sources              0.01076   0.0       1     
unpickling prefilter           0.01018   0.0       30    
store source_info              0.00706   0.0       1     
aggregate curves               0.00259   0.0       8     
unpickling count_eff_ruptures  0.00209   0.0       8     
reading site collection        4.916E-04 0.0       1     
============================== ========= ========= ======