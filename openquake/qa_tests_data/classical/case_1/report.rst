Classical Hazard QA Test, Case 1
================================

============== ===================
checksum32     1,984,592,463      
date           2018-05-15T04:13:50
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 6

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job.ini <job.ini>`_                        
source          `source_model.xml <source_model.xml>`_      
source_model    `source_model.xml <source_model.xml>`_      
=============== ============================================

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
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  1            5.054E-05 8.106E-06  1         1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  5.054E-05 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
prefilter          8.321E-04 NaN    8.321E-04 8.321E-04 1        
count_ruptures     0.0       NaN    0.0       0.0       1        
================== ========= ====== ========= ========= =========

Fastest task
------------
taskno=1, weight=0, duration=0 s, sources="1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   0.10000 NaN    0.10000 0.10000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=1, weight=0, duration=0 s, sources="1"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   0.10000 NaN    0.10000 0.10000 1
======== ======= ====== ======= ======= =

Informational data
------------------
============== ===================================================================== ========
task           sent                                                                  received
prefilter      srcs=0 B srcfilter=0 B monitor=0 B                                    1.24 KB 
count_ruptures sources=1.29 KB srcfilter=717 B monitor=564 B param=507 B gsims=120 B 358 B   
============== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.00809   0.0       1     
store source_info              0.00385   0.0       1     
reading composite source model 0.00223   0.0       1     
total count_ruptures           0.00177   0.83203   1     
total prefilter                8.321E-04 0.0       1     
splitting sources              4.289E-04 0.0       1     
reading site collection        2.508E-04 0.0       1     
unpickling prefilter           1.161E-04 0.0       1     
unpickling count_ruptures      3.242E-05 0.0       1     
saving probability maps        2.837E-05 0.0       1     
aggregate curves               2.241E-05 0.0       1     
============================== ========= ========= ======