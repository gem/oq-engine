Classical PSHA QA test with sites_csv
=====================================

============== ===================
checksum32     762,001,888        
date           2018-06-05T06:39:12
engine_version 3.2.0-git65c4735   
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
3         SimpleFaultSource 447          0.06558   2.310E-04  10        15        0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.06558   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00661 0.00213 0.00223 0.01103 15       
count_eff_ruptures 0.00862 0.00168 0.00590 0.01024 10       
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=5, weight=347, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   NaN    10  10  1
weight   347  NaN    347 347 1
======== ==== ====== === === =

Slowest task
------------
taskno=3, weight=234, duration=0 s, sources="3"

======== ==== ====== === === =
variable mean stddev min max n
======== ==== ====== === === =
nsites   10   0.0    10  10  5
weight   46   31     18  101 5
======== ==== ====== === === =

Data transfer
-------------
================== ============================================================================ ========
task               sent                                                                         received
RtreeFilter        srcs=15.24 KB monitor=5.07 KB srcfilter=4.09 KB                              17.41 KB
count_eff_ruptures sources=14.2 KB param=5.01 KB monitor=3.45 KB gsims=2.3 KB srcfilter=2.28 KB 3.5 KB  
================== ============================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.35947   0.0       1     
managing sources               0.16389   0.0       1     
total prefilter                0.09921   5.19141   15    
total count_eff_ruptures       0.08622   5.86719   10    
reading composite source model 0.00785   0.0       1     
store source_info              0.00573   0.0       1     
unpickling prefilter           0.00469   0.0       15    
aggregate curves               0.00283   0.0       10    
unpickling count_eff_ruptures  0.00247   0.0       10    
reading site collection        0.00107   0.0       1     
splitting sources              6.094E-04 0.0       1     
saving probability maps        2.129E-04 0.0       1     
============================== ========= ========= ======