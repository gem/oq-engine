Classical Tiling for Turkey reduced
===================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7647.hdf5 Wed Apr 26 15:56:37 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 83, sitecol = 5.13 KB

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
======================== ====== ======================================================== ====================== ================
smlt_path                weight source_model_file                                        gsim_logic_tree        num_realizations
======================== ====== ======================================================== ====================== ================
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     complex(2,5,4,4,1,0,4) 4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ complex(2,5,4,4,1,0,4) 4/4             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     complex(2,5,4,4,1,0,4) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
4      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rx rjb rhypo rrup vs30 vs30measured z1pt0 dip hypo_depth ztor rake mag
9      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rx rjb rhypo rrup vs30 vs30measured z1pt0 dip hypo_depth ztor rake mag
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  4,AkkarBommer2010(): ['<0,AreaSource~AkkarBommer2010asc_@_@_@_@_@_@,w=0.24999999893563138>']
  4,CauzziFaccioli2008(): ['<1,AreaSource~CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.24999999893563138>']
  4,ChiouYoungs2008(): ['<2,AreaSource~ChiouYoungs2008asc_@_@_@_@_@_@,w=0.14285714224893223>']
  4,ZhaoEtAl2006Asc(): ['<3,AreaSource~ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.07142857112446611>']
  9,AkkarBommer2010(): ['<4,FaultSourceAndBackground~AkkarBommer2010asc_@_@_@_@_@_@,w=0.10000000106436867>']
  9,CauzziFaccioli2008(): ['<5,FaultSourceAndBackground~CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.10000000106436867>']
  9,ChiouYoungs2008(): ['<6,FaultSourceAndBackground~ChiouYoungs2008asc_@_@_@_@_@_@,w=0.05714285775106781>']
  9,ZhaoEtAl2006Asc(): ['<7,FaultSourceAndBackground~ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.028571428875533905>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ============
source_model              grp_id trt                  num_sources eff_ruptures tot_ruptures
========================= ====== ==================== =========== ============ ============
models/src/as_model.xml   4      Active Shallow Crust 1           3195         3,876       
models/src/fsbg_model.xml 9      Active Shallow Crust 2           1653         2,061       
========================= ====== ==================== =========== ============ ============

============= =====
#TRT models   2    
#sources      3    
#eff_ruptures 4,848
#tot_ruptures 5,937
#tot_weight   593  
============= =====

Informational data
------------------
============================== =================================================================================
count_eff_ruptures.received    tot 7.23 KB, max_per_task 1.81 KB                                                
count_eff_ruptures.sent        sources 47.07 KB, srcfilter 22.07 KB, monitor 6.36 KB, gsims 1.27 KB, param 260 B
hazard.input_weight            593                                                                              
hazard.n_imts                  2 B                                                                              
hazard.n_levels                90 B                                                                             
hazard.n_realizations          3.75 KB                                                                          
hazard.n_sites                 83 B                                                                             
hazard.n_sources               3 B                                                                              
hazard.output_weight           28,684,800                                                                       
hostname                       tstation.gem.lan                                                                 
require_epsilons               0 B                                                                              
============================== =================================================================================

Slowest sources
---------------
====== ============ ============ ============ ========= ========= =========
grp_id source_id    source_class num_ruptures calc_time num_sites num_split
====== ============ ============ ============ ========= ========= =========
4      AS_GEAS343   AreaSource   3,876        0.0       33        0        
9      FSBG_TRBG103 AreaSource   1,755        0.0       16        0        
9      FSBG_ARAS462 AreaSource   306          0.0       4         0        
====== ============ ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       3     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.766 0.406  0.202 1.092 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         3.063     0.0       4     
reading composite source model   0.734     0.0       1     
filtering composite source model 0.084     0.0       1     
reading site collection          0.008     0.0       1     
store source_info                0.001     0.0       1     
aggregate curves                 1.123E-04 0.0       4     
managing sources                 8.011E-05 0.0       1     
saving probability maps          4.292E-05 0.0       1     
================================ ========= ========= ======