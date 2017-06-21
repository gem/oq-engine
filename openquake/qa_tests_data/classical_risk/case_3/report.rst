Classical PSHA - Loss fractions QA test
=======================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_29169.hdf5 Wed Jun 14 10:03:45 2017
engine_version                                   2.5.0-gite200a20        
================================================ ========================

num_sites = 12, num_imts = 1

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
source_model.xml 0      Active Shallow Crust 2           2132         2,132       
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== =============================================================================
count_eff_ruptures.received    tot 1.14 KB, max_per_task 585 B                                              
count_eff_ruptures.sent        sources 3.72 KB, srcfilter 1.94 KB, param 1.47 KB, monitor 626 B, gsims 196 B
hazard.input_weight            213                                                                          
hazard.n_imts                  1 B                                                                          
hazard.n_levels                19 B                                                                         
hazard.n_realizations          1 B                                                                          
hazard.n_sites                 12 B                                                                         
hazard.n_sources               2 B                                                                          
hazard.output_weight           228                                                                          
hostname                       tstation.gem.lan                                                             
require_epsilons               1 B                                                                          
============================== =============================================================================

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
0      225       AreaSource   520          0.003     3         1        
0      232       AreaSource   1,612        0.003     10        1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.006     2     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.005 1.716E-04 0.005 0.005 2        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.067     0.0       1     
total count_eff_ruptures       0.010     3.750     2     
prefiltering source model      0.009     0.359     1     
reading exposure               0.006     0.0       1     
store source_info              0.003     0.0       1     
managing sources               0.002     0.0       1     
aggregate curves               4.196E-05 0.0       2     
saving probability maps        2.408E-05 0.0       1     
reading site collection        6.437E-06 0.0       1     
============================== ========= ========= ======