Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     17,280,623         
date           2017-12-06T11:19:56
engine_version 2.9.0-gite55e76e   
============== ===================

num_sites = 3, num_imts = 2

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     0                 
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ====== =============== ================
smlt_path      weight gsim_logic_tree num_realizations
============== ====== =============== ================
SM1            0.500  complex(2,2)    4/4             
SM2_a3b1       0.250  complex(2,2)    2/2             
SM2_a3pt2b0pt8 0.250  complex(2,2)    2/2             
============== ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =========================================== ========= ========== =================
grp_id gsims                                       distances siteparams ruptparams       
====== =========================================== ========= ========== =================
0      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
1      Campbell2003() ToroEtAl2002()               rjb rrup             mag              
2      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
3      BooreAtkinson2008() CampbellBozorgnia2008() rjb rrup  vs30 z2pt5 dip mag rake ztor
====== =========================================== ========= ========== =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,BooreAtkinson2008(): [0 1]
  0,CampbellBozorgnia2008(): [2 3]
  1,Campbell2003(): [0 2]
  1,ToroEtAl2002(): [1 3]
  2,BooreAtkinson2008(): [4]
  2,CampbellBozorgnia2008(): [5]
  3,BooreAtkinson2008(): [6]
  3,CampbellBozorgnia2008(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== ============ ============
source_model       grp_id trt                      eff_ruptures tot_ruptures
================== ====== ======================== ============ ============
source_model_1.xml 0      Active Shallow Crust     255          15          
source_model_1.xml 1      Stable Continental Crust 15           15          
source_model_2.xml 2      Active Shallow Crust     255          240         
source_model_2.xml 3      Active Shallow Crust     240          240         
================== ====== ======================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 765
#tot_ruptures 510
#tot_weight   0  
============= ===

Informational data
------------------
======================= =============================================================================
count_ruptures.received tot 1.81 KB, max_per_task 674 B                                              
count_ruptures.sent     sources 5.42 KB, srcfilter 2.17 KB, param 1.76 KB, monitor 957 B, gsims 539 B
hazard.input_weight     51.0                                                                         
hazard.n_imts           2                                                                            
hazard.n_levels         17                                                                           
hazard.n_realizations   12                                                                           
hazard.n_sites          3                                                                            
hazard.n_sources        4                                                                            
hazard.output_weight    102.0                                                                        
hostname                tstation.gem.lan                                                             
require_epsilons        False                                                                        
======================= =============================================================================

Slowest sources
---------------
========= ============ ============ ========= ========= =========
source_id source_class num_ruptures calc_time num_sites num_split
========= ============ ============ ========= ========= =========
1         AreaSource   240          0.004     3         5        
2         PointSource  15           1.993E-04 3         1        
========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.004     1     
PointSource  1.993E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ========= ===== =========
operation-duration mean  stddev min       max   num_tasks
count_ruptures     0.002 0.001  8.886E-04 0.004 3        
================== ===== ====== ========= ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.010     0.0       1     
total count_ruptures           0.006     0.0       3     
managing sources               0.005     0.0       1     
store source_info              0.004     0.0       1     
reading site collection        4.959E-05 0.0       1     
aggregate curves               4.363E-05 0.0       3     
saving probability maps        2.527E-05 0.0       1     
============================== ========= ========= ======