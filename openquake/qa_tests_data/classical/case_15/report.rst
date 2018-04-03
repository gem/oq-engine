Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     17,280,623         
date           2018-03-26T15:55:41
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 3, num_levels = 17

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
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
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
source_model_1.xml 0      Active Shallow Crust     495          15          
source_model_1.xml 1      Stable Continental Crust 15           15          
source_model_2.xml 2      Active Shallow Crust     495          240         
source_model_2.xml 3      Active Shallow Crust     495          240         
================== ====== ======================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 1,500
#tot_ruptures 510  
#tot_weight   176  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= =========
source_id source_class num_ruptures calc_time split_time num_sites num_split
========= ============ ============ ========= ========== ========= =========
1         AreaSource   240          0.018     0.004      297       99       
2         PointSource  15           8.204E-04 2.623E-06  3         1        
========= ============ ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.018     1     
PointSource  8.204E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.013 0.014  0.003 0.023 2        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ========================================================================= ========
task           sent                                                                      received
count_ruptures sources=8.87 KB srcfilter=1.62 KB param=1.18 KB monitor=660 B gsims=430 B 749 B   
============== ========================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.026     1.773     2     
reading composite source model 0.023     0.0       1     
managing sources               0.012     0.0       1     
splitting sources              0.009     0.0       1     
store source_info              0.007     0.0       1     
reading site collection        3.660E-04 0.0       1     
unpickling count_ruptures      1.292E-04 0.0       2     
aggregate curves               6.628E-05 0.0       2     
saving probability maps        4.172E-05 0.0       1     
============================== ========= ========= ======