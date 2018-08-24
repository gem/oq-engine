Event-Based Hazard QA Test, Case 2
==================================

============== ===================
checksum32     3,954,449,156      
date           2018-06-26T14:58:07
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         600               
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.001             
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
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
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
source_model.xml 0      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  3,000        4.63544   0.0        1.00000   1         3     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  4.63544   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
RtreeFilter        0.00415 NaN    0.00415 0.00415 1        
compute_hazard     4.64495 NaN    4.64495 4.64495 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
============== ============================================================================================ ========
task           sent                                                                                         received
RtreeFilter    srcs=0 B srcfilter=0 B monitor=0 B                                                           13.02 KB
compute_hazard sources_or_ruptures=13.05 KB param=2.32 KB monitor=323 B rlzs_by_gsim=290 B src_filter=246 B 4.33 KB 
============== ============================================================================================ ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               4.68452   0.0       1     
total compute_hazard           4.64495   7.65234   1     
building ruptures              4.64144   6.92578   1     
store source_info              0.00831   0.0       1     
saving ruptures                0.00762   0.0       1     
reading composite source model 0.00549   0.0       1     
total prefilter                0.00415   0.0       1     
saving gmfs                    0.00356   0.0       1     
saving gmf_data/indices        0.00246   0.0       1     
unpickling compute_hazard      8.585E-04 0.0       1     
making contexts                8.302E-04 0.0       3     
building hazard                6.635E-04 0.0       1     
aggregating hcurves            4.196E-04 0.0       1     
GmfGetter.init                 2.935E-04 0.0       1     
reading site collection        2.851E-04 0.0       1     
unpickling prefilter           2.558E-04 0.0       1     
splitting sources              2.170E-04 0.0       1     
building hazard curves         1.047E-04 0.0       1     
============================== ========= ========= ======