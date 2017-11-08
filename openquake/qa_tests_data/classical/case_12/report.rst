Classical Hazard QA Test, Case 12
=================================

============== ===================
checksum32     3,041,491,618      
date           2017-11-08T18:07:16
engine_version 2.8.0-gite3d0f56   
============== ===================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1,1)    1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 1           1            1           
source_model.xml 1      Stable Continental   1           1            1           
================ ====== ==================== =========== ============ ============

============= =
#TRT models   2
#sources      2
#eff_ruptures 2
#tot_ruptures 2
#tot_weight   0
============= =

Informational data
------------------
=========================== =============================================================================
count_eff_ruptures.received tot 1.2 KB, max_per_task 615 B                                               
count_eff_ruptures.sent     sources 2.31 KB, srcfilter 1.34 KB, param 1.16 KB, monitor 656 B, gsims 193 B
hazard.input_weight         0.2                                                                          
hazard.n_imts               1                                                                            
hazard.n_levels             3                                                                            
hazard.n_realizations       1                                                                            
hazard.n_sites              1                                                                            
hazard.n_sources            2                                                                            
hazard.output_weight        3.0                                                                          
hostname                    tstation.gem.lan                                                             
require_epsilons            False                                                                        
=========================== =============================================================================

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      1         PointSource  1            1.760E-04 1         1        
1      2         PointSource  1            1.483E-04 1         1        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  3.242E-04 2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.581E-04 1.077E-04 6.819E-04 8.342E-04 2        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
store source_info              0.004     0.0       1     
managing sources               0.002     0.0       1     
reading composite source model 0.002     0.0       1     
total count_eff_ruptures       0.002     0.0       2     
prefiltering source model      7.155E-04 0.0       1     
reading site collection        4.625E-05 0.0       1     
aggregate curves               4.029E-05 0.0       2     
saving probability maps        3.004E-05 0.0       1     
============================== ========= ========= ======