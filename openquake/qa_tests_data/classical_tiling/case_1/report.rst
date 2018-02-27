Classical PSHA using Area Source
================================

============== ===================
checksum32     1,205,782,117      
date           2018-02-25T06:44:32
engine_version 2.10.0-git1f7c0c0  
============== ===================

num_sites = 6, num_levels = 57

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
width_of_mfd_bin                0.2               
area_source_discretization      5.0               
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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  simple(2)       2/2             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1,640        1,640       
================ ====== ==================== ============ ============

Informational data
------------------
======================= ====================================================================================
count_ruptures.received tot 9.64 KB, max_per_task 823 B                                                     
count_ruptures.sent     sources 259.03 KB, param 11.75 KB, srcfilter 8.46 KB, monitor 3.87 KB, gsims 2.58 KB
hazard.input_weight     164.0                                                                               
hazard.n_imts           3                                                                                   
hazard.n_levels         57                                                                                  
hazard.n_realizations   2                                                                                   
hazard.n_sites          6                                                                                   
hazard.n_sources        1                                                                                   
hazard.output_weight    684.0                                                                               
hostname                tstation.gem.lan                                                                    
require_epsilons        False                                                                               
======================= ====================================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   1,640        0.192     1,231     1,230    
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.192     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.024 0.008  0.012 0.038 12       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.287     0.0       12    
managing sources               0.135     0.0       1     
reading composite source model 0.074     0.0       1     
store source_info              0.005     0.0       1     
reading site collection        0.002     0.0       1     
aggregate curves               3.192E-04 0.0       12    
saving probability maps        4.268E-05 0.0       1     
============================== ========= ========= ======