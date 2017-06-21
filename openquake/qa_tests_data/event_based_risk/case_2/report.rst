Event Based Risk QA Test 2
==========================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29207.hdf5 Wed Jun 14 10:03:55 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 3, num_imts = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              50.0              
ses_per_logic_tree_path         20                
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
exposure                 `exposure.xml <exposure.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job.ini <job.ini>`_                                          
source                   `source_model.xml <source_model.xml>`_                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

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
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
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
source_model.xml 0      Active Shallow Crust 3           18           18          
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================ =========================================================================
compute_ruptures.received    max_per_task 8.69 KB, tot 8.69 KB                                        
compute_ruptures.sent        sources 2.14 KB, param 841 B, src_filter 740 B, monitor 311 B, gsims 98 B
hazard.input_weight          1.800                                                                    
hazard.n_imts                3 B                                                                      
hazard.n_levels              15 B                                                                     
hazard.n_realizations        1 B                                                                      
hazard.n_sites               3 B                                                                      
hazard.n_sources             3 B                                                                      
hazard.output_weight         45                                                                       
hostname                     tstation.gem.lan                                                         
require_epsilons             1 B                                                                      
============================ =========================================================================

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 50 tasks = 3.12 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC+      1.000 NaN    1   1   1         1         
RM       1.000 0.0    1   1   2         2         
W/1      1.000 NaN    1   1   1         1         
*ALL*    1.333 0.577  1   2   3         4         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      3         PointSource  6            0.0       1         0        
0      2         PointSource  6            0.0       1         0        
0      1         PointSource  6            0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       3     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.020 NaN    0.020 0.020 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.020     0.449     1     
reading exposure               0.007     0.0       1     
assoc_assets_sites             0.006     0.0       1     
filtering ruptures             0.004     0.0       9     
store source_info              0.004     0.0       1     
saving ruptures                0.003     0.0       1     
reading composite source model 0.003     0.0       1     
setting event years            0.001     0.0       1     
managing sources               0.001     0.0       1     
prefiltering source model      7.300E-04 0.0       1     
reading site collection        4.983E-05 0.0       1     
============================== ========= ========= ======