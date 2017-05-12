QA test for blocksize independence (hazard)
===========================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_20459.hdf5 Fri May 12 06:37:29 2017
engine_version                                   2.4.0-giteadb85d        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 2, sitecol = 863 B

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.5               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     42                
master_seed                     0                 
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
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rrup rx rjb vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 9           3            22,406      
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================ ========================================================================
compute_ruptures.received    tot 4.57 KB, max_per_task 4.57 KB                                       
compute_ruptures.sent        sources 96.6 KB, monitor 858 B, src_filter 712 B, gsims 98 B, param 66 B
hazard.input_weight          2,241                                                                   
hazard.n_imts                1 B                                                                     
hazard.n_levels              4 B                                                                     
hazard.n_realizations        1 B                                                                     
hazard.n_sites               2 B                                                                     
hazard.n_sources             9 B                                                                     
hazard.output_weight         0.100                                                                   
hostname                     tstation.gem.lan                                                        
require_epsilons             0 B                                                                     
============================ ========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      4         AreaSource   1,077        0.0       0         0        
0      3         AreaSource   1,760        0.0       0         0        
0      2         AreaSource   2,334        0.0       0         0        
0      5         AreaSource   2,092        0.0       0         0        
0      7         AreaSource   4,144        0.0       0         0        
0      1         AreaSource   7,020        0.0       0         0        
0      8         AreaSource   1,812        0.0       0         0        
0      9         AreaSource   897          0.0       0         0        
0      6         AreaSource   1,270        0.0       0         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       9     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   2.513 NaN    2.513 2.513 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_ruptures           2.513     0.0       1     
reading composite source model   1.465     0.0       1     
saving ruptures                  0.006     0.0       1     
setting event years              0.002     0.0       1     
managing sources                 0.002     0.0       1     
store source_info                0.001     0.0       1     
filtering ruptures               6.292E-04 0.0       3     
reading site collection          4.220E-05 0.0       1     
filtering composite source model 2.575E-05 0.0       1     
================================ ========= ========= ======