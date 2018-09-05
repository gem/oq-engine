North Africa PSHA
=================

============== ===================
checksum32     576,018,697        
date           2018-09-05T10:04:41
engine_version 3.2.0-gitb4ef3a4b6c
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
21        MultiPointSource 260          0.00573   2.959E-04  1.00000   4         0     
========= ================ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================ ========= ======
source_class     calc_time counts
================ ========= ======
MultiPointSource 0.00573   1     
================ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.00185 NaN       0.00185 0.00185 1        
count_eff_ruptures   0.00349 3.357E-04 0.00325 0.00372 2        
preprocess           0.00149 8.143E-05 0.00138 0.00156 4        
==================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=104, duration=0 s, sources="21"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   2
weight   52      0.0    52  52  2
======== ======= ====== === === =

Slowest task
------------
taskno=2, weight=104, duration=0 s, sources="21"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   2
weight   52      0.0    52  52  2
======== ======= ====== === === =

Data transfer
-------------
==================== ======================================================================= ========
task                 sent                                                                    received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                    154 B   
count_eff_ruptures   sources=4.24 KB param=3.87 KB gsims=794 B monitor=614 B srcfilter=440 B 720 B   
preprocess           srcs=5.64 KB monitor=1.25 KB srcfilter=1012 B param=144 B               5.83 KB 
==================== ======================================================================= ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
managing sources           0.02541   0.0       1     
total count_eff_ruptures   0.00697   0.0       2     
store source_info          0.00651   0.0       1     
total preprocess           0.00597   0.0       4     
total pickle_source_models 0.00185   0.0       1     
splitting sources          9.680E-04 0.0       1     
aggregate curves           4.566E-04 0.0       2     
========================== ========= ========= ======