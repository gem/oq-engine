Event Based QA Test, Case 12
============================

============== ===================
checksum32     3,009,527,013      
date           2018-06-05T06:40:06
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3500              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

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
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =
#TRT models   2
#eff_ruptures 2
#tot_ruptures 2
#tot_weight   0
============= =

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
2         PointSource  1            0.02724   1.431E-06  1.00000   1         3,370 
1         PointSource  1            0.02532   9.298E-06  1.00000   1         3,536 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.05256   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00327 1.317E-04 0.00317 0.00336 2        
compute_ruptures   0.03391 0.00129   0.03300 0.03483 2        
================== ======= ========= ======= ======= =========

Data transfer
-------------
================ ======================================================================== =========
task             sent                                                                     received 
RtreeFilter      srcs=2.55 KB monitor=692 B srcfilter=558 B                               2.64 KB  
compute_ruptures sources=2.76 KB param=1.16 KB monitor=706 B src_filter=466 B gsims=251 B 179.41 KB
================ ======================================================================== =========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.47776   0.0       1     
managing sources                0.25775   0.0       1     
total compute_ruptures          0.06782   7.19531   2     
saving ruptures                 0.03974   0.0       2     
setting event years             0.01462   0.0       1     
total prefilter                 0.00653   2.53906   2     
store source_info               0.00463   0.0       1     
reading composite source model  0.00417   0.0       1     
making contexts                 0.00163   0.0       2     
unpickling compute_ruptures     0.00107   0.0       2     
reading site collection         8.533E-04 0.0       1     
unpickling prefilter            5.462E-04 0.0       2     
splitting sources               3.033E-04 0.0       1     
=============================== ========= ========= ======