Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     949,605,442        
date           2017-11-08T18:06:29
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 7, num_imts = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
random_seed                     42                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
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
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           1,694        1,694       
================ ====== ==================== =========== ============ ============

Informational data
------------------
=========================== ====================================================================================
count_eff_ruptures.received tot 8.47 KB, max_per_task 649 B                                                     
count_eff_ruptures.sent     sources 14.76 KB, param 12.43 KB, srcfilter 11.65 KB, monitor 4.48 KB, gsims 1.24 KB
hazard.input_weight         11858.0                                                                             
hazard.n_imts               3                                                                                   
hazard.n_levels             25                                                                                  
hazard.n_realizations       1                                                                                   
hazard.n_sites              7                                                                                   
hazard.n_sources            1                                                                                   
hazard.output_weight        175.0                                                                               
hostname                    tstation.gem.lan                                                                    
require_epsilons            False                                                                               
=========================== ====================================================================================

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Concrete 1.000 0.0    1   1   2         2         
Steel    1.000 0.0    1   1   2         2         
Wood     1.000 0.0    1   1   3         3         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ================= ============ ========= ========= =========
grp_id source_id source_class      num_ruptures calc_time num_sites num_split
====== ========= ================= ============ ========= ========= =========
0      1         SimpleFaultSource 1,694        0.043     7         15       
====== ========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.043     1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.004 0.001  0.002 0.007 14       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.108     0.0       1     
total count_eff_ruptures       0.052     0.0       14    
reading exposure               0.008     0.0       1     
reading composite source model 0.007     0.0       1     
store source_info              0.005     0.0       1     
prefiltering source model      0.002     0.0       1     
aggregate curves               3.650E-04 0.0       14    
saving probability maps        4.673E-05 0.0       1     
reading site collection        6.676E-06 0.0       1     
============================== ========= ========= ======