North Africa PSHA
=================

============== ===================
checksum32     576,018,697        
date           2018-05-15T04:13:33
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 2, num_levels = 133

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     19                
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
sites                   `sites.csv <sites.csv>`_                                    
source                  `GridSources.xml <GridSources.xml>`_                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============================= ======= =============== ================
smlt_path                     weight  gsim_logic_tree num_realizations
============================= ======= =============== ================
smoothed_model_m_m0.2_b_e0.0  0.50000 simple(0,4,0)   4/4             
smoothed_model_m_m0.2_b_m0.05 0.50000 simple(0,4,0)   4/4             
============================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================================================== =========== ======================= =================
grp_id gsims                                                                                  distances   siteparams              ruptparams       
====== ====================================================================================== =========== ======================= =================
0      AkkarEtAlRjb2014() AtkinsonBoore2006Modified2011() ChiouYoungs2014() PezeshkEtAl2011() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarEtAlRjb2014() AtkinsonBoore2006Modified2011() ChiouYoungs2014() PezeshkEtAl2011() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ====================================================================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,AkkarEtAlRjb2014(): [1]
  0,AtkinsonBoore2006Modified2011(): [2]
  0,ChiouYoungs2014(): [0]
  0,PezeshkEtAl2011(): [3]
  1,AkkarEtAlRjb2014(): [5]
  1,AtkinsonBoore2006Modified2011(): [6]
  1,ChiouYoungs2014(): [4]
  1,PezeshkEtAl2011(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
=============== ====== =============== ============ ============
source_model    grp_id trt             eff_ruptures tot_ruptures
=============== ====== =============== ============ ============
GridSources.xml 0      Tectonic_type_b 260          260         
GridSources.xml 1      Tectonic_type_b 260          260         
=============== ====== =============== ============ ============

============= ===
#TRT models   2  
#eff_ruptures 520
#tot_ruptures 520
#tot_weight   208
============= ===

Slowest sources
---------------
========= ================ ============ ========= ========== ========= ========= ======
source_id source_class     num_ruptures calc_time split_time num_sites num_split events
========= ================ ============ ========= ========== ========= ========= ======
21        MultiPointSource 260          2.449E-04 2.792E-04  4         4         0     
========= ================ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 2.449E-04 1     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
prefilter          0.00345 2.523E-04 0.00324 0.00381 4        
count_ruptures     0.00194 1.972E-05 0.00192 0.00195 2        
================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=2, weight=104, duration=0 s, sources="21"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   2
weight   52      0.0    52  52  2
======== ======= ====== === === =

Slowest task
------------
taskno=1, weight=104, duration=0 s, sources="21"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   2
weight   52      0.0    52  52  2
======== ======= ====== === === =

Informational data
------------------
============== ========================================================================= ========
task           sent                                                                      received
prefilter      srcs=5.45 KB monitor=1.27 KB srcfilter=916 B                              5.76 KB 
count_ruptures sources=4.13 KB param=3.69 KB srcfilter=1.51 KB gsims=794 B monitor=666 B 720 B   
============== ========================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.02601   0.0       1     
total prefilter                0.01382   3.08984   4     
store source_info              0.00617   0.0       1     
reading composite source model 0.00581   0.0       1     
total count_ruptures           0.00387   0.49609   2     
splitting sources              0.00120   0.0       1     
reading site collection        7.555E-04 0.0       1     
unpickling prefilter           3.843E-04 0.0       4     
unpickling count_ruptures      7.915E-05 0.0       2     
aggregate curves               4.935E-05 0.0       2     
saving probability maps        3.529E-05 0.0       1     
============================== ========= ========= ======