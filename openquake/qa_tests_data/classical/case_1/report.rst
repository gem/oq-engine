Classical Hazard QA Test, Case 1
================================

============== ===================
checksum32     490,180,455        
date           2017-12-06T11:20:29
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 1, num_imts = 2

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
random_seed                     1066              
master_seed                     0                 
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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

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
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Informational data
------------------
======================= ========================================================================
count_ruptures.received max_per_task 588 B, tot 588 B                                           
count_ruptures.sent     sources 1.15 KB, srcfilter 684 B, param 513 B, monitor 319 B, gsims 91 B
hazard.input_weight     0.1                                                                     
hazard.n_imts           2                                                                       
hazard.n_levels         6                                                                       
hazard.n_realizations   1                                                                       
hazard.n_sites          1                                                                       
hazard.n_sources        1                                                                       
hazard.output_weight    6.0                                                                     
hostname                tstation.gem.lan                                                        
require_epsilons        False                                                                   
======================= ========================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         PointSource  1            1.593E-04 1         1        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  1.593E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
count_ruptures     7.930E-04 NaN    7.930E-04 7.930E-04 1        
================== ========= ====== ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
store source_info              0.003     0.0       1     
managing sources               0.002     0.0       1     
reading composite source model 0.001     0.0       1     
total count_ruptures           7.930E-04 0.0       1     
reading site collection        3.457E-05 0.0       1     
saving probability maps        2.337E-05 0.0       1     
aggregate curves               1.216E-05 0.0       1     
============================== ========= ========= ======