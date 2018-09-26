Event Based Risk SJ
===================

============== ===================
checksum32     2,235,537,411      
date           2018-09-25T14:28:02
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 61, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 50.0}
investigation_time              25.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.3              
area_source_discretization      20.0             
ground_motion_correlation_model 'JB2009'         
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ====================================================================
Name                    File                                                                
======================= ====================================================================
gsim_logic_tree         `Costa_Rica_RESIS_II_gmpe_CQ.xml <Costa_Rica_RESIS_II_gmpe_CQ.xml>`_
job_ini                 `job.ini <job.ini>`_                                                
site_model              `site_model_CR_60.xml <site_model_CR_60.xml>`_                      
source                  `areasource.xml <areasource.xml>`_                                  
source_model_logic_tree `sm_lt.xml <sm_lt.xml>`_                                            
======================= ====================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,0,0)  1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= ========= ========== ===================
grp_id gsims             distances siteparams ruptparams         
====== ================= ========= ========== ===================
0      ZhaoEtAl2006Asc() rrup      vs30       hypo_depth mag rake
====== ================= ========= ========== ===================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ZhaoEtAl2006Asc(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============== ====== ==================== ============ ============
source_model   grp_id trt                  eff_ruptures tot_ruptures
============== ====== ==================== ============ ============
areasource.xml 0      Active Shallow Crust 120          120         
============== ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         A    0     9     120          0.14816   0.17720    389       20        3.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.14816   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.00590 NaN     0.00590 0.00590 1        
split_filter       0.01430 NaN     0.01430 0.01430 1        
build_ruptures     0.01131 0.00293 0.00508 0.01504 20       
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
read_source_models monitor=0 B fnames=0 B converter=0 B                                    2.35 KB 
split_filter       srcs=2.56 KB monitor=432 B srcfilter=220 B sample_factor=21 B seed=14 B 9.42 KB 
build_ruptures     srcs=31.7 KB param=8.5 KB monitor=6.74 KB srcfilter=4.3 KB              39.65 KB
================== ======================================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total build_ruptures     0.22620  0.0       20    
updating source_info     0.02463  0.0       1     
total split_filter       0.01430  0.0       1     
saving ruptures          0.00776  0.0       3     
total read_source_models 0.00590  0.0       1     
store source_info        0.00497  0.0       1     
making contexts          0.00189  0.0       3     
======================== ======== ========= ======