Classical Hazard QA Test, Case 11
=================================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_7609.hdf5 Wed Apr 26 15:55:35 2017
engine_version                                  2.4.0-git9336bd0        
hazardlib_version                               0.24.0-gita895d4c       
=============================================== ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     1066              
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `-0.5 <-0.5>`_                                              
source                  `0.0 <0.0>`_                                                
source                  `0.5 <0.5>`_                                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1_b2     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.600  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
2      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): ['<0,b1_b2~b1,w=0.19999999701976784>']
  1,SadighEtAl1997(): ['<1,b1_b3~b1,w=0.6000000059604643>']
  2,SadighEtAl1997(): ['<2,b1_b4~b1,w=0.19999999701976784>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           3500         3,500       
source_model.xml 1      Active Shallow Crust 1           3000         3,000       
source_model.xml 2      Active Shallow Crust 1           2500         2,500       
================ ====== ==================== =========== ============ ============

============= =====
#TRT models   3    
#sources      3    
#eff_ruptures 9,000
#tot_ruptures 9,000
#tot_weight   900  
============= =====

Informational data
------------------
============================== ===========================================================================
count_eff_ruptures.received    tot 3.17 KB, max_per_task 1.06 KB                                          
count_eff_ruptures.sent        sources 39.07 KB, monitor 2.52 KB, srcfilter 2 KB, gsims 273 B, param 195 B
hazard.input_weight            900                                                                        
hazard.n_imts                  1 B                                                                        
hazard.n_levels                4 B                                                                        
hazard.n_realizations          3 B                                                                        
hazard.n_sites                 1 B                                                                        
hazard.n_sources               3 B                                                                        
hazard.output_weight           12                                                                         
hostname                       tstation.gem.lan                                                           
require_epsilons               0 B                                                                        
============================== ===========================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      1         PointSource  3,000        0.0       1         0        
2      1         PointSource  2,500        0.0       1         0        
0      1         PointSource  3,500        0.0       1         0        
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
count_eff_ruptures 1.735 0.248  1.485 1.982 3        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total count_eff_ruptures         5.206     0.0       3     
reading composite source model   0.019     0.0       1     
filtering composite source model 0.017     0.0       1     
store source_info                0.001     0.0       1     
managing sources                 1.063E-04 0.0       1     
aggregate curves                 9.179E-05 0.0       3     
reading site collection          4.983E-05 0.0       1     
saving probability maps          4.864E-05 0.0       1     
================================ ========= ========= ======