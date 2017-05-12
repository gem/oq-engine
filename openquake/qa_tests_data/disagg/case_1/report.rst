QA test for disaggregation case_1, taken from the disagg demo
=============================================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21371.hdf5 Fri May 12 10:46:44 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

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
source_model.xml 0      Active Shallow Crust 4           2236         2,236       
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== =============================================================================
count_eff_ruptures.received    tot 4.36 KB, max_per_task 1.47 KB                                            
count_eff_ruptures.sent        sources 4.37 KB, monitor 3.64 KB, srcfilter 2.09 KB, gsims 294 B, param 195 B
hazard.input_weight            1,418                                                                        
hazard.n_imts                  2 B                                                                          
hazard.n_levels                38 B                                                                         
hazard.n_realizations          1 B                                                                          
hazard.n_sites                 2 B                                                                          
hazard.n_sources               4 B                                                                          
hazard.output_weight           76                                                                           
hostname                       tstation.gem.lan                                                             
require_epsilons               0 B                                                                          
============================== =============================================================================

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      3         SimpleFaultSource  617          0.003     1         1        
0      2         AreaSource         1,440        0.002     1         1        
0      4         ComplexFaultSource 164          0.002     1         1        
0      1         PointSource        15           3.116E-04 1         1        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.002     1     
ComplexFaultSource 0.002     1     
PointSource        3.116E-04 1     
SimpleFaultSource  0.003     1     
================== ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.003 9.272E-04 0.002 0.004 3        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.028     0.0       1     
total count_eff_ruptures         0.009     0.0       3     
managing sources                 0.002     0.0       1     
store source_info                4.930E-04 0.0       1     
aggregate curves                 5.317E-05 0.0       3     
filtering composite source model 4.101E-05 0.0       1     
reading site collection          3.314E-05 0.0       1     
saving probability maps          2.408E-05 0.0       1     
================================ ========= ========= ======