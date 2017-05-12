Classical PSHA - Loss fractions QA test
=======================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7544.hdf5 Wed Apr 26 15:54:15 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 12, sitecol = 1.37 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
avg_losses                      False             
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
0      ChiouYoungs2008() rjb rx rrup vs30 vs30measured z1pt0 dip rake ztor mag
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
source_model.xml 0      Active Shallow Crust 2           1613         2,132       
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ==============================================================================
count_eff_ruptures.received    tot 2.4 KB, max_per_task 1.2 KB                                               
count_eff_ruptures.sent        sources 12.22 KB, monitor 1.96 KB, srcfilter 1.94 KB, gsims 196 B, param 130 B
hazard.input_weight            213                                                                           
hazard.n_imts                  1 B                                                                           
hazard.n_levels                19 B                                                                          
hazard.n_realizations          1 B                                                                           
hazard.n_sites                 12 B                                                                          
hazard.n_sources               2 B                                                                           
hazard.output_weight           228                                                                           
hostname                       tstation.gem.lan                                                              
require_epsilons               1 B                                                                           
============================== ==============================================================================

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   4         4         
DS       2.000 NaN    2   2   1         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.083 0.289  1   2   12        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      225       AreaSource   520          0.0       3         0        
0      232       AreaSource   1,612        0.0       10        0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.594 0.410  0.304 0.884 2        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         1.188     4.281     2     
reading composite source model   0.910     0.0       1     
filtering composite source model 0.008     0.0       1     
building site collection         0.004     0.0       1     
reading exposure                 0.003     0.0       1     
store source_info                0.001     0.0       1     
managing sources                 1.826E-04 0.0       1     
aggregate curves                 8.297E-05 0.0       2     
saving probability maps          5.388E-05 0.0       1     
reading site collection          1.001E-05 0.0       1     
================================ ========= ========= ======