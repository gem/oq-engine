SHARE OpenQuake Computational Settings
======================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7616.hdf5 Wed Apr 26 15:55:46 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

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
========= ====== ============================================================== ====================== ================
smlt_path weight source_model_file                                              gsim_logic_tree        num_realizations
========= ====== ============================================================== ====================== ================
b1        1.000  `simple_area_source_model.xml <simple_area_source_model.xml>`_ complex(4,2,4,5,0,1,0) 4/4             
========= ====== ============================================================== ====================== ================

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
  4,AtkinsonBoore2003SSlab(): ['<0,b1~@_@_@_@_b51_@_@,w=0.2>']
  4,LinLee2008SSlab(): ['<1,b1~@_@_@_@_b52_@_@,w=0.2>']
  4,YoungsEtAl1997SSlab(): ['<2,b1~@_@_@_@_b53_@_@,w=0.2>']
  4,ZhaoEtAl2006SSlab(): ['<3,b1~@_@_@_@_b54_@_@,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= =========== ============ ============
source_model                 grp_id trt               num_sources eff_ruptures tot_ruptures
============================ ====== ================= =========== ============ ============
simple_area_source_model.xml 4      Subduction Inslab 1           5161         7,770       
============================ ====== ================= =========== ============ ============

Informational data
------------------
============================== =================================================================================
count_eff_ruptures.received    tot 7.44 KB, max_per_task 1.86 KB                                                
count_eff_ruptures.sent        sources 118.84 KB, monitor 6.57 KB, srcfilter 3.02 KB, gsims 1.26 KB, param 260 B
hazard.input_weight            777                                                                              
hazard.n_imts                  3 B                                                                              
hazard.n_levels                78 B                                                                             
hazard.n_realizations          1.25 KB                                                                          
hazard.n_sites                 1 B                                                                              
hazard.n_sources               1 B                                                                              
hazard.output_weight           99,840                                                                           
hostname                       tstation.gem.lan                                                                 
require_epsilons               0 B                                                                              
============================== =================================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
4      s46       AreaSource   7,770        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 1.240 0.136  1.037 1.316 4        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         4.959     2.055     4     
reading composite source model   4.364     0.0       1     
filtering composite source model 0.016     0.0       1     
store source_info                0.001     0.0       1     
managing sources                 1.009E-04 0.0       1     
aggregate curves                 8.750E-05 0.0       4     
saving probability maps          4.363E-05 0.0       1     
reading site collection          3.338E-05 0.0       1     
================================ ========= ========= ======