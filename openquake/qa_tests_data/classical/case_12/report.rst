Classical Hazard QA Test, Case 12
=================================

============== ===================
checksum32     3,041,491,618      
date           2018-05-15T04:13:35
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 3

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
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rjb rrup  vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =======
#TRT models   2      
#eff_ruptures 2      
#tot_ruptures 2      
#tot_weight   0.20000
============= =======

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  1            5.984E-05 9.298E-06  1         1         0     
2         PointSource  1            5.698E-05 1.431E-06  1         1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  1.168E-04 2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
prefilter          0.00289 2.753E-04 0.00269 0.00308 2        
count_ruptures     0.00214 1.910E-04 0.00200 0.00227 2        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=2, weight=0, duration=0 s, sources="2"

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
============== ====================================================================== ========
task           sent                                                                   received
prefilter      srcs=2.26 KB monitor=652 B srcfilter=458 B                             2.49 KB 
count_ruptures sources=2.58 KB srcfilter=1.4 KB param=824 B monitor=666 B gsims=251 B 716 B   
============== ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.01652   0.0       1     
total prefilter                0.00577   2.43359   2     
total count_ruptures           0.00427   1.37109   2     
reading composite source model 0.00408   0.0       1     
store source_info              0.00388   0.0       1     
splitting sources              4.792E-04 0.0       1     
reading site collection        2.854E-04 0.0       1     
unpickling prefilter           1.643E-04 0.0       2     
unpickling count_ruptures      7.343E-05 0.0       2     
saving probability maps        4.506E-05 0.0       1     
aggregate curves               4.411E-05 0.0       2     
============================== ========= ========= ======