SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     1,302,227,115      
date           2017-11-08T18:07:16
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 1, num_imts = 3

Parameters
----------
=============================== ===========================================
calculation_mode                'classical'                                
number_of_logic_tree_samples    0                                          
maximum_distance                {'default': [(6, 100), (7, 150), (8, 200)]}
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
=============================== ===========================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source                  `simple_area_source_model.xml <simple_area_source_model.xml>`_            
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ====== ====================== ================
smlt_path weight gsim_logic_tree        num_realizations
========= ====== ====================== ================
b1        1.000  complex(4,0,4,5,1,2,0) 4/4             
========= ====== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================== ========== ========== ==============
grp_id gsims                                                                                distances  siteparams ruptparams    
====== ==================================================================================== ========== ========== ==============
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab() rhypo rrup vs30       hypo_depth mag
====== ==================================================================================== ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  4,AtkinsonBoore2003SSlab(): [0]
  4,LinLee2008SSlab(): [1]
  4,YoungsEtAl1997SSlab(): [2]
  4,ZhaoEtAl2006SSlab(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= =========== ============ ============
source_model                 grp_id trt               num_sources eff_ruptures tot_ruptures
============================ ====== ================= =========== ============ ============
simple_area_source_model.xml 4      Subduction Inslab 1           7,770        7,770       
============================ ====== ================= =========== ============ ============

Informational data
------------------
=========================== ==================================================================================
count_eff_ruptures.received tot 14.12 KB, max_per_task 3.64 KB                                                
count_eff_ruptures.sent     sources 76.66 KB, param 5.31 KB, srcfilter 2.74 KB, monitor 1.28 KB, gsims 1.26 KB
hazard.input_weight         777.0                                                                             
hazard.n_imts               3                                                                                 
hazard.n_levels             78                                                                                
hazard.n_realizations       1280                                                                              
hazard.n_sites              1                                                                                 
hazard.n_sources            1                                                                                 
hazard.output_weight        78.0                                                                              
hostname                    tstation.gem.lan                                                                  
require_epsilons            False                                                                             
=========================== ==================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
4      s46       AreaSource   7,770        0.030     1         370      
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.030     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.010 0.003  0.005 0.012 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 4.833     0.0       1     
managing sources               0.099     0.0       1     
total count_eff_ruptures       0.039     0.0       4     
prefiltering source model      0.017     0.0       1     
store source_info              0.014     0.0       1     
aggregate curves               3.843E-04 0.0       4     
reading site collection        4.148E-05 0.0       1     
saving probability maps        2.337E-05 0.0       1     
============================== ========= ========= ======