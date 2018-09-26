Event Based from NonParametric source
=====================================

============== ===================
checksum32     4,272,018,576      
date           2018-09-25T14:28:01
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 3, num_levels = 7

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      20.0              
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3            4           
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         N    0     420   4            0.02246   1.895E-04  9.00000   3         4.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.02246   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.05353 NaN     0.05353 0.05353 1        
split_filter       0.00571 NaN     0.00571 0.00571 1        
build_ruptures     0.01212 0.00177 0.01012 0.01345 3        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
read_source_models monitor=0 B fnames=0 B converter=0 B                                    14.88 KB
split_filter       srcs=14.6 KB monitor=432 B srcfilter=220 B sample_factor=21 B seed=14 B 13.29 KB
build_ruptures     srcs=14.82 KB monitor=1.01 KB param=885 B srcfilter=660 B               29.97 KB
================== ======================================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.05353  0.0       1     
total build_ruptures     0.03637  0.0       3     
making contexts          0.02086  0.0       3     
updating source_info     0.01202  0.0       1     
saving ruptures          0.00839  0.0       3     
total split_filter       0.00571  0.48828   1     
store source_info        0.00463  0.0       1     
======================== ======== ========= ======