Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     1,591,568,041      
date           2018-09-05T10:04:36
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 10, num_levels = 13

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
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
reqv                    `lookup.hdf5 <lookup.hdf5>`_                                
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source                  `simple_fault.xml <simple_fault.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============ ======= =============== ================
smlt_path    weight  gsim_logic_tree num_realizations
============ ======= =============== ================
simple_fault 1.00000 simple(2)       2/2             
============ ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================= =========== ============================= =======================
grp_id gsims                                         distances   siteparams                    ruptparams             
====== ============================================= =========== ============================= =======================
0      AbrahamsonSilva2008() CampbellBozorgnia2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake width ztor
====== ============================================= =========== ============================= =======================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AbrahamsonSilva2008(): [0]
  0,CampbellBozorgnia2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
simple_fault.xml 0      Active Shallow Crust 447          447         
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
3         SimpleFaultSource 447          0.03568   1.502E-04  10        15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.03568   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ======= ======= ======= =========
operation-duration   mean    stddev  min     max     num_tasks
pickle_source_models 0.00380 NaN     0.00380 0.00380 1        
count_eff_ruptures   0.00429 0.00117 0.00243 0.00542 10       
preprocess           0.00416 0.00120 0.00189 0.00544 14       
==================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=10, weight=271, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   0.0    10  10  2
weight   135  49     101 170 2
======== ==== ====== === === =

Slowest task
------------
taskno=5, weight=347, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   NaN    10  10  1
weight   347  NaN    347 347 1
======== ==== ====== === === =

Data transfer
-------------
==================== ========================================================================== ========
task                 sent                                                                       received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                       156 B   
count_eff_ruptures   param=1.08 MB sources=14.13 KB monitor=3 KB gsims=2.3 KB srcfilter=2.15 KB 3.5 KB  
preprocess           srcs=14.54 KB monitor=4.36 KB srcfilter=3.46 KB param=504 B                16.21 KB
==================== ========================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           0.05823   0.49219   14    
managing sources           0.05434   0.0       1     
total count_eff_ruptures   0.04288   0.0       10    
store source_info          0.00397   0.0       1     
total pickle_source_models 0.00380   0.0       1     
aggregate curves           0.00203   0.0       10    
splitting sources          3.991E-04 0.0       1     
========================== ========= ========= ======