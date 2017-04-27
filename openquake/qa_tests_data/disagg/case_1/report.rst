QA test for disaggregation case_1, taken from the disagg demo
=============================================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7646.hdf5 Wed Apr 26 15:56:34 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 2, sitecol = 863 B

Parameters
----------
=============================== ==================
calculation_mode                'disaggregation'  
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     9000              
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
source_model.xml 0      Active Shallow Crust 4           2236         2,236       
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ==============================================================================
count_eff_ruptures.received    tot 7.15 KB, max_per_task 1.43 KB                                             
count_eff_ruptures.sent        sources 18.66 KB, monitor 6.06 KB, srcfilter 3.48 KB, gsims 490 B, param 325 B
hazard.input_weight            1,418                                                                         
hazard.n_imts                  2 B                                                                           
hazard.n_levels                38 B                                                                          
hazard.n_realizations          1 B                                                                           
hazard.n_sites                 2 B                                                                           
hazard.n_sources               4 B                                                                           
hazard.output_weight           76                                                                            
hostname                       tstation.gem.lan                                                              
require_epsilons               0 B                                                                           
============================== ==============================================================================

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      3         SimpleFaultSource  617          0.0       1         0        
0      4         ComplexFaultSource 164          0.0       1         0        
0      1         PointSource        15           0.0       1         0        
0      2         AreaSource         1,440        0.0       1         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.0       1     
ComplexFaultSource 0.0       1     
PointSource        0.0       1     
SimpleFaultSource  0.0       1     
================== ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.236 0.227  0.104 0.640 5        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         1.182     0.0       5     
reading composite source model   0.035     0.0       1     
filtering composite source model 0.004     0.0       1     
store source_info                0.001     0.0       1     
managing sources                 1.144E-04 0.0       1     
aggregate curves                 6.914E-05 0.0       5     
saving probability maps          5.364E-05 0.0       1     
reading site collection          4.792E-05 0.0       1     
================================ ========= ========= ======