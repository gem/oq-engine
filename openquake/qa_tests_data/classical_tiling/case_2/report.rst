Classical Tiling for Turkey reduced
===================================

============== ===================
checksum32     1,556,025,092      
date           2017-11-08T18:08:06
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 83, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              10.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                0.1               
area_source_discretization      25.0              
ground_motion_correlation_model None              
random_seed                     323               
master_seed                     0                 
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                      
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `as_model.xml <as_model.xml>`_                                            
source                   `fsbg_model.xml <fsbg_model.xml>`_                                        
source                   `ss_model.xml <ss_model.xml>`_                                            
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
======================== ====== ====================== ================
smlt_path                weight gsim_logic_tree        num_realizations
======================== ====== ====================== ================
AreaSource               0.500  complex(2,4,4,1,5,4,0) 4/4             
FaultSourceAndBackground 0.200  complex(2,4,4,1,5,4,0) 4/4             
SeiFaCrust               0.300  complex(2,4,4,1,5,4,0) 0/0             
======================== ====== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
4      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
9      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  4,AkkarBommer2010(): [0]
  4,CauzziFaccioli2008(): [1]
  4,ChiouYoungs2008(): [2]
  4,ZhaoEtAl2006Asc(): [3]
  9,AkkarBommer2010(): [4]
  9,CauzziFaccioli2008(): [5]
  9,ChiouYoungs2008(): [6]
  9,ZhaoEtAl2006Asc(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ============
source_model              grp_id trt                  num_sources eff_ruptures tot_ruptures
========================= ====== ==================== =========== ============ ============
models/src/as_model.xml   4      Active Shallow Crust 1           34,884       3,876       
models/src/fsbg_model.xml 9      Active Shallow Crust 2           7,632        2,061       
========================= ====== ==================== =========== ============ ============

============= ======
#TRT models   2     
#sources      3     
#eff_ruptures 42,516
#tot_ruptures 5,937 
#tot_weight   0     
============= ======

Informational data
------------------
=========================== =================================================================================
count_eff_ruptures.received tot 9.74 KB, max_per_task 630 B                                                  
count_eff_ruptures.sent     sources 48.49 KB, param 21.39 KB, srcfilter 21 KB, monitor 5.12 KB, gsims 5.08 KB
hazard.input_weight         15721.2                                                                          
hazard.n_imts               2                                                                                
hazard.n_levels             90                                                                               
hazard.n_realizations       3840                                                                             
hazard.n_sites              83                                                                               
hazard.n_sources            3                                                                                
hazard.output_weight        7470.0                                                                           
hostname                    tstation.gem.lan                                                                 
require_epsilons            False                                                                            
=========================== =================================================================================

Slowest sources
---------------
====== ============ ============ ============ ========= ========= =========
grp_id source_id    source_class num_ruptures calc_time num_sites num_split
====== ============ ============ ============ ========= ========= =========
4      AS_GEAS343   AreaSource   3,876        0.026     7         9        
9      FSBG_TRBG103 AreaSource   1,755        0.011     5         4        
9      FSBG_ARAS462 AreaSource   306          0.003     3         2        
====== ============ ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.040     3     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.003 5.613E-04 0.002 0.004 16       
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.660     0.0       1     
prefiltering source model      0.117     0.0       10    
store source_info              0.058     0.0       1     
total count_eff_ruptures       0.056     0.156     16    
managing sources               0.054     0.0       1     
reading site collection        0.005     0.0       1     
aggregate curves               2.389E-04 0.0       16    
saving probability maps        3.767E-05 0.0       1     
============================== ========= ========= ======