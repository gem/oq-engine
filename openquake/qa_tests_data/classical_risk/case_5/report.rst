Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     2,783,587,006      
date           2018-06-26T14:56:57
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 50

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              15.0              
ses_per_logic_tree_path         1                 
truncation_level                4.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1024              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 simple(1,4)     4/4             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================== ========== ========== ==============
grp_id gsims                                                                                    distances  siteparams ruptparams    
====== ======================================================================================== ========== ========== ==============
0      AkkarBommer2010()                                                                        rjb        vs30       mag rake      
1      AtkinsonBoore2003SInter() LinLee2008SInter() YoungsEtAl1997SInter() ZhaoEtAl2006SInter() rhypo rrup vs30       hypo_depth mag
====== ======================================================================================== ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,AkkarBommer2010(): [0 1 2 3]
  1,AtkinsonBoore2003SInter(): [1]
  1,LinLee2008SInter(): [3]
  1,YoungsEtAl1997SInter(): [2]
  1,ZhaoEtAl2006SInter(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 23           23          
source_model.xml 1      Subduction Interface 23           23          
================ ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 46
#tot_ruptures 46
#tot_weight   11
============= ==

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
B         PointSource  23           0.00530   1.669E-06  1.00000   1         0     
A         PointSource  23           0.00368   4.053E-06  1.00000   1         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.00898   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00231 5.884E-05 0.00227 0.00235 2        
count_eff_ruptures 0.00603 0.00161   0.00490 0.00717 2        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=2, duration=0 s, sources="A"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   2.30000 NaN    2.30000 2.30000 1
======== ======= ====== ======= ======= =

Slowest task
------------
taskno=2, weight=9, duration=0 s, sources="B"

======== ======= ====== ======= ======= =
variable mean    stddev min     max     n
======== ======= ====== ======= ======= =
nsites   1.00000 NaN    1       1       1
weight   9.20000 NaN    9.20000 9.20000 1
======== ======= ====== ======= ======= =

Data transfer
-------------
================== ====================================================================== ========
task               sent                                                                   received
RtreeFilter        srcs=2.27 KB monitor=644 B srcfilter=558 B                             2.5 KB  
count_eff_ruptures sources=2.59 KB param=1.6 KB monitor=658 B gsims=519 B srcfilter=492 B 716 B   
================== ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.21960   0.0       1     
total count_eff_ruptures       0.01207   6.50391   2     
store source_info              0.00899   0.0       1     
total prefilter                0.00462   2.01953   2     
reading composite source model 0.00273   0.0       1     
aggregate curves               7.279E-04 0.0       2     
unpickling count_eff_ruptures  6.392E-04 0.0       2     
unpickling prefilter           5.658E-04 0.0       2     
reading site collection        3.037E-04 0.0       1     
splitting sources              2.730E-04 0.0       1     
============================== ========= ========= ======