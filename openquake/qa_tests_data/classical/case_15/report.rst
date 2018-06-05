Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     17,280,623         
date           2018-06-05T06:38:45
engine_version 3.2.0-git65c4735   
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
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
SM1            0.50000 complex(2,2)    4/4             
SM2_a3b1       0.25000 complex(2,2)    2/2             
SM2_a3pt2b0pt8 0.25000 complex(2,2)    2/2             
============== ======= =============== ================

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
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   240          0.00617   0.00312    3.00000   99        0     
2         PointSource  15           0.00577   1.669E-06  3.00000   1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00617   1     
PointSource  0.00577   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00361 0.00178 0.00101 0.00686 34       
count_eff_ruptures 0.00927 0.00227 0.00767 0.01087 2        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=2, weight=5, duration=0 s, sources="2"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   3.00000 NaN    3       3       1
weight   5.19615 NaN    5.19615 5.19615 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=1, weight=171, duration=0 s, sources="1"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   3.00000 0.0    3       3       33
weight   5.19615 0.0    5.19615 5.19615 33
======== ======= ====== ======= ======= ==

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
RtreeFilter        srcs=41.84 KB monitor=11.49 KB srcfilter=9.26 KB                        44.81 KB
count_eff_ruptures sources=17.42 KB param=1.2 KB monitor=706 B srcfilter=466 B gsims=430 B 737 B   
================== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.44942   0.0       1     
managing sources               0.25504   0.0       1     
total prefilter                0.12275   3.46875   34    
total count_eff_ruptures       0.01854   5.65234   2     
reading composite source model 0.01636   0.0       1     
unpickling prefilter           0.01181   0.0       34    
store source_info              0.00872   0.0       1     
splitting sources              0.00674   0.0       1     
aggregate curves               7.701E-04 0.0       2     
reading site collection        7.505E-04 0.0       1     
unpickling count_eff_ruptures  6.235E-04 0.0       2     
saving probability maps        2.396E-04 0.0       1     
============================== ========= ========= ======