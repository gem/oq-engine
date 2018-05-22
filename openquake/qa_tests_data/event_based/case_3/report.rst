Event Based QA Test, Case 3
===========================

============== ===================
checksum32     2,932,887,546      
date           2018-05-15T04:14:06
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              2.0               
ses_per_logic_tree_path         2                 
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
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
b1        1.00000 simple(2)       2/2             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================== ========= ========== ==========
grp_id gsims                              distances siteparams ruptparams
====== ================================== ========= ========== ==========
0      AkkarBommer2010() SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
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
1         PointSource  1            0.00327   0.0        1         1         7     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00327   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
prefilter          9.708E-04 NaN    9.708E-04 9.708E-04 1        
compute_ruptures   0.00552   NaN    0.00552   0.00552   1        
================== ========= ====== ========= ========= =========

Informational data
------------------
================ ====================================================================== ========
task             sent                                                                   received
prefilter        srcs=0 B srcfilter=0 B monitor=0 B                                     1.29 KB 
compute_ruptures sources=1.34 KB src_filter=717 B param=576 B monitor=330 B gsims=209 B 2.57 KB 
================ ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.02859   0.0       1     
total compute_ruptures         0.00552   2.74219   1     
store source_info              0.00436   0.0       1     
saving ruptures                0.00397   0.0       1     
reading composite source model 0.00308   0.0       1     
setting event years            0.00141   0.0       1     
making contexts                0.00139   0.0       1     
total prefilter                9.708E-04 0.0       1     
splitting sources              5.071E-04 0.0       1     
reading site collection        2.816E-04 0.0       1     
unpickling compute_ruptures    1.869E-04 0.0       1     
unpickling prefilter           1.018E-04 0.0       1     
============================== ========= ========= ======