Classical Hazard QA Test, Case 8
================================

============== ===================
checksum32     4,079,887,042      
date           2019-01-20T07:39:25
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                0.001             
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
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1_b2     0.30000 trivial(1)      1/1             
b1_b3     0.30000 trivial(1)      1/1             
b1_b4     0.40000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
2      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]
  2,SadighEtAl1997(): [2]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
source_model.xml 1      Active Shallow Crust 3,000        3,000       
source_model.xml 2      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   900  
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     3,000        0.0       1.931E-05  0.0       1         0.0   
1      1         P    1     2     3,000        0.0       5.722E-06  0.0       1         0.0   
2      1         P    2     3     3,000        0.0       4.530E-06  0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       3     
==== ========= ======

Duplicated sources
------------------
['1']
Found 1 source(s) with the same ID and 1 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00454 1.664E-04 0.00439 0.00472 3      
split_filter       0.01210 NaN       0.01210 0.01210 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=1.14 KB fnames=318 B         4.59 KB 
split_filter       srcs=1.76 KB srcfilter=253 B seed=14 B 1.96 KB 
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.01362  0.50781   3     
total split_filter       0.01210  1.98828   1     
======================== ======== ========= ======