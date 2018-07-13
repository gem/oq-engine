Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     762,001,888        
date           2018-06-26T14:57:47
engine_version 3.2.0-gitb0cd949   
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
3         SimpleFaultSource 447          0.06393   2.196E-04  10        15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.06393   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00864 0.00176 0.00566 0.01077 15       
count_eff_ruptures 0.00853 0.00154 0.00635 0.01012 10       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=7, weight=252, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   NaN    10  10  1
weight   252  NaN    252 252 1
======== ==== ====== === === =

Slowest task
------------
taskno=2, weight=347, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   NaN    10  10  1
weight   347  NaN    347 347 1
======== ==== ====== === === =

Data transfer
-------------
================== =========================================================================== ========
task               sent                                                                        received
RtreeFilter        srcs=15.24 KB monitor=4.72 KB srcfilter=4.09 KB                             17.41 KB
count_eff_ruptures sources=14.2 KB param=5.01 KB monitor=3.21 KB srcfilter=2.4 KB gsims=2.3 KB 3.5 KB  
================== =========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.27843   0.0       1     
total prefilter                0.12953   4.74219   15    
total count_eff_ruptures       0.08526   6.50391   10    
store source_info              0.00645   0.0       1     
reading composite source model 0.00590   0.0       1     
unpickling prefilter           0.00456   0.0       15    
aggregate curves               0.00327   0.0       10    
unpickling count_eff_ruptures  0.00268   0.0       10    
splitting sources              5.145E-04 0.0       1     
reading site collection        5.052E-04 0.0       1     
============================== ========= ========= ======