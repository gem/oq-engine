Classical Hazard QA Test, Case 10
=================================

============== ===================
checksum32     873,192,949        
date           2017-12-06T11:19:56
engine_version 2.9.0-gite55e76e   
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1_b2     0.500  trivial(1)      1/1             
b1_b3     0.500  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
source_model.xml 1      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 6,000
#tot_ruptures 6,000
#tot_weight   0    
============= =====

Informational data
------------------
======================= ===========================================================================
count_ruptures.received tot 1.15 KB, max_per_task 589 B                                            
count_ruptures.sent     sources 2.33 KB, srcfilter 1.34 KB, param 852 B, monitor 638 B, gsims 182 B
hazard.input_weight     600.0                                                                      
hazard.n_imts           1                                                                          
hazard.n_levels         4                                                                          
hazard.n_realizations   2                                                                          
hazard.n_sites          1                                                                          
hazard.n_sources        2                                                                          
hazard.output_weight    4.0                                                                        
hostname                tstation.gem.lan                                                           
require_epsilons        False                                                                      
======================= ===========================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         PointSource  3,000        3.443E-04 1         2        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  3.443E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ========= ========= ===== =========
operation-duration mean      stddev    min       max   num_tasks
count_ruptures     8.098E-04 2.746E-04 6.156E-04 0.001 2        
================== ========= ========= ========= ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.014     0.0       1     
managing sources               0.011     0.0       1     
store source_info              0.003     0.0       1     
total count_ruptures           0.002     0.0       2     
reading site collection        5.245E-05 0.0       1     
aggregate curves               2.694E-05 0.0       2     
saving probability maps        2.456E-05 0.0       1     
============================== ========= ========= ======