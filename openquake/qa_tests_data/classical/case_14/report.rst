Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     762,001,888        
date           2018-04-30T11:22:11
engine_version 3.1.0-gitb0812f0   
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
3         SimpleFaultSource 447          8.223E-04 2.263E-04  150       15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 8.223E-04 1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
count_ruptures     0.00267 3.444E-04 0.00200 0.00299 10       
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=6, weight=252, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   NaN    10  10  1
weight   252  NaN    252 252 1
======== ==== ====== === === =

Slowest task
------------
taskno=10, weight=234, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   0.0    10  10  5
weight   46   31     18  101 5
======== ==== ====== === === =

Informational data
------------------
============== ============================================================================== ========
task           sent                                                                           received
count_ruptures sources=13.82 KB srcfilter=11.77 KB param=4.82 KB monitor=3.22 KB gsims=2.3 KB 3.5 KB  
============== ============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.02668   1.32031   10    
managing sources               0.02010   0.0       1     
reading composite source model 0.00763   0.0       1     
store source_info              0.00416   0.0       1     
splitting sources              7.939E-04 0.0       1     
reading site collection        7.656E-04 0.0       1     
unpickling count_ruptures      4.120E-04 0.0       10    
aggregate curves               1.817E-04 0.0       10    
saving probability maps        3.409E-05 0.0       1     
============================== ========= ========= ======